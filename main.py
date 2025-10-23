import asyncio
import json

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
    description="""Get Conan profile configuration.
    
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
        Dictionary containing both host and build profile configurations.
        The dictionary structure includes:
        - "host": Host profile settings (compiler, arch, build_type, etc.)
        - "build": Build profile settings (compiler, arch, build_type, etc.)
        - Additional configuration like package_settings, options, tool_requires, etc.
    """
)
async def get_conan_profile(
    profile: str = Field(default=None, description="Specific profile name to retrieve. If not provided, uses the default profile.")
) -> dict:
    cmd = ["conan", "profile", "show", "--format=json"]
    if profile:
        cmd.extend(["--profile", profile])
    raw_output = await run_command(cmd)
    return json.loads(raw_output)


@mcp.tool(
    description="""List Conan profiles available.

    Use this tool to see which profiles are available to select or inspect.

    Returns:
        List of profile names.
    """
)
async def list_conan_profiles() -> list[str]:    
    cmd = ["conan", "profile", "list", "--format=json"]
    raw_output = await run_command(cmd)
    return json.loads(raw_output)


@mcp.tool(
    description="""Create a new Conan project with specified dependencies.
    
    This tool creates a new Conan project using templates and automatically adds
    the specified dependencies. It's perfect for quickly setting up new projects
    with common libraries like fmt, openssl, boost, etc.
    
    Note: The generated source code contains placeholder examples that don't use
    your specified dependencies. You must manually edit the source files to
    actually use the libraries you requested.
    
    Args:
        template: Template type for the project. Available templates: basic,
        cmake_lib, cmake_exe, header_lib, meson_lib, meson_exe, msbuild_lib,
        msbuild_exe, bazel_lib, bazel_exe, autotools_lib, autotools_exe,
        premake_lib, premake_exe, local_recipes_index, workspace name: Name of
        the project version: Version of the project (default: "1.0") requires:
        List of dependencies with versions (e.g., ['fmt/12.0.0',
        'openssl/3.6.0']) output_dir: Output directory for the project (default:
        current directory) force: Overwrite existing files if they exist
        (default: False)
    
    Returns:
        Dictionary with project creation details including output directory and
        created files.
    """
)
async def conan_new(
    template: str = Field(description="Template type for the project. Available templates: basic, cmake_lib, cmake_exe, header_lib, meson_lib, meson_exe, msbuild_lib, msbuild_exe, bazel_lib, bazel_exe, autotools_lib, autotools_exe, premake_lib, premake_exe, local_recipes_index, workspace"),
    name: str = Field(description="Name of the project"),
    version: str = Field(default="1.0", description="Version of the project"),
    requires: list[str] = Field(default=[], description="List of dependencies with versions (e.g., ['fmt/12.0.0', 'openssl/3.6.0'])"),
    output_dir: str = Field(default=".", description="Output directory for the project"),
    force: bool = Field(default=False, description="Overwrite existing files if they exist")
) -> dict:
    """Create a new Conan project with specified dependencies."""
    
    # Build the conan new command
    cmd = ["conan", "new", template]
    
    # Add template arguments
    cmd.extend(["-d", f"name={name}"])
    cmd.extend(["-d", f"version={version}"])
    
    # Add dependencies if provided
    if requires:
        for dep in requires:
            if dep.strip():  # Skip empty strings
                cmd.extend(["-d", f"requires={dep.strip()}"])
    
    # Add output directory
    if output_dir != ".":
        cmd.extend(["-o", output_dir])
    
    # Add force flag if requested
    if force:
        cmd.append("-f")
    
    output = await run_command(cmd)
    deps_note = f" (IMPORTANT: The generated code contains placeholder examples - you must edit the source files to actually use these dependencies: {', '.join(requires)})" if requires else ""
    return {
        "result": f"Project '{name}' created successfully with template '{template}'{deps_note}\n\nOutput:\n{output}"
    }


def main():
    """Main entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
