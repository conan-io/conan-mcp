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
@patch("main.run_command")
async def test_conan_new_with_dependencies(
    mock_run_command, client_session: ClientSession, mock_conan_output
):
    """Test conan_new with dependencies."""
    mock_run_command.return_value = mock_conan_output

    result = await client_session.call_tool(
        "conan_new",
        {
            "template": "cmake_lib",
            "name": "mylib",
            "requires": ["fmt/12.0.0", "openssl/3.6.0"],
        },
    )

    assert isinstance(result, CallToolResult)
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args and "new" in call_args and "cmake_lib" in call_args
    assert "requires=fmt/12.0.0" in call_args and "requires=openssl/3.6.0" in call_args

    # Verify output is included in result
    response_text = result.content[0].text
    assert "File saved: CMakeLists.txt" in response_text
    assert "WARNING" in response_text and "fmt/12.0.0" in response_text


@pytest.mark.anyio
@patch("main.run_command")
async def test_conan_new_empty_dependencies(
    mock_run_command, client_session: ClientSession, mock_conan_output
):
    """Test conan_new with empty dependencies list."""
    mock_run_command.return_value = mock_conan_output

    result = await client_session.call_tool(
        "conan_new", {"template": "header_lib", "name": "mylib", "requires": []}
    )

    assert isinstance(result, CallToolResult)
    mock_run_command.assert_called_once()

    # Verify output is included in result
    response_text = result.content[0].text
    assert "File saved: CMakeLists.txt" in response_text
    assert "WARNING" not in response_text  # No warning for empty dependencies
