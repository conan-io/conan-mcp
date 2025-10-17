import asyncio

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("conan-mcp")


async def run_command(cmd: list[str]) -> str:
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
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            return stdout.decode("utf-8", "replace")
        else:
            error_msg = stderr.decode("utf-8", "replace").strip()
            if not error_msg:
                error_msg = f"Conan command failed with return code {proc.returncode}"
            raise RuntimeError(f"Command error: {error_msg}")
    except asyncio.CancelledError:
        if proc:
            proc.kill()
        raise
    except FileNotFoundError:
        raise RuntimeError("Command not found.")
    except Exception as e:
        raise RuntimeError(f"Error running command: {str(e)}")

@mcp.tool(
    description=
        "List the available versions for conan packages specified by the user using a fine-grained search query."
        "Use just the parameters you need to search for the package. All parameters are optional. Except for name."
)
async def list_conan_packages(
    name: str = Field(description=
        'Pattern like'
        ' - "fmt" : library exact name'
        ' - "fmt*" : library name starting with "fmt"'
        ' - "*fmt*" : library name containing "fmt"'
        ' - "*fmt" : library name ending with "fmt"'

    ),
    version: str = Field(default="*",description=
        'Version or version range to search for.'
        'Supports Conan2 version range syntax, e.g.:'
        '  - "1.2.3" : exact version'
        '  - "[>=1.0 <2.0]" : any version >=1.0 and <2.0'
        '  - "[~1.2]" : compatible with 1.2.x'
        '  - "[^1.0]" : compatible up to next major version'
        '  - "[>1 <2.0 || ^3.2]" : compatible with 1.x or 3.2.x'
        '  - "*" : all versions'
    ),
    user: str = Field(default="*", description=
        'User name. Use * to search all users.'
    ),
    channel: str = Field(default="*", description=
        'Channel name. Use * to search all channels.'
    ), 
    recipe_revision: str = Field(default="",description=
        'Recipe revision number also know as rrev. Use * to search all revisions. Use "latest" to search the latest revision.'
    ),
    package_id: str = Field(default="", description=
        'Package ID. Use * to search all packages.'
    ),
    package_revision: str = Field(default="", description=
        'Package revision number also know as prev. Use * to search all revisions.'
    ),
    filter_settings: [str] = Field(default=None, description=
        'Filter settings like architecture, operating system, build type, compiler,'
        'compiler version, compiler runtime, compiler runtime version.'
        'Omit to search all filter options.'
        'To use more than one filter setting, use a comma to separate them. e.g. "arch=armv8,os=Windows,build_type=Release"'
        ' - "arch=armv8" : architecture'
        ' - "os=Windows" : operating system'
        ' - "build_type=Release" : build type'
        ' - "compiler=gcc" : compiler'
        ' - "compiler_version=11" : compiler version'
        ' - "compiler_runtime=libstdc++11" : compiler runtime'
        ' - "compiler_runtime_version=11" : compiler runtime version'
    ),
    filter_options: [str] = Field(default=None, description=
        'Filter options like fPIC, header_only, shared, with_*, without_*, etc.'
        'Omit to search all filter options.'
        'To use more than one filter option, use a comma to separate them. e.g. "fPIC=True,header_only=True"'
        ' - "*:fPIC=True" : fPIC'
        ' - "*:header_only=True" : header only'
        ' - "*:shared=False" : shared'
        ' - "&:with_boost=True", &:with_os_api=False : Specify multiple filter options'
        'Use "&:fPIC=True" to refer to the current package.'
        'Use "*:fPIC=True" or other pattern if the intent was to apply to dependencies'
    ),
    remote: str = Field(default="*", description=
        "Remote name. Omit to search all remotes. Dont use if you are not sure about the remote."
    )
) -> str:
    """
    List the available versions for Conan packages across remotes.
    Supports filter settings and filter options.
    Supports version range syntax.
    Supports user and channel.
    Supports recipe revision and package revision.
    Supports package ID.
    Supports output format.
    Supports remote.

    Use this tool when you need to:
    - Check available versions of dependencies
    - Find the latest version of a package
    - Search for packages by name
    - Search for packages by version or version range
    - Search for packages and filter them using filter settings or filter options
    - Search for package spefycing package ID, recipe revision, or package revision

    Examples:
    - list_conan_packages(name="fmt", version="1.0.0") - List all available versions for fmt/1.0.0 package in JSON format
    - list_conan_packages(name="fmt", filter_settings="arch=armv8") - List all available versions for fmt package in JSON format with architecture armv8
    - list_conan_packages(name="fmt", filter_options="fPIC=True") - List all available versions for fmt package in JSON format with fPIC

    Args:
        name: Library name.
        Optional: version: Version or version range to search for.
        Optional: user: User name. Optional.
        Optional: channel: Channel name.
        Optional: recipe_revision: Recipe revision number also know as rrev.
        Optional: package_id: Package ID.
        Optional: package_revision: Package revision number also know as prev.
        Optional: filter_settings: Filter settings like architecture, operating system, build type, compiler, compiler version, compiler runtime, compiler runtime version.
        Optional: filter_options: Filter options like fPIC, header_only, shared, with_*, without_*, etc.
        Optional: remote: Remote name. Omit to search all remotes.
    
    Returns:
        JSON string with list of available versions from Conan

    """

    if filter_settings or filter_options and not package_id:
        print("No package ID provided, searching for all packages")
        package_id = "*"

    cmd = ["conan", "list", f"{name}/{version}@{user}/{channel}#{recipe_revision}:{package_id}#{package_revision}", "--format=json"]
    if remote:
        cmd.extend(["--remote", remote])
    if filter_settings:
        cmd.extend([ i for fs in filter_settings.split(",")  for i in ( '-fs', fs)])
    if filter_options:
        cmd.extend([ i for fo in filter_options.split(",")  for i in ( '-fo', fo)])
    
    return await run_command(cmd)

# @mcp.tool(
#     description="Search for Conan packages and check available versions across remotes."
# )
# async def search_conan_packages(
#     query: str = Field(description='Pattern like "fmt/*", "boost", or "*ssl*"'),
#     remote: str = Field(default=None, description="Remote name. Omit to search all remotes.")
# ) -> str:
#     """Search for Conan packages across remotes.

#     Searches for Conan packages matching the given query pattern. Supports wildcards
#     and can search in all remotes or a specific one.

#     Use this tool when you need to:
#     - Check available versions of dependencies
#     - Find the latest version of a package
#     - Search for packages by name
#     - Update project dependencies

#     Examples:
#     - search_conan_packages("boost") - Find all boost versions
#     - search_conan_packages("fmt") - Find all fmt versions
#     - search_conan_packages("*boost*") - Find packages containing 'boost'

#     Args:
#         query: Search pattern for package names (supports wildcards like *boost*)
#         remote: Optional remote name to search in (searches all remotes if not specified)

#     Returns:
#         JSON string with search results from Conan
#     """

#     cmd = ["conan", "search", query, "--format=json"]
#     if remote:
#         cmd.extend(["--remote", remote])

#     return await run_command(cmd)


def main():
    """Main entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
