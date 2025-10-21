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
- *"Verify that my profile supports C++20"*

**`list_conan_profiles`** 

List available Conan profiles

Parameters:
- No parameters

Usage examples:

- *"What Conan profiles do I have available?"*
- *"List all my configured profiles"*

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