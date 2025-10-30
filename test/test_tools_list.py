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
async def test_list_conan_basic(mock_run_command, client_session: ClientSession):
    """Only name and version"""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "list_conan_packages", {"name": "foo", "version": "1.2.11"}
    )

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "list", "foo/1.2.11", "--format=json", "--remote", "*"]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_list_conan_user_chanel(mock_run_command, client_session: ClientSession):
    """Define name, version, user and channel"""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "list_conan_packages",
        {"name": "foo", "version": "1.2.11", "user": "*", "channel": "*"},
    )

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "list", "foo/1.2.11@*/*", "--format=json", "--remote", "*"]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_list_conan_rrev_pid_prev(
    mock_run_command, client_session: ClientSession
):
    """Define name, version, rrev, pid and prev."""
    mock_run_command.return_value = '{"result": "success"}'

    rrev = "abc123"
    pid = "qwerty"

    await client_session.call_tool(
        "list_conan_packages",
        {
            "name": "foo",
            "version": "1.2.11",
            "recipe_revision": rrev,
            "package_id": pid,
        },
    )

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "list",
        f"foo/1.2.11#{rrev}:{pid}",
        "--format=json",
        "--remote",
        "*",
    ]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_list_conan_filter_options(
    mock_run_command, client_session: ClientSession
):
    """Use filter options: fPIC and shared."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "list_conan_packages",
        {
            "name": "zlib",
            "filter_options": ["*:fPIC=True", "*:shared=False"],
            "include_all_package_revisions": True,
        },
    )

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "list",
        "zlib/*:*#*",
        "--format=json",
        "--remote",
        "*",
        "-fo",
        "*:fPIC=True",
        "-fo",
        "*:shared=False",
    ]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_list_conan_filter_settings(
    mock_run_command, client_session: ClientSession
):
    """Use filter settings: arch and os."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "list_conan_packages",
        {"name": "zlib", "filter_settings": ["arch=armv8", "os=Windows"]},
    )

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "list",
        "zlib/*:*",
        "--format=json",
        "--remote",
        "*",
        "-fs",
        "arch=armv8",
        "-fs",
        "os=Windows",
    ]
    assert call_args == expected_cmd


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_list_conan_change_remote(
    mock_run_command, client_session: ClientSession
):
    """Use filter options: fPIC and shared."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "list_conan_packages", {"name": "zlib", "remote": "conancenter"}
    )

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = [
        "conan",
        "list",
        "zlib/*",
        "--format=json",
        "--remote",
        "conancenter",
    ]
    assert call_args == expected_cmd
