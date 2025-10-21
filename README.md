# Conan MCP Server

A Model Context Protocol server for Conan package manager integration.

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

**`get_conan_profile`**: Get Conan profile configuration
- `profile` (optional): If provided, show that specific profile; otherwise, default

**Examples:**
- `get_conan_profile()`
- `get_conan_profile(profile="linux-debug")`

**`list_conan_profiles`**: List available Conan profiles
- No parameters

**Examples:**
- `list_conan_profiles()`

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