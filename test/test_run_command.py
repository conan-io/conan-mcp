import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from conan_mcp.main import run_command


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestRunCommand:
    """Comprehensive tests for the run_command function using mocking."""

    @pytest.mark.anyio
    async def test_successful_command_execution(self):
        """Test successful command execution with valid output."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Hello World\n", b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_create:
            result = await run_command(["echo", "Hello World"])
            
            assert result == "Hello World\n"
            mock_create.assert_called_once_with(
                "echo", "Hello World",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None
            )

    @pytest.mark.anyio
    async def test_command_with_non_zero_exit_code(self):
        """Test command that fails with non-zero exit code."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"Command failed: file not found")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command error: Command failed: file not found"):
                await run_command(["invalid_command"])

    @pytest.mark.anyio
    async def test_command_with_empty_stderr(self):
        """Test command that fails but has empty stderr."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 2
        mock_proc.communicate.return_value = (b"", b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command error: Conan command failed with return code 2"):
                await run_command(["failing_command"])

    @pytest.mark.anyio
    async def test_command_timeout(self):
        """Test command that times out."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = asyncio.TimeoutError()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command timeout after 30.0s"):
                await run_command(["slow_command"])

    @pytest.mark.anyio
    async def test_command_timeout_with_custom_timeout(self):
        """Test command timeout with custom timeout value."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = asyncio.TimeoutError()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command timeout after 5.0s"):
                await run_command(["slow_command"], timeout=5.0)

    @pytest.mark.anyio
    async def test_command_cancellation(self):
        """Test command cancellation handling."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = asyncio.CancelledError()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(asyncio.CancelledError):
                await run_command(["cancelled_command"])

    @pytest.mark.anyio
    async def test_command_not_found(self):
        """Test command not found error."""
        with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError()):
            with pytest.raises(RuntimeError, match="Command not found."):
                await run_command(["nonexistent_command"])

    @pytest.mark.anyio
    async def test_generic_exception_handling(self):
        """Test handling of generic exceptions."""
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Unexpected error")):
            with pytest.raises(RuntimeError, match="Error running command: Unexpected error"):
                await run_command(["problematic_command"])

    @pytest.mark.anyio
    async def test_unicode_output_handling(self):
        """Test handling of unicode output with replacement strategy."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        # Simulate output with invalid UTF-8 bytes
        mock_proc.communicate.return_value = (b"Hello \xff World\n", b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            result = await run_command(["echo", "unicode_test"])
            # Should handle invalid UTF-8 gracefully with replacement
            assert "Hello" in result
            assert "World" in result

    @pytest.mark.anyio
    async def test_stderr_with_unicode(self):
        """Test handling of unicode in stderr."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"Error: \xe2\x80\x9cfile\xe2\x80\x9d not found")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command error: Error: .*file.* not found"):
                await run_command(["unicode_error_command"])

    @pytest.mark.anyio
    async def test_process_kill_on_timeout(self):
        """Test that process is killed on timeout."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = asyncio.TimeoutError()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command timeout after 30.0s"):
                await run_command(["slow_command"])
            
            # Verify process was killed
            mock_proc.kill.assert_called_once()

    @pytest.mark.anyio
    async def test_process_kill_on_cancellation(self):
        """Test that process is killed on cancellation."""
        mock_proc = AsyncMock()
        mock_proc.communicate.side_effect = asyncio.CancelledError()
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(asyncio.CancelledError):
                await run_command(["cancelled_command"])
            
            # Verify process was killed
            mock_proc.kill.assert_called_once()

    @pytest.mark.anyio
    async def test_multiline_output(self):
        """Test handling of multiline output."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        output = b"Line 1\nLine 2\nLine 3\n"
        mock_proc.communicate.return_value = (output, b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            result = await run_command(["multiline_command"])
            assert result == "Line 1\nLine 2\nLine 3\n"

    @pytest.mark.anyio
    async def test_empty_output(self):
        """Test handling of empty output."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            result = await run_command(["empty_output_command"])
            assert result == ""

    @pytest.mark.anyio
    async def test_command_with_arguments(self):
        """Test command with multiple arguments."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"arg1 arg2 arg3\n", b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_create:
            result = await run_command(["test_command", "arg1", "arg2", "arg3"])
            
            assert result == "arg1 arg2 arg3\n"
            mock_create.assert_called_once_with(
                "test_command", "arg1", "arg2", "arg3",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None
            )

    @pytest.mark.anyio
    async def test_wait_for_timeout_integration(self):
        """Test integration with asyncio.wait_for for timeout."""
        mock_proc = AsyncMock()
        # Simulate a command that takes longer than timeout
        async def slow_communicate():
            await asyncio.sleep(0.1)  # Simulate slow operation
            raise asyncio.TimeoutError()
        
        mock_proc.communicate = slow_communicate
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Command timeout after 0.05s"):
                await run_command(["slow_command"], timeout=0.05)
