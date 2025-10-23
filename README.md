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

**`conan_new`**

Create a new Conan project with specified dependencies

Parameters:
- `template` (required): Template type for the project. Available templates: basic, cmake_lib, cmake_exe, header_lib, meson_lib, meson_exe, msbuild_lib, msbuild_exe, bazel_lib, bazel_exe, autotools_lib, autotools_exe, premake_lib, premake_exe, local_recipes_index, workspace
- `name` (required): Name of the project
- `version` (optional): Version of the project (default: "1.0")
- `requires` (optional): List of dependencies with versions (e.g., ["fmt/12.0.0", "openssl/3.6.0"])
- `output_dir` (optional): Output directory for the project (default: current directory)
- `force` (optional): Overwrite existing files if they exist (default: False)

Usage examples:

- *"Create a new CMake executable project called 'myapp' with fmt and openssl dependencies"*
- *"Create a header-only library project called 'mylib'"*
- *"Create a Meson executable project with gtest and spdlog dependencies"*


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