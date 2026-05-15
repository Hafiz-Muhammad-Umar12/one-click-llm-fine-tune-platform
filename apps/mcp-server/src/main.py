import os
import logging
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from ai_platform import AIPlatformClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-ai-platform")

# Initialize MCP Server
app = Server("one-click-ai-platform")

# Initialize SDK Client (expects API key in env)
API_KEY = os.getenv("AI_PLATFORM_API_KEY")
BASE_URL = os.getenv("AI_PLATFORM_BASE_URL", "http://localhost:8000/api/v1")

def get_client():
    if not API_KEY:
        raise ValueError("AI_PLATFORM_API_KEY environment variable is required")
    return AIPlatformClient(API_KEY, BASE_URL)

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for managing AI platform."""
    return [
        Tool(
            name="list_datasets",
            description="Returns a list of all datasets available for fine-tuning.",
            input_schema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="trigger_training",
            description="Starts a new LLM fine-tuning job.",
            input_schema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string", "description": "The UUID of the dataset to use."},
                    "base_model": {"type": "string", "description": "The name of the base model (e.g., meta-llama/Llama-3-8b)."},
                    "name": {"type": "string", "description": "A descriptive name for the training job."},
                    "method": {"type": "string", "enum": ["lora", "qlora", "full"], "default": "lora"}
                },
                "required": ["dataset_id", "base_model", "name"]
            }
        ),
        Tool(
            name="get_job_status",
            description="Checks the current status and metrics of a training job.",
            input_schema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "The UUID of the training job."}
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="list_deployments",
            description="Lists all active inference endpoints.",
            input_schema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a tool call."""
    client = get_client()
    
    try:
        if name == "list_datasets":
            datasets = client.list_datasets()
            return [TextContent(type="text", text=str(datasets))]
            
        elif name == "trigger_training":
            res = client.create_training_job(
                dataset_id=arguments["dataset_id"],
                base_model=arguments["base_model"],
                name=arguments["name"],
                hyperparameters={"method": arguments.get("method", "lora")}
            )
            return [TextContent(type="text", text=f"Training job started successfully. ID: {res['id']}")]
            
        elif name == "get_job_status":
            status = client.get_job_status(arguments["job_id"])
            return [TextContent(type="text", text=str(status))]
            
        elif name == "list_deployments":
            deployments = client.list_deployments()
            return [TextContent(type="text", text=str(deployments))]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

if __name__ == "__main__":
    from mcp.server.stdio import stdio_server
    import asyncio
    
    async def run():
        async with stdio_server() as (read_stream, write_server):
            await app.run(read_stream, write_server, app.create_initialization_options())
            
    asyncio.run(run())
