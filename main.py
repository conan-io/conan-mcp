import asyncio

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("conan-mcp")


async def run_command(cmd: list[str], timeout: float = 30.0) -> str:
    """Execute a command and return the output.
    
    Args:
        cmd: List of command arguments (e.g., ["conan", "search", "boost"])
        
    Returns:
        Command output as string
        
    Raises:
        RuntimeError: If command is not found or fails
    """
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        if proc.returncode == 0:
            return stdout.decode("utf-8", "replace")
        else:
            error_msg = stderr.decode("utf-8", "replace").strip()
            if not error_msg:
                error_msg = f"Conan command failed with return code {proc.returncode}"
            raise RuntimeError(f"Command error: {error_msg}")
    except asyncio.TimeoutError:
        if proc:
            proc.kill()
        raise RuntimeError(f"Command timeout after {timeout}s")
    except asyncio.CancelledError:
        if proc:
            proc.kill()
        raise
    except FileNotFoundError:
        raise RuntimeError("Command not found.")
    except Exception as e:
        raise RuntimeError(f"Error running command: {str(e)}")


@mcp.tool(
    description="Get Conan profile configuration for the user's platform and build environment"
)
async def get_conan_profile(
    profile: str = Field(default=None, description="Specific profile name to retrieve. If not provided, uses the default profile.")
) -> str:
    """Get Conan profile configuration.
    
    This tool should be called when the user mentions:
    - Their platform (Windows, macOS, Linux)
    - Their compiler (gcc, clang, msvc, etc.)
    - Their architecture (x86_64, arm64, etc.)
    - Build configurations
    - When they want to list packages for their specific platform
    - When they need context about their Conan environment
    - When they want to check a specific profile configuration
    
    This is typically a prerequisite step before listing packages or making 
    platform-specific recommendations, as it provides essential context about
    the user's build environment.
    
    Args:
        profile: Optional profile name to retrieve. If not specified, retrieves the default profile.
    
    Returns:
        JSON string containing both host and build profile configurations.
        The JSON structure includes:
        - "host": Host profile settings (compiler, arch, build_type, etc.)
        - "build": Build profile settings (compiler, arch, build_type, etc.)
        - Additional configuration like package_settings, options, tool_requires, etc.
    """
    cmd = ["conan", "profile", "show", "--format=json"]
    if profile:
        cmd.extend(["--profile", profile])
    return await run_command(cmd)


@mcp.tool(
    description="List available Conan profiles."
)
async def list_conan_profiles() -> str:
    """List Conan profiles available.

    Use this tool to see which profiles are available to select or inspect.

    Returns:
        JSON string with a list of profile names.
    """
    cmd = ["conan", "profile", "list", "--format=json"]
    return await run_command(cmd)


@mcp.tool(
    description="Search for Conan packages and check available versions across remotes."
)
async def search_conan_packages(
    query: str = Field(description='Pattern like "fmt/*", "boost", or "*ssl*"'),
    remote: str = Field(default=None, description="Remote name. Omit to search all remotes.")
) -> str:
    """Search for Conan packages across remotes.

    Searches for Conan packages matching the given query pattern. Supports wildcards
    and can search in all remotes or a specific one.

    Use this tool when you need to:
    - Check available versions of dependencies
    - Find the latest version of a package
    - Search for packages by name
    - Update project dependencies

    Examples:
    - search_conan_packages("boost") - Find all boost versions
    - search_conan_packages("fmt") - Find all fmt versions
    - search_conan_packages("*boost*") - Find packages containing 'boost'

    Args:
        query: Search pattern for package names (supports wildcards like *boost*)
        remote: Optional remote name to search in (searches all remotes if not specified)

    Returns:
        JSON string with search results from Conan
    """

    cmd = ["conan", "search", query, "--format=json"]
    if remote:
        cmd.extend(["--remote", remote])

    return await run_command(cmd)


def main():
    """Main entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
