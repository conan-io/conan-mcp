from unittest.mock import patch

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult, TextContent

from main import mcp


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client_session() -> ClientSession:
    async with create_connected_server_and_client_session(
        mcp, raise_exceptions=True
    ) as _session:
        yield _session


@pytest.mark.anyio
@patch("main.run_command")
async def test_install_conan_packages_basic(
    mock_run_command, client_session: ClientSession
):
    """Test basic install functionality - command composition."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "install_conan_packages", {"path": "/path/to/conanfile.txt"}
    )

    # Verify the command was composed correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "install", "/path/to/conanfile.txt", "--format=json"]
    assert call_args == expected_cmd

    # Verify timeout is default (90.0)
    call_kwargs = mock_run_command.call_args[1]
    assert call_kwargs.get("timeout") == 90.0


@pytest.mark.anyio
@patch("main.run_command")
async def test_install_conan_packages_with_remote(
    mock_run_command, client_session: ClientSession
):
    """Test install with specific remote - command composition."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "install_conan_packages",
        {"path": "/path/to/project/conanfile.py", "remote": "conancenter"},
    )

    # Verify the command was composed correctly with remote
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "install",
        "/path/to/project/conanfile.py",
        "--remote",
        "conancenter",
        "--format=json",
    ]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("main.run_command")
async def test_install_conan_packages_with_settings_and_options(
    mock_run_command, client_session: ClientSession
):
    """Test install with settings_host and options_host parameters - command composition."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "install_conan_packages",
        {
            "path": "/home/user/project/conanfile.py",
            "settings_host": [
                "os=Linux",
                "arch=armv8",
                "compiler=gcc",
                "compiler.version=11",
            ],
            "options_host": ["fPIC=True", "shared=False"],
            "build_missing": True,
        },
    )

    # Verify the command was composed correctly with all parameters
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "install",
        "/home/user/project/conanfile.py",
        "-s:h",
        "os=Linux",
        "-s:h",
        "arch=armv8",
        "-s:h",
        "compiler=gcc",
        "-s:h",
        "compiler.version=11",
        "-o:h",
        "fPIC=True",
        "-o:h",
        "shared=False",
        "--build=missing",
        "--format=json",
    ]
    assert call_args == expected_cmd

    # Verify timeout was set to 300.0 for build_missing=True
    call_kwargs = mock_run_command.call_args[1]
    assert call_kwargs.get("timeout") == 300.0


@pytest.mark.anyio
@patch("main.run_command")
async def test_install_conan_packages_with_profile(
    mock_run_command, client_session: ClientSession
):
    """Test install with specific remote - command composition."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "install_conan_packages",
        {
            "path": "/path/to/project/conanfile.py",
            "build_profile": "linux-debug",
            "host_profile": "Windows-msvc193-x86_64-Release",
        },
    )

    # Verify the command was composed correctly with remote
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "install",
        "/path/to/project/conanfile.py",
        "-pr:b",
        "linux-debug",
        "-pr:h",
        "Windows-msvc193-x86_64-Release",
        "--format=json",
    ]
    assert call_args == expected_cmd
