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
    """Test basic check_licenses functionality - verify command composition."""
    # Mock graph info output with host context nodes
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
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
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "2": {
                    "ref": "zlib/1.2.13",
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
        "check_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
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
    """Test check_licenses with profiles and remote - command composition."""
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
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
        "check_licenses",
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
    """Test that check_licenses only processes host context nodes, ignoring build context."""
    # Mock graph output with both host and build context nodes
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
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
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "2": {
                    "ref": "cmake/3.28.0",
                    "context": "build",
                    "license": "BSD-3-Clause",
                    "dependencies": {},
                },
                "3": {
                    "ref": "zlib/1.2.13",
                    "context": "host",
                    "license": "Zlib",
                    "dependencies": {},
                },
                "4": {
                    "ref": "ninja/1.13.0",
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
        "check_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # Verify only host context packages are included
    # FastMCP returns the result as a dict directly
    assert result is not None
    result_data = json.loads(result.content[0].text)
    
    # Should only have 2 packages (fmt and zlib), not cmake or ninja
    assert result_data["total_packages"] == 2
    assert "fmt/10.0.0" in result_data["compliant_packages"]
    assert "zlib/1.2.13" in result_data["compliant_packages"]
    assert "cmake/3.28.0" not in result_data["compliant_packages"]
    assert "ninja/1.13.0" not in result_data["compliant_packages"]


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
@patch("pathlib.Path.mkdir")
async def test_check_licenses_classifies_licenses_correctly(
    mock_mkdir, mock_run_command, client_session: ClientSession
):
    """Test that check_licenses correctly classifies commercial-safe, unsafe, and unknown licenses."""
    # Mock graph output with different license types
    mock_graph_output = {
        "graph": {
            "nodes": {
                "0": {
                    "ref": "conanfile",
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
                    "context": "host",
                    "license": "MIT",
                    "dependencies": {},
                },
                "2": {
                    "ref": "openssl/3.2.0",
                    "context": "host",
                    "license": "Apache-2.0",
                    "dependencies": {},
                },
                "3": {
                    "ref": "gpl-library/1.0.0",
                    "context": "host",
                    "license": "GPL-3.0",
                    "dependencies": {},
                },
                "4": {
                    "ref": "agpl-library/2.0.0",
                    "context": "host",
                    "license": "AGPL-3.0",
                    "dependencies": {},
                },
                "5": {
                    "ref": "unknown-library/1.0.0",
                    "context": "host",
                    "license": "Custom-License",
                    "dependencies": {},
                },
                "6": {
                    "ref": "no-license-library/1.0.0",
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
        "check_licenses", {"path": "conanfile.txt", "work_dir": "/path/to"}
    )

    # FastMCP returns the result as a dict directly
    result_data = json.loads(result.content[0].text)

    # Verify totals
    assert result_data["total_packages"] == 6

    # Verify compliant packages (MIT, Apache-2.0)
    assert len(result_data["compliant_packages"]) == 2
    assert "fmt/10.0.0" in result_data["compliant_packages"]
    assert "openssl/3.2.0" in result_data["compliant_packages"]

    # Verify non-compliant packages (GPL, AGPL)
    assert len(result_data["non_compliant_packages"]) == 2
    assert "gpl-library/1.0.0" in result_data["non_compliant_packages"]
    assert "agpl-library/2.0.0" in result_data["non_compliant_packages"]

    # Verify unknown licenses (Custom-License, None)
    assert len(result_data["unknown_licenses"]) == 2
    assert "unknown-library/1.0.0" in result_data["unknown_licenses"]
    assert "no-license-library/1.0.0" in result_data["unknown_licenses"]

    # Verify all_compliant is False
    assert result_data["all_compliant"] is False

    # Verify details structure
    assert len(result_data["details"]) == 6
    for detail in result_data["details"]:
        assert "package" in detail
        assert "license" in detail
        assert "compliant" in detail
        assert "reason" in detail

    # Verify specific details
    fmt_detail = next(d for d in result_data["details"] if d["package"] == "fmt/10.0.0")
    assert fmt_detail["compliant"] is True
    assert "MIT" in fmt_detail["license"]
    assert "permissive" in fmt_detail["reason"].lower()

    gpl_detail = next(
        d for d in result_data["details"] if d["package"] == "gpl-library/1.0.0"
    )
    assert gpl_detail["compliant"] is False
    assert "GPL-3.0" in gpl_detail["license"]
    assert "copyleft" in gpl_detail["reason"].lower()

