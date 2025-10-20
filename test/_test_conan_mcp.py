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
async def test_search_conan_packages_basic(mock_run_command, client_session: ClientSession):
    """Test basic search functionality."""
    # Mock realistic conan search response
    mock_response = {
        "conancenter": {
            "boost/1.82.0": {},
            "boost/1.83.0": {},
            "boost/1.84.0": {}
        }
    }
    mock_run_command.return_value = str(mock_response).replace("'", '"')
    
    result = await client_session.call_tool("search_conan_packages", {"query": "boost"})
    
    # Check that we get a valid response structure
    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].type == "text"
    
    # Check the response contains our mocked data
    response_text = result.content[0].text
    assert "boost" in response_text
    assert "1.82.0" in response_text
    assert "conancenter" in response_text
    
    # Verify the command was called correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "conan" in call_args
    assert "search" in call_args
    assert "boost" in call_args


@pytest.mark.anyio
@patch('main.run_command')
async def test_search_conan_packages_with_remote(mock_run_command, client_session: ClientSession):
    """Test search with specific remote."""
    # Mock realistic conan search response for specific remote
    mock_response = {
        "conancenter": {
            "fmt/10.1.0": {},
            "fmt/10.2.0": {},
            "fmt/11.0.0": {},
            "fmt/12.0.0": {}
        }
    }
    mock_run_command.return_value = str(mock_response).replace("'", '"')
    
    result = await client_session.call_tool(
        "search_conan_packages", 
        {"query": "fmt", "remote": "conancenter"}
    )
    
    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)
    
    # Check the response contains our mocked data
    response_text = result.content[0].text
    assert "fmt" in response_text
    assert "10.1.0" in response_text
    assert "conancenter" in response_text
    
    # Verify the command was called with remote
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "--remote" in call_args
    assert "conancenter" in call_args


@pytest.mark.anyio
@patch('main.run_command')
async def test_search_conan_packages_wildcard(mock_run_command, client_session: ClientSession):
    """Test search with wildcard pattern."""
    # Mock realistic conan search response with multiple remotes
    mock_response = {
        "conancenter": {
            "openssl/3.1.0": {},
            "openssl/3.1.1": {},
            "openssl/3.1.2": {}
        },
        "develop": {
            "error": "Recipe 'openssl' not found"
        }
    }
    mock_run_command.return_value = str(mock_response).replace("'", '"')
    
    result = await client_session.call_tool("search_conan_packages", {"query": "*ssl*"})
    
    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)
    
    # Check the response contains our mocked data
    response_text = result.content[0].text
    assert "openssl" in response_text
    assert "3.1.0" in response_text
    assert "conancenter" in response_text
    assert "develop" in response_text
    assert "error" in response_text
    
    # Verify the command was called with wildcard
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "*ssl*" in call_args


@pytest.mark.anyio
async def test_search_conan_packages_missing_query(client_session: ClientSession):
    """Test that missing required parameter returns an error."""
    result = await client_session.call_tool("search_conan_packages", {})
    
    # Should return an error result, not raise an exception
    assert result.isError is True
    assert len(result.content) > 0
    assert "Field required" in result.content[0].text
    assert "query" in result.content[0].text


@pytest.mark.anyio
@patch('main.run_command')
async def test_search_conan_packages_empty_query(mock_run_command, client_session: ClientSession):
    """Test search with empty query."""
    # Mock empty search response (realistic structure)
    mock_response = {
        "conancenter": {}
    }
    mock_run_command.return_value = str(mock_response).replace("'", '"')
    
    result = await client_session.call_tool("search_conan_packages", {"query": ""})
    
    assert isinstance(result, CallToolResult)
    assert len(result.content) > 0
    assert isinstance(result.content[0], TextContent)
    
    # Check the response contains our mocked data
    response_text = result.content[0].text
    assert "conancenter" in response_text
    
    # Verify the command was called with empty query
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    assert "" in call_args  # Empty string in command args
    
