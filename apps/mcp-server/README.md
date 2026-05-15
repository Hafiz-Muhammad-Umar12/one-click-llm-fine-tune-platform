# MCP Server - One-Click AI Platform

This service implements the **Model Context Protocol (MCP)**, allowing AI agents like Claude to programmatically interact with the platform.

## Features

- **list_datasets:** Retrieve available fine-tuning data.
- **trigger_training:** Start a new training job with specific hyperparameters.
- **get_job_status:** Monitor training progress.
- **list_deployments:** See active inference endpoints.

## Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "one-click-ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/apps/mcp-server",
      "env": {
        "AI_PLATFORM_API_KEY": "your-api-key",
        "AI_PLATFORM_BASE_URL": "https://api.platform.com/api/v1"
      }
    }
  }
}
```
