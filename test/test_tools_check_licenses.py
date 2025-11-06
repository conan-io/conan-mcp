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
@patch("pathlib.Path.mkdir")
async def test_check_licenses_basic_command_composition(
    mock_mkdir, mock_run_command, client_session: ClientSession
):
    """Test basic check_conan_dependencies_licenses functionality - verify command composition."""
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

    await client_session.call_tool(
        "check_conan_dependencies_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # Verify the command was composed correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "graph", "info", os.path.normpath("/path/to/conanfile.txt"), "--format=json"]
    assert call_args == expected_cmd

    # Verify timeout is set correctly (90.0 for graph info)
    call_kwargs = mock_run_command.call_args[1]
    assert call_kwargs.get("timeout") == 90.0


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.mkdir")
async def test_check_licenses_with_profiles_and_remote(
    mock_mkdir, mock_run_command, client_session: ClientSession
):
    """Test check_conan_dependencies_licenses with profiles and remote - command composition."""
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

    await client_session.call_tool(
        "check_conan_dependencies_licenses",
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
        os.path.normpath("/home/user/project/conanfile.py"),
        "--format=json",
        "--remote",
        "conancenter",
        "-pr:b",
        "linux-debug",
        "-pr:h",
        "linux-release",
    ]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.mkdir")
async def test_check_licenses_filters_host_context_only(
    mock_mkdir, mock_run_command, client_session: ClientSession
):
    """Test that check_conan_dependencies_licenses only processes host context nodes, ignoring build context."""
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

    result = await client_session.call_tool(
        "check_conan_dependencies_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # Verify only host context packages are included
    # FastMCP returns the result as a dict directly
    assert result is not None
    result_data = json.loads(result.content[0].text)
    
    # Should only have 2 packages (fmt and zlib), not cmake or ninja
    assert len(result_data) == 2
    assert "fmt/10.0.0" in result_data
    assert result_data["fmt/10.0.0"] == "MIT"
    assert "zlib/1.2.13" in result_data
    assert result_data["zlib/1.2.13"] == "Zlib"
    assert "cmake/3.28.0" not in result_data
    assert "ninja/1.13.0" not in result_data


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.mkdir")
async def test_check_licenses_collects_licenses_correctly(
    mock_mkdir, mock_run_command, client_session: ClientSession
):
    """Test that check_conan_dependencies_licenses correctly collects all licenses from packages."""
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

    result = await client_session.call_tool(
        "check_conan_dependencies_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # FastMCP returns the result as a dict directly
    result_data = json.loads(result.content[0].text)

    # Verify we have all 6 packages
    assert len(result_data) == 6

    # Verify all licenses are collected correctly
    assert result_data["fmt/10.0.0"] == "MIT"
    assert result_data["openssl/3.2.0"] == "Apache-2.0"
    assert result_data["gpl-library/1.0.0"] == "GPL-3.0"
    assert result_data["agpl-library/2.0.0"] == "AGPL-3.0"
    assert result_data["unknown-library/1.0.0"] == "Custom-License"
    assert result_data["no-license-library/1.0.0"] is None


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.mkdir")
async def test_check_licenses_handles_multiple_licenses(
    mock_mkdir, mock_run_command, client_session: ClientSession
):
    """Test that check_conan_dependencies_licenses correctly handles packages with multiple licenses (list format)."""
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

    result = await client_session.call_tool(
        "check_conan_dependencies_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # FastMCP returns the result as a dict directly
    result_data = json.loads(result.content[0].text)

    # Verify the multiple licenses are joined with " OR "
    assert len(result_data) == 1
    assert "multi-license-pkg/1.0.0" in result_data
    assert result_data["multi-license-pkg/1.0.0"] == "MIT OR Apache-2.0"

