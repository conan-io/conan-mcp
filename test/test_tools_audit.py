from unittest.mock import patch

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from conan_mcp.main import mcp


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
@patch("conan_mcp.main.run_command")
async def test_audit_conan_scan(
    mock_run_command, client_session: ClientSession
):
    """Test basic conan audit scan command composition."""
    mock_run_command.return_value = '{"result": "success"}'

    await client_session.call_tool(
        "audit_conan_scan", {"path": "/path/to/conanfile.txt", "work_dir": "/path/to/project"}
    )

    # Verify the command was composed correctly
    mock_run_command.assert_called_once()
    call_args = mock_run_command.call_args[0][0]
    expected_cmd = ["conan", "audit", "scan", "/path/to/conanfile.txt", "--format", "json"]
    assert call_args == expected_cmd
