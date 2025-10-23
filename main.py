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

@mcp.tool(
    description="""
    Install Conan package dependencies from a recipe file (conanfile.py or conanfile.txt).

    This tool uses the `conan install` command to install the dependencies of a Conan recipe.
    It provides a complete, structured view of all nodes and relationships in the dependency graph.

    If any requirement is not found in the local cache, it will iterate the remotes looking for it.
    When the full dependency graph is computed and all dependency recipes have been found, it will look
    for binary packages matching the current settings and options. If no binary package is found for
    some dependencies, it will error unless the 'build_missing' argument is used to build from source.

    Examples:
        - install_conan_packages(path="C:/Users/dani/project/conanfile.txt")
        - install_conan_packages(path="~/folder/conanfile.py", remote="conancenter")
        - install_conan_packages(path="/home/dani/project/conanfile.py",
                                settings_host="os=Windows,arch=armv8")

    Args:
        path: Path to a folder containing a recipe or to a recipe file (conanfile.txt or conanfile.py)
        remote: Optional remote name to search in (searches all remotes if not specified)
        settings_host: Substitute settings from the default host profile (architecture, OS, etc.)
            Omit to use the settings of the default host profile.
            e.g. ["arch=armv8", "os=Windows", "build_type=Release"] 
            - "arch=armv8": architecture,
            - "os=Windows": operating system, 
            - "build_type=Release": build type,
            - "compiler=gcc": compiler,
            - "compiler.version=11": compiler version,
            - "compiler.runtime=libstdc++11": compiler runtime,
            - "compiler.runtime_version=11": compiler runtime version'
        options_host: Substitute options from the default host profile (fPIC, shared, etc.)
            Omit to use the options of the default host profile.
            e.g. ["fPIC=True", "shared=False"]
            - "Use "&:fPIC=True" to refer to the current package. "
            - "Use "*:fPIC=True" or other pattern if the intent was to apply to dependencies"
            - "*:fPIC=True": fPIC for all packages,
            - "&:shared=False": shared for the current package,
            - "*:with_boost=True": with boost option for all packages,
        build_missing: Build missing binary dependencies from source

    Returns:
        JSON string with dependency graph metadata including installation status for each package.

        The "binary" and "recipe" fields on each node indicate the package status:
        - Missing: Recipe/binary not found, needs to be built
        - Invalid: Package invalid due to recipe restrictions
        - Build: Package has been built
        - Cache: Recipe/binary exists in local cache
        - Skip: Package skipped from installation
        - Download: Recipe/binary was downloaded
        - null: Binary unknown (e.g., consumer conanfile.txt)
    """
)
async def install_conan_packages(
    path: str = Field(description='Path to the folder containing the recipe of the project or to a recipe file conanfile.txt/.py'),
    remote: str = Field(default=None, description="Remote name. Omit  to search in all remotes."),
    settings_host: list[str] = Field(
        default=None,
        description=(
            "Apply different settings like architecture, operating system, build type, compiler, "
        )
    ),
    options_host: list[str] = Field(
        default=None,
        description=(
            "Apply options like fPIC, header_only, shared, with_*, without_*, etc. to the host context only. "
        )
    ),
    build_missing: bool = Field(
        default=False,
        description="Build all the missing binary dependencies when they are not available in the cache or in the remotes for download."
    ),
) -> dict:

    cmd = ["conan", "install", path]

    if remote:
        cmd.extend(["--remote", remote])

    if settings_host:
        for setting in settings_host.split(","):
            cmd.extend(["-s:h", setting.strip()])
    if options_host:
        for option in options_host.split(","):
            cmd.extend(["-o:h", option.strip()])

    timeout = 90.0

    if build_missing:
        cmd.extend(["--build=missing"])
        timeout = 300.0

    cmd.extend(["--format=json"])

    raw_output = await run_command(cmd, timeout=timeout)
    return json.loads(raw_output)


def main():
    """Main entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
