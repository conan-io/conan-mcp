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


@pytest.fixture
def mock_conan_output():
    """Common mock output for conan new command."""
    return """File saved: CMakeLists.txt
File saved: conanfile.py
File saved: include/hello.h
File saved: src/hello.cpp
File saved: test_package/CMakeLists.txt
File saved: test_package/conanfile.py
File saved: test_package/src/example.cpp"""


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_conan_new_with_dependencies(
    mock_run_command, client_session: ClientSession, mock_conan_output
):
    """Test conan_new with dependencies and tool_requires - verify all arguments are included."""
    mock_run_command.return_value = mock_conan_output

    result = await client_session.call_tool(
        "create_conan_project",
        {
            "template": "cmake_lib",
            "name": "mylib",
            "version": "2.0",
            "requires": ["fmt/12.0.0", "openssl/3.6.0"],
            "tool_requires": ["cmake/3.28.0", "ninja/1.11.1"],
            "output_dir": "/tmp/test",
            "force": True,
        },
    )

    assert isinstance(result, CallToolResult)
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]

    # Verify all expected arguments are present
    assert "conan" in call_args and "new" in call_args and "cmake_lib" in call_args
    assert "--define" in call_args
    assert "name=mylib" in call_args
    assert "version=2.0" in call_args
    assert "requires=fmt/12.0.0" in call_args
    assert "requires=openssl/3.6.0" in call_args
    assert "tool_requires=cmake/3.28.0" in call_args
    assert "tool_requires=ninja/1.11.1" in call_args
    assert "--output" in call_args
    assert "/tmp/test" in call_args
    assert "--force" in call_args

    # Verify output is included in result and warning includes only requires (not tool_requires)
    response_text = result.content[0].text
    assert "File saved: CMakeLists.txt" in response_text
    assert "WARNING" in response_text
    assert "fmt/12.0.0" in response_text
    assert "openssl/3.6.0" in response_text
    # tool_requires should NOT appear in the warning
    assert "cmake/3.28.0" not in response_text
    assert "ninja/1.11.1" not in response_text


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_conan_new_empty_dependencies(
    mock_run_command, client_session: ClientSession, mock_conan_output
):
    """Test conan_new with minimal parameters - verify no unnecessary arguments."""
    mock_run_command.return_value = mock_conan_output

    result = await client_session.call_tool(
        "create_conan_project",
        {"template": "header_lib", "name": "mylib", "requires": []},
    )

    assert isinstance(result, CallToolResult)
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]

    # Verify only essential arguments are present
    assert "conan" in call_args and "new" in call_args and "header_lib" in call_args
    assert "--define" in call_args
    assert "name=mylib" in call_args
    assert "version=0.1" in call_args  # Default version is 0.1, not 1.0

    # Verify unnecessary arguments are NOT present
    assert not any("requires=" in arg for arg in call_args)  # No requires
    assert "--output" not in call_args  # No custom output dir
    assert "--force" not in call_args  # No force flag

    # Verify output is included in result
    response_text = result.content[0].text
    assert "File saved: CMakeLists.txt" in response_text
    assert "WARNING" not in response_text  # No warning for empty dependencies


@pytest.mark.anyio
@patch("conan_mcp.main.run_command")
async def test_create_project_uses_custom_conan_binary(
    mock_run_command, client_session: ClientSession, mock_conan_output
):
    """Test that create_conan_project uses CONAN_MCP_CONAN_PATH if set."""
    mock_run_command.return_value = mock_conan_output
    custom_path = "/custom/path/conan"

    with patch.dict(os.environ, {"CONAN_MCP_CONAN_PATH": custom_path}, clear=False):
        await client_session.call_tool(
            "create_conan_project", {"template": "cmake_lib", "name": "test"}
        )
        call_args = mock_run_command.call_args[0][0]
        assert call_args[0] == custom_path
