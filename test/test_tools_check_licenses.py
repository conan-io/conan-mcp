import json
import os
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from conan_mcp.main import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client_session() -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(
        mcp, raise_exceptions=True
    ) as _session:
        yield _session


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_basic_command_composition(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test basic get_conan_licenses functionality - verify command composition."""
    # Mock graph info output with host context nodes
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "fmt/10.0.0",
                            "direct": True,
                        },
                        "2": {
                            "ref": "zlib/1.2.13",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "fmt/10.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "2": {
                    "ref": "zlib/1.2.13",
                    "recipe": "Cache",
                    "context": "host",
                    "license": "Zlib",
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    await client_session.call_tool(
        "get_conan_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # Verify the command was composed correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "graph", "info", "--format=json", os.path.normpath("/path/to/conanfile.txt")]
    assert call_args == expected_cmd

    # Verify timeout is set correctly (90.0 for graph info)
    call_kwargs = mock_run_command.call_args[1]
    assert call_kwargs.get("timeout") == 90.0


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_with_profiles_and_remote(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test get_conan_licenses with profiles and remote - command composition."""
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "boost/1.84.0",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "boost/1.84.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "BSL-1.0",
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    await client_session.call_tool(
        "get_conan_licenses",
        {
            "path": "conanfile.py",
            "work_dir": "/home/user/project",
            "remote": "conancenter",
            "build_profile": "linux-debug",
            "host_profile": "linux-release",
        },
    )

    # Verify the command was composed correctly with all parameters
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "graph",
        "info",
        "--format=json",
        os.path.normpath("/home/user/project/conanfile.py"),
        "--remote=conancenter",
        "-pr:b=linux-debug",
        "-pr:h=linux-release",
    ]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_filters_host_context_only(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test that get_conan_licenses only processes host context nodes, ignoring build context."""
    # Mock graph output with both host and build context nodes
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "fmt/10.0.0",
                            "direct": True,
                        },
                        "2": {
                            "ref": "zlib/1.2.13",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "fmt/10.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "2": {
                    "ref": "cmake/3.28.0",
                    "recipe": "Cache",
                    "context": "build",
                    "license": "BSD-3-Clause",
                    "dependencies": {},
                },
                "3": {
                    "ref": "zlib/1.2.13",
                    "recipe": "Cache",
                    "context": "host",
                    "license": "Zlib",
                    "dependencies": {},
                },
                "4": {
                    "ref": "ninja/1.13.0",
                    "recipe": "Cache",
                    "context": "build",
                    "license": "Apache-2.0",
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    result = await client_session.call_tool(
        "get_conan_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # Verify only host context packages are included
    # FastMCP may serialize list items separately, so we need to collect all content items
    assert result is not None
    result_data = []
    for content_item in result.content:
        item_data = json.loads(content_item.text)
        if isinstance(item_data, list):
            result_data.extend(item_data)
        else:
            result_data.append(item_data)
    
    # Should only have 2 packages (fmt and zlib), not cmake or ninja
    assert len(result_data) == 2
    
    # Convert to dict for easier lookup
    result_dict = {item["ref"]: item["licenses"] for item in result_data}
    
    assert "fmt/10.0.0" in result_dict
    assert result_dict["fmt/10.0.0"] == ["MIT"]
    assert "zlib/1.2.13" in result_dict
    assert result_dict["zlib/1.2.13"] == ["Zlib"]
    assert "cmake/3.28.0" not in result_dict
    assert "ninja/1.13.0" not in result_dict


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_collects_licenses_correctly(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test that get_conan_licenses correctly collects all licenses from packages."""
    # Mock graph output with different license types
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "fmt/10.0.0",
                            "direct": True,
                        },
                        "2": {
                            "ref": "openssl/3.2.0",
                            "direct": True,
                        },
                        "3": {
                            "ref": "gpl-library/1.0.0",
                            "direct": True,
                        },
                        "4": {
                            "ref": "agpl-library/2.0.0",
                            "direct": True,
                        },
                        "5": {
                            "ref": "unknown-library/1.0.0",
                            "direct": True,
                        },
                        "6": {
                            "ref": "no-license-library/1.0.0",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "fmt/10.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "2": {
                    "ref": "openssl/3.2.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "Apache-2.0",
                    "dependencies": {},
                },
                "3": {
                    "ref": "gpl-library/1.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "GPL-3.0",
                    "dependencies": {},
                },
                "4": {
                    "ref": "agpl-library/2.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "AGPL-3.0",
                    "dependencies": {},
                },
                "5": {
                    "ref": "unknown-library/1.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "Custom-License",
                    "dependencies": {},
                },
                "6": {
                    "ref": "no-license-library/1.0.0",
                    "recipe": "Cache",
                    "context": "host",
                    "license": None,
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    result = await client_session.call_tool(
        "get_conan_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # FastMCP may serialize list items separately, so we need to collect all content items
    result_data = []
    for content_item in result.content:
        item_data = json.loads(content_item.text)
        if isinstance(item_data, list):
            result_data.extend(item_data)
        else:
            result_data.append(item_data)

    # Verify we have all 6 packages
    assert len(result_data) == 6

    # Convert to dict for easier lookup
    result_dict = {item["ref"]: item["licenses"] for item in result_data}

    # Verify all licenses are collected correctly
    assert result_dict["fmt/10.0.0"] == ["MIT"]
    assert result_dict["openssl/3.2.0"] == ["Apache-2.0"]
    assert result_dict["gpl-library/1.0.0"] == ["GPL-3.0"]
    assert result_dict["agpl-library/2.0.0"] == ["AGPL-3.0"]
    assert result_dict["unknown-library/1.0.0"] == ["Custom-License"]
    assert result_dict["no-license-library/1.0.0"] == []


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_handles_multiple_licenses(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test that get_conan_licenses correctly handles packages with multiple licenses (list format)."""
    # Mock graph output with a package that has multiple licenses
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "multi-license-pkg/1.0.0",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "multi-license-pkg/1.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": ["MIT", "Apache-2.0"],
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    result = await client_session.call_tool(
        "get_conan_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # FastMCP may serialize list items separately, so we need to collect all content items
    result_data = []
    for content_item in result.content:
        item_data = json.loads(content_item.text)
        if isinstance(item_data, list):
            result_data.extend(item_data)
        else:
            result_data.append(item_data)

    # Verify the multiple licenses are in a list (not joined with " OR ")
    assert len(result_data) == 1
    assert result_data[0]["ref"] == "multi-license-pkg/1.0.0"
    assert result_data[0]["licenses"] == ["MIT", "Apache-2.0"]


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_with_requires_single_reference(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test that get_conan_licenses works with requires parameter (single reference)."""
    # Mock graph output with a single package reference
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "zlib/1.2.11",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "zlib/1.2.11",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "Zlib",
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    result = await client_session.call_tool(
        "get_conan_licenses",
        {"requires": ["zlib/1.2.11"], "work_dir": "/tmp"}
    )

    # Verify the command was composed correctly with --requires
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "graph", "info", "--format=json", "--requires=zlib/1.2.11"]
    assert call_args == expected_cmd

    # Verify the result
    # FastMCP may serialize list items separately, so we need to collect all content items
    result_data = []
    for content_item in result.content:
        item_data = json.loads(content_item.text)
        if isinstance(item_data, list):
            result_data.extend(item_data)
        else:
            result_data.append(item_data)
    assert isinstance(result_data, list)
    assert len(result_data) == 1
    assert result_data[0]["ref"] == "zlib/1.2.11"
    assert result_data[0]["licenses"] == ["Zlib"]


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_with_requires_multiple_references(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test that get_conan_licenses works with requires parameter (multiple references)."""
    # Mock graph output with multiple package references
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "zlib/1.2.11",
                            "direct": True,
                        },
                        "2": {
                            "ref": "fmt/10.0.0",
                            "direct": True,
                        },
                        "3": {
                            "ref": "openssl/3.2.0",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "zlib/1.2.11",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "Zlib",
                    "dependencies": {},
                },
                "2": {
                    "ref": "fmt/10.0.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "3": {
                    "ref": "openssl/3.2.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "Apache-2.0",
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    result = await client_session.call_tool(
        "get_conan_licenses",
        {
            "requires": ["zlib/1.2.11", "fmt/10.0.0", "openssl/3.2.0"],
            "work_dir": "/tmp"
        }
    )

    # Verify the command was composed correctly with multiple --requires flags
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "graph",
        "info",
        "--format=json",
        "--requires=zlib/1.2.11",
        "--requires=fmt/10.0.0",
        "--requires=openssl/3.2.0",
    ]
    assert call_args == expected_cmd

    # Verify the result
    # FastMCP may serialize list items separately, so we need to collect all content items
    result_data = []
    for content_item in result.content:
        item_data = json.loads(content_item.text)
        if isinstance(item_data, list):
            result_data.extend(item_data)
        else:
            result_data.append(item_data)
    assert isinstance(result_data, list)
    assert len(result_data) == 3

    # Convert to dict for easier lookup
    result_dict = {item["ref"]: item["licenses"] for item in result_data}

    assert "zlib/1.2.11" in result_dict
    assert result_dict["zlib/1.2.11"] == ["Zlib"]
    assert "fmt/10.0.0" in result_dict
    assert result_dict["fmt/10.0.0"] == ["MIT"]
    assert "openssl/3.2.0" in result_dict
    assert result_dict["openssl/3.2.0"] == ["Apache-2.0"]


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.is_dir")
async def test_check_licenses_with_requires_and_profiles(
    mock_is_dir, mock_run_command, client_session: ClientSession
):
    """Test that get_conan_licenses works with requires and profiles."""
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
                    "recipe": "Consumer",
                    "context": "host",
                    "license": None,
                    "dependencies": {
                        "1": {
                            "ref": "boost/1.84.0",
                            "direct": True,
                        },
                    },
                },
                "1": {
                    "ref": "boost/1.84.0",
                    "recipe": "Downloaded",
                    "context": "host",
                    "license": "BSL-1.0",
                    "dependencies": {},
                },
            },
            "root": {
                "0": "None"
            },
            "overrides": {},
            "resolved_ranges": {},
            "replaced_requires": {},
        }
    }
    mock_run_command.return_value = json.dumps(mock_graph_output)
    mock_is_dir.return_value = True

    result = await client_session.call_tool(
        "get_conan_licenses",
        {
            "requires": ["boost/1.84.0"],
            "work_dir": "/tmp",
            "remote": "conancenter",
            "build_profile": "linux-debug",
            "host_profile": "linux-release",
        },
    )

    # Verify the command was composed correctly with all parameters
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "graph",
        "info",
        "--format=json",
        "--requires=boost/1.84.0",
        "--remote=conancenter",
        "-pr:b=linux-debug",
        "-pr:h=linux-release",
    ]
    assert call_args == expected_cmd

