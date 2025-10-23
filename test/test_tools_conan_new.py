from collections.abc import AsyncGenerator
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
async def client_session() -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(mcp, raise_exceptions=True) as _session:
        yield _session


@pytest.mark.anyio
@patch('main.run_command')
async def test_conan_new_basic(mock_run_command, client_session: ClientSession):
    """Test conan_new with basic parameters."""
    mock_run_command.return_value = "Project created successfully"

    result = await client_session.call_tool("conan_new", {
        "template": "cmake_exe",
        "name": "testapp",
        "version": "1.0"
    })

    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)

    response_text = result.content[0].text
    assert isinstance(response_text, str)

    # Verify the command was called correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "new" in call_args
    assert "cmake_exe" in call_args
    assert "-d" in call_args
    assert "name=testapp" in call_args
    assert "version=1.0" in call_args


@pytest.mark.anyio
@patch('main.run_command')
async def test_conan_new_with_dependencies(mock_run_command, client_session: ClientSession):
    """Test conan_new with dependencies."""
    mock_run_command.return_value = "Project created successfully with dependencies"

    result = await client_session.call_tool("conan_new", {
        "template": "cmake_lib",
        "name": "mylib",
        "version": "2.0",
        "requires": ["fmt/12.0.0", "openssl/3.6.0"],
        "output_dir": "/tmp/test",
        "force": True
    })

    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)

    response_text = result.content[0].text
    assert isinstance(response_text, str)

    # Verify the command was called correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "new" in call_args
    assert "cmake_lib" in call_args
    assert "-d" in call_args
    assert "name=mylib" in call_args
    assert "version=2.0" in call_args
    # Check that each dependency is added as a separate -d requires= parameter
    assert "requires=fmt/12.0.0" in call_args
    assert "requires=openssl/3.6.0" in call_args
    assert "-o" in call_args
    assert "/tmp/test" in call_args
    assert "-f" in call_args


@pytest.mark.anyio
@patch('main.run_command')
async def test_conan_new_error_handling(mock_run_command, client_session: ClientSession):
    """Test conan_new error handling."""
    mock_run_command.side_effect = RuntimeError("Conan command failed")

    # The MCP framework will catch the exception and return an error response
    result = await client_session.call_tool("conan_new", {
        "template": "cmake_exe",
        "name": "testapp"
    })

    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)

    response_text = result.content[0].text
    assert isinstance(response_text, str)
    # The response should contain error information
    assert "error" in response_text.lower() or "failed" in response_text.lower()


@pytest.mark.anyio
@patch('main.run_command')
async def test_conan_new_empty_dependencies(mock_run_command, client_session: ClientSession):
    """Test conan_new with empty dependencies list."""
    mock_run_command.return_value = "Project created successfully"

    result = await client_session.call_tool("conan_new", {
        "template": "header_lib",
        "name": "mylib",
        "requires": []
    })

    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)

    response_text = result.content[0].text
    assert isinstance(response_text, str)
    # Should not contain dependency note
    assert "IMPORTANT" not in response_text
    assert "placeholder examples" not in response_text

    # Verify the command was called correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "new" in call_args
    assert "header_lib" in call_args
    assert "name=mylib" in call_args
    # Should not have any requires parameters
    assert not any("requires=" in arg for arg in call_args)


@pytest.mark.anyio
@patch('main.run_command')
async def test_conan_new_dependency_note_in_output(mock_run_command, client_session: ClientSession):
    """Test that dependency note appears in output when dependencies are specified."""
    mock_run_command.return_value = "Files created:\n  conanfile.py\n  CMakeLists.txt"

    result = await client_session.call_tool("conan_new", {
        "template": "cmake_exe",
        "name": "testapp",
        "requires": ["fmt/12.0.0", "boost/1.82.0"]
    })

    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)

    response_text = result.content[0].text
    assert isinstance(response_text, str)
    
    # Should contain the dependency note
    assert "IMPORTANT" in response_text
    assert "placeholder examples" in response_text
    assert "fmt/12.0.0" in response_text
    assert "boost/1.82.0" in response_text
    assert "Files created:" in response_text
