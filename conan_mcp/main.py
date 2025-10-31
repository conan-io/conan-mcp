import asyncio
import json
import os

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("conan-mcp")


def _get_conan_binary() -> str:
    """Get the Conan binary path from environment variable or default to 'conan'.

    Returns:
        Path to conan binary. Defaults to 'conan' if CONAN_MCP_CONAN_PATH is not set.
    """
    return os.environ.get("CONAN_MCP_CONAN_PATH", "conan")


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
            stdin=asyncio.subprocess.DEVNULL,
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
    description="""
    Search for Conan packages across remotes with fine-grained filtering.

    Use this tool when you need to:
    - Check available versions of dependencies
    - Find the latest version of a package
    - Search for packages by name
    - Search for packages by version or version range
    - Search for packages and filter them using filter settings or filter options
    - Search for package specifying package ID, or recipe revision

     Examples:
     - list_conan_packages(name="fmt", version="1.0.0") - List all available versions for fmt/1.0.0 package.
     - list_conan_packages(name="fmt", filter_settings=["arch=armv8"]) - List all available versions for fmt package with architecture armv8
     - list_conan_packages(name="fmt", filter_options=["*:fPIC=True"]) - List all available versions for fmt package with fPIC

    Args:
        name: Package name pattern (required). Supports wildcards:
            - "fmt" : exact name
            - "fmt*" : starts with "fmt"
            - "*fmt*" : contains "fmt"
            - "*fmt" : ends with "fmt"
        version: Version or version range (default: "*"). Supports Conan2 syntax:
            - "1.2.3" : exact version
            - "[>=1.0 <2.0]" : range >=1.0 and <2.0
            - "[~1.2]" : compatible with 1.2.x
            - "[^1.0]" : compatible up to next major
            - "[>1 <2.0 || ^3.2]" : multiple ranges
        user: User name (default: None). Use "*" for all users.
        channel: Channel name (default: None). Use "*" for all channels.
        recipe_revision: Recipe revision (rrev) (default: None). 
            Use "*" for all, "latest" for latest.
            Use it together with package_id to find all packages with the same recipe revision.
        package_id: Package ID (default: None). Use "*" for all packages.
            Use "*" when you are trying to find all packages.
            Use it together with include_all_package_revisions to include all package revisions.
        filter_settings: Filter by settings (default: None). List of strings:
            Pass as list of strings, e.g. ["arch=armv8", "os=Windows", "build_type=Release"]
            - ["arch=armv8"] : architecture
            - ["os=Windows"] : operating system
            - ["build_type=Release"] : build type
            - ["compiler=gcc"] : compiler
            - ["compiler_version=11"] : compiler version
            - ["compiler_runtime=libstdc++11"] : compiler runtime
            - ["compiler_runtime_version=11"] : compiler runtime version
        filter_options: Filter by options (default: None). List of strings:
            Pass as list of strings, e.g. ["*:fPIC=True", "*:header_only=True", "*:shared=False", "*:with_boost=True"]
            - ["*:fPIC=True"] : fPIC option
            - ["*:header_only=True"] : header only
            - ["*:shared=False"] : shared library
            - ["*:with_boost=True"] : with boost option
        remote: Remote name (default: "*"). 
            - None: Search in local cache only
            - "conancenter": Search in ConanCenter remote
            - "*": Search in all remotes
            - Other remote names: Search in specific remote
        search_in_cache: Include local cache in search (default: False). 
            - True: Search in both remotes and local cache
            - False: Search only in remotes (default)
            Note: This parameter should be set consistently across requests.
        include_all_package_revisions: Include all package revisions (default: False). 
            - True: Include all package revisions.
            - False: Include only the latest package revision (default)

    Returns:
        Dictionary containing available packages and their metadata.

     Examples:
         - list_conan_packages(name="fmt", version="1.0.0")
         - list_conan_packages(name="*boost*", filter_settings=["arch=armv8", "os=Windows"])
         - list_conan_packages(name="zlib", filter_options=["*:shared=True"])
    """
)
async def list_conan_packages(
    name: str = Field(description="Package name pattern (supports wildcards)"),
    version: str = Field(
        default="*", description="Version or version range to search for."
    ),
    user: str = Field(
        default=None, description="User name. Use * to search all users."
    ),
    channel: str = Field(
        default=None, description="Channel name. Use * to search all channels."
    ),
    recipe_revision: str = Field(
        default=None,
        description='Recipe revision number also know as rrev. Use * to search all revisions. Use "latest" to search the latest revision.',
    ),
    package_id: str = Field(
        default=None, description="Package ID. Use * to search all packages."
    ),
    filter_settings: list[str] = Field(
        default=None,
        description="Filter settings like architecture, operating system, build type, compiler, compiler version, compiler runtime, compiler runtime version.",
    ),
    filter_options: list[str] = Field(
        default=None,
        description="Filter options like fPIC, header_only, shared, with_*, without_*, etc.",
    ),
    remote: str = Field(default="*", description="Name of the remote to search in."),
    search_in_cache: bool = Field(
        default=False, description="Include local cache in search"
    ),
    include_all_package_revisions: bool = Field(
        default=False, description="Include all package revisions"
    ),
) -> dict:
    if (filter_settings or filter_options) and not package_id:
        # No package ID provided, searching for all packages
        package_id = "*"

    pattern = f"{name}/{version if version else '*'}"
    pattern += (
        f"@{user if user else '*'}/{channel if channel else '*'}"
        if user or channel
        else ""
    )
    pattern += f"#{recipe_revision}" if recipe_revision else ""
    if package_id:
        pattern += f":{package_id}"
        pattern += "#*" if include_all_package_revisions else ""

    cmd = [_get_conan_binary(), "list", pattern, "--format=json"]
    if remote:
        cmd.extend(["--remote", remote])
    if filter_settings:
        for fs in filter_settings:
            cmd.extend(["-fs", fs])
    if filter_options:
        for fo in filter_options:
            cmd.extend(["-fo", fo])
    if search_in_cache:
        cmd.extend(["--cache"])
    raw_output = await run_command(cmd)
    return json.loads(raw_output)


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
    profile: str = Field(
        default=None,
        description="Specific profile name to retrieve. If not provided, uses the default profile.",
    ),
) -> dict:
    cmd = [_get_conan_binary(), "profile", "show", "--format=json"]
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
    cmd = [_get_conan_binary(), "profile", "list", "--format=json"]
    raw_output = await run_command(cmd)
    return json.loads(raw_output)


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
        - install_conan_packages(path="C:/Users/username/project/conanfile.txt")
        - install_conan_packages(path="~/folder/conanfile.py", remote="conancenter")
        - install_conan_packages(path="/home/username/project/conanfile.py",
                                settings_host="os=Windows,arch=armv8")

    Args:
        path: Path to a folder containing a recipe or to a recipe file (conanfile.txt or conanfile.py)
        remote: Optional remote name to search in (searches all remotes if not specified)
        search_in_cache: Do not use remote, resolve exclusively in the cache.
        build_profile: Profile to the build context.
        host_profile: Profile to the host context.
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
    path: str = Field(
        description="Path to the folder containing the recipe of the project or to a recipe file conanfile.txt/.py"
    ),
    remote: str = Field(
        default=None, description="Remote name. Omit  to search in all remotes."
    ),
    search_in_cache: bool = Field(
        default=False,
        description="Do not use remote, resolve exclusively in the cache.",
    ),
    build_profile: str = Field(
        default=None,
        description="Profile to the build context.",
    ),
    host_profile: str = Field(
        default=None,
        description="Profile to the host context.",
    ),
    settings_host: list[str] = Field(
        default=None,
        description=(
            "Apply different settings like architecture, operating system, build type, compiler, "
        ),
    ),
    options_host: list[str] = Field(
        default=None,
        description=(
            "Apply options like fPIC, header_only, shared, with_*, without_*, etc. to the host context only. "
        ),
    ),
    build_missing: bool = Field(
        default=False,
        description="Build all the missing binary dependencies when they are not available in the cache or in the remotes for download.",
    ),
) -> dict:
    cmd = ["conan", "install", path]

    if remote and not search_in_cache:
        cmd.extend(["--remote", remote])

    if search_in_cache:
        cmd.extend(["--no-remote"])

    if build_profile:
        cmd.extend(["-pr:b", build_profile])

    if host_profile:
        cmd.extend(["-pr:h", host_profile])

    if settings_host:
        for sh in settings_host:
            cmd.extend(["-s:h", sh])
    if options_host:
        for oh in options_host:
            cmd.extend(["-o:h", oh])

    timeout = 90.0

    if build_missing:
        cmd.extend(["--build=missing"])
        timeout = 300.0

    cmd.extend(["--format=json"])

    raw_output = await run_command(cmd, timeout=timeout)
    return json.loads(raw_output)


@mcp.tool(
    description="""Create a new Conan project with specified dependencies.
    
    This tool creates a new Conan project using templates and automatically adds
    the specified dependencies. Useful for setting up new projects with common
    libraries like fmt, openssl, boost, etc.
    
    Note: The generated code contains placeholder examples. You need to review
    and update: includes/imports, source code usage, and build system targets
    (CMakeLists.txt, meson.build, etc.) to properly use your specified dependencies.
    
    Args:
        template: Template type for the project.
                  
                  Libraries (produce libraries to be linked):
                  - cmake_lib: CMake library (default for libraries)
                  - header_lib: Header-only library
                  - meson_lib: Meson build system
                  - msbuild_lib: Visual Studio / MSBuild (Windows only)
                  - bazel_lib: Bazel build system (experimental)
                  - autotools_lib: Autotools (configure/make)
                  
                  Executables (programs that can be run):
                  - cmake_exe: CMake executable (default for executables)
                  - meson_exe: Meson build system
                  - msbuild_exe: Visual Studio / MSBuild (Windows only)
                  - bazel_exe: Bazel build system (experimental)
                  - autotools_exe: Autotools (configure/make)
                  
                  Note: If the user doesn't specify build system, use cmake_lib
                  for libraries or cmake_exe for executables as defaults.
        name: Name of the project
        version: Version of the project (default: "0.1")
        requires: List of dependencies with versions (e.g., ['fmt/12.0.0', 
                  'openssl/3.6.0'])
        tool_requires: List of tool dependencies with versions. Common examples:
                      - ['cmake/4.1.2'] - CMake build tool
                      - ['ninja/1.13.1'] - Ninja build system
                      - ['meson/1.9.1'] - Meson build system
        output_dir: Output directory for the project (default: current directory)
        force: Overwrite existing files if they exist (default: False)
    
    Returns:
        Dictionary containing:
        - result: Success message with project details, dependency note, and 
                  raw output from the conan new command
    """
)
async def create_conan_project(
    template: str = Field(
        description="Template type for the project. If not specified, use cmake_lib for libraries or cmake_exe for executables"
    ),
    name: str = Field(description="Name of the project"),
    version: str = Field(default="0.1", description="Version of the project"),
    requires: list[str] = Field(
        default=None,
        description="List of dependencies with versions",
    ),
    tool_requires: list[str] = Field(
        default=None,
        description="List of tool dependencies with versions. Common examples: ['cmake/4.1.2'], ['ninja/1.13.1'], ['meson/1.9.1']",
    ),
    output_dir: str = Field(
        default=".", description="Output directory for the project"
    ),
    force: bool = Field(
        default=False, description="Overwrite existing files if they exist"
    ),
) -> dict:
    """Create a new Conan project with specified dependencies."""

    # Build the conan new command
    cmd = [_get_conan_binary(), "new", template]

    # Add template arguments
    cmd.extend(["--define", f"name={name}"])
    cmd.extend(["--define", f"version={version}"])

    # Add dependencies if provided
    if requires:
        for dep in requires:
            if dep.strip():  # Skip empty strings
                cmd.extend(["--define", f"requires={dep.strip()}"])

    # Add tool dependencies if provided
    if tool_requires:
        for dep in tool_requires:
            if dep.strip():  # Skip empty strings
                cmd.extend(["--define", f"tool_requires={dep.strip()}"])

    # Add output directory
    if output_dir != ".":
        cmd.extend(["--output", output_dir])

    # Add force flag if requested
    if force:
        cmd.append("--force")

    output = await run_command(cmd)

    deps_note = (
        f" (WARNING: Review and update the generated code to use these dependencies: {', '.join(requires)} - check includes, source code usage, and build system targets)"
        if requires
        else ""
    )
    return {
        "result": f"Project '{name}' created successfully with template '{template}'{deps_note}\n\nOutput:\n{output}"
    }


def main():
    """Main entry point."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
