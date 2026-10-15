"""
Weather Agent - Connects to Remote MCP Server on Cloud Run
Successfully connects to custom MCP HTTP endpoints!
"""
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
from dotenv import load_dotenv
import logging
import os
from pathlib import Path

# ADK normally loads .env when started by its CLI. Loading it here as well makes
# imports and verification work from any current working directory.
CLIENT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(CLIENT_DIR / ".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mặc định: server chạy local. Deploy lên Cloud Run thì đặt MCP_SERVER_URL trong .env
# (ví dụ: https://<service>.run.app/mcp). verify_setup.py đọc cùng biến này.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

logger.info("Initializing weather agent with remote MCP server")
logger.info("MCP Server: %s", MCP_SERVER_URL)

# McpToolset connects lazily when the agent handles a request.
connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)
weather_tools = McpToolset(connection_params=connection_params)

root_agent = Agent(
    name="weather_agent",
    model="gemini-3.8-flash",
    description="An assistant that provides current weather and short forecasts.",
    instruction=(
        "Answer weather questions by using the MCP weather tools. "
        "Use get_current_weather for current conditions and get_forecast for "
        "1-3 day forecasts. Ask for a city when the user did not provide one. "
        "Do not invent weather data when a tool call fails."
    ),
    tools=[weather_tools],
)
logger.info("Weather agent configured with MCP tools")

