# Conan MCP Server

A Model Context Protocol server for Conan package manager integration.

## Usage Examples

> *"Create a CMake library project with Conan that has the latest version of fmt
> and openssl as requirements, install the dependencies and verify that the
> libraries I depend on don't have serious vulnerabilities and have a license
> that allows my application to be commercial."*

## Installation

### Requirements

- Python >= 3.10
- Conan [installed](https://docs.conan.io/2/installation.html)
- [uv](https://github.com/astral-sh/uv) (optional, recommended)

### MCP Configuration

Add to your `mcp.json`:

```json
{
  "mcpServers": {
    "conan": {
      "command": "uvx",
      "args": ["conan-mcp"]
    }
  }
}
```

#### Configuring Conan Binary Path

By default, the server uses `conan` from the system PATH (or the virtual environment where the MCP server is running). If you need to use a specific Conan installation or version, you can set the `CONAN_MCP_CONAN_PATH` environment variable in your MCP configuration:

```json
{
  "mcpServers": {
    "conan": {
      "command": "uv",
      "args": ["--directory", "/path/to/conan-mcp", "run", "conan-mcp"],
      "env": {
        "CONAN_MCP_CONAN_PATH": "/home/user/venv/bin/conan"
      }
    }
  }
}
```

If `CONAN_MCP_CONAN_PATH` is not set, the server will use `conan` from PATH or
the virtual environment where the MCP server is running.

### Available Tools

**`get_conan_profile`**: 

Get Conan profile configuration

Parameters:
- `profile` (optional): If provided, show that specific profile; otherwise, default

Usage examples:

- *"What is my default Conan profile?"*
- *"Show me the linux-debug profile configuration"*

**`list_conan_profiles`** 

List available Conan profiles

Parameters:
- No parameters

Usage examples:

- *"What Conan profiles do I have available?"*

**`create_conan_project`**

Create a new Conan project with specified dependencies

Parameters:
- `template` (required): Template type for the project.
  - Libraries: `cmake_lib` (default), `header_lib`, `meson_lib`, `msbuild_lib`, `bazel_lib`, `autotools_lib`
  - Executables: `cmake_exe` (default), `meson_exe`, `msbuild_exe`, `bazel_exe`, `autotools_exe`
- `name` (required): Name of the project
- `version` (optional): Version of the project (default: "0.1")
- `requires` (optional): List of dependencies with versions (e.g., ["fmt/12.0.0", "openssl/3.6.0"])
- `tool_requires` (optional): List of tool dependencies (e.g., ["cmake/4.1.2", "ninja/1.13.1", "meson/1.9.1"])
- `work_dir` (**required**): Working directory where the command should be executed. The project will be created directly in this directory.
- `force` (optional): Overwrite existing files if they exist (default: False)

Usage examples:

- *"Create a new CMake executable project called 'myapp' with fmt and openssl dependencies"*
- *"Create a header-only library project called 'mylib'"*
- *"Create a Meson executable project with gtest and spdlog dependencies"*
- *"Create a CMake library project with boost dependencies and cmake tool_requires"*

**`list_conan_packages`**

List recipes and packages from the local cache or configurated remotes

Parameters:
- `name` (**required**): Package name.
- `version` (optional): Version or version range.
- `user` (optional): User name to search. 
- `channel` (optional): Channel name to search.
- `recipe_revision` (optional): Recipe revision (rrev). Use `"*"` for all, `"latest"` for latest.
- `package_id` (optional): Package ID. Use `"*"` for all packages.
- `filter_settings` (optional): List of setting filters. E.g. `["arch=armv8", "os=Windows"]`.
- `filter_options` (optional): List of option filters. E.g. `["*:fPIC=True", "*:shared=False"]`.
- `remote` (optional): Remote name to search in. Use `"*"`for all.
- `search_in_cache` (optional): Whether to include the local cache in the search.

Usage examples:
- *"List all available versions for fmt in conancenter"*  
- *"List versions of zlib with architecture armv8 and shared=False"*
- *"Show all zlib packages for Windows armv8 in my local cache"*
- *"List all packages that contain boost in the name in conancenter"*
- *"Search for fmt versions greater than or equal to 8.0 but less than 9.0 in conancenter"*
- *"Search for zlib versions compatibles with 1.3.x in every remote"*
- *"List versions of poco provided by user barbarian and channel stable in local cache"*
- *"Provide all packages for zlib 1.3 that use the recipe at revision b3b71bfe8dd07abc7b82ff2bd0eac021 in conancenter"*   

**`install_conan_packages`**

Install all dependencies of a Conan recipe, producing a full dependency graph. 

Parameters:
- `path` (**required**): Path to the folder containing the recipe, or to a `conanfile.txt` or `conanfile.py`. This path is ALWAYS relative to `work_dir`.
- `work_dir` (**required**): Working directory where the command should be executed. This is the base directory from which all paths are resolved.
- `remote` (optional): Name of the remote to search for dependencies. If omitted, all remotes are searched.
- `search_in_cache` (optional): Do not use remote, resolve exclusively in the cache.
- `settings_host` (optional): List of settings (host context) to override. Example: `["arch=armv8", "os=Windows", "build_type=Release"]`
- `options_host` (optional): List of options (host context) to override. Example: `["fPIC=True", "shared=False"]`
- `build_missing` (optional): Boolean, build missing binary dependencies from source if not available (`false` by default).

Usage examples:
- *"Install dependencies in this project using conancenter"*
- *"Install dependencies from ~/project for architecture armv8, and shared=False build the missing binaries"*
- *"Install dependencies in this project use windows profile for host and linux profile for build"*

**`audit_conan_scan`**

Scan Conan packages and dependencies for security vulnerabilities

Parameters:
- `path` (**required**): Path to the folder containing the recipe or to a `conanfile.txt`/`conanfile.py`.

Usage examples:
- *"Scan dependencies in this project for known vulnerabilities"*
- *"Scan the latest version of zlib for vulnerabilities"*


## Local Development

### Clone and run

```bash
# Clone the repository
git clone https://github.com/conan-io/conan-mcp.git
cd conan-mcp

# Install dependencies
uv sync

# Run the server
uv run conan-mcp
```

### Local MCP configuration

For local development, use the absolute path:

```json
{
  "mcpServers": {
    "conan": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/conan-mcp", "run", "conan-mcp"]
    }
  }
}
```

### Testing with MCP Inspector

You can test the server using the MCP Inspector to verify it's working
correctly:

```bash
uv run mcp dev main.py
```

### Running Conan MCP Server tests

See [test/README.md](test/README.md) for detailed testing instructions.

## License

MIT License