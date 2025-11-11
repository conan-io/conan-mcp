import os
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult, TextContent

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
async def test_get_conan_profile_default(
    mock_run_command, client_session: ClientSession
):
    """Test get_conan_profile with default profile."""
    # Minimal conan profile response
    mock_profile = {"host": {"settings": {}}, "build": {"settings": {}}}
    mock_run_command.return_value = str(mock_profile).replace("'", '"')

    # Test calling the tool without profile parameter
    result = await client_session.call_tool("get_conan_profile", {})

    # Check that we get a valid response structure
    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].type == "text"

    # Basic sanity check: got some text back
    response_text = result.content[0].text
    assert isinstance(response_text, str)

    # Verify the command was called correctly (no --profile flag)
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "profile" in call_args
    assert "show" in call_args
    assert "--format=json" in call_args
    assert "--profile" not in call_args


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_get_conan_profile_specific(
    mock_run_command, client_session: ClientSession
):
    """Test get_conan_profile with specific profile."""
    # Minimal conan profile response
    mock_profile = {"host": {"settings": {}}, "build": {"settings": {}}}
    mock_run_command.return_value = str(mock_profile).replace("'", '"')

    # Test calling the tool with specific profile
    result = await client_session.call_tool(
        "get_conan_profile", {"profile": "linux-debug"}
    )

    # Check that we get a valid response structure
    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].type == "text"

    # Basic sanity check: got some text back
    response_text = result.content[0].text
    assert isinstance(response_text, str)

    # Verify the command was called correctly (with --profile flag)
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "profile" in call_args
    assert "show" in call_args
    assert "--format=json" in call_args
    assert "--profile=linux-debug" in call_args


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_list_conan_profiles(mock_run_command, client_session: ClientSession):
    """Test listing conan profiles successfully."""
    mock_response = {"local": ["default", "linux-debug", "macos-release"]}
    mock_run_command.return_value = str(mock_response).replace("'", '"')

    result = await client_session.call_tool("list_conan_profiles", {})

    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)

    response_text = result.content[0].text
    assert isinstance(response_text, str)

    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "profile" in call_args
    assert "list" in call_args
    assert "--format=json" in call_args


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_profile_tools_use_custom_conan_binary(
    mock_run_command, client_session: ClientSession
):
    """Test that profile tools use CONAN_MCP_CONAN_PATH if set."""
    mock_run_command.return_value = '{"local": ["default"]}'
    custom_path = "/custom/path/conan"

    with patch.dict(os.environ, {"CONAN_MCP_CONAN_PATH": custom_path}, clear=False):
        await client_session.call_tool("get_conan_profile", {})
        call_args = mock_run_command.call_args[0][0]
        assert call_args[0] == custom_path
