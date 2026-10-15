#!/usr/bin/env python3
"""
Verification script for Weather Agent setup
Checks if all components are configured correctly
"""
import os
import sys
import asyncio
from pathlib import Path

CLIENT_DIR = Path(__file__).resolve().parent
SERVER_DIR = CLIENT_DIR.parent / "mcp-server"


def _is_configured(value: str | None) -> bool:
    """Return True only for a non-empty, non-placeholder secret."""
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized not in {
        "your_key",
        "your_gemini_api_key",
        "your_google_api_key_here",
        "your_weatherapi_key",
    }


def check_environment():
    """Check whether both service keys are present in their .env files."""
    print("[CHECK] Environment configuration...")

    from dotenv import dotenv_values

    client_env = CLIENT_DIR / ".env"
    server_env = SERVER_DIR / ".env"
    ok = True

    if not client_env.exists():
        print(f"[ERROR] Missing {client_env}")
        ok = False
    elif not _is_configured(dotenv_values(client_env).get("GOOGLE_API_KEY")):
        print(f"[ERROR] Fill GOOGLE_API_KEY in {client_env}")
        print("   Get a key at: https://aistudio.google.com/apikey")
        ok = False
    else:
        print("[OK] GOOGLE_API_KEY configured")

    if not server_env.exists():
        print(f"[ERROR] Missing {server_env}")
        ok = False
    elif not _is_configured(dotenv_values(server_env).get("WEATHERAPI_KEY")):
        print(f"[ERROR] Fill WEATHERAPI_KEY in {server_env}")
        print("   Get a key at: https://www.weatherapi.com/")
        ok = False
    else:
        print("[OK] WEATHERAPI_KEY configured")

    return ok


def check_python_version():
    """Check the Python version targeted by this lab."""
    print("\n[CHECK] Python version...")
    version = sys.version_info
    if version < (3, 11):
        print(f"[ERROR] Python {version.major}.{version.minor} is too old; use Python 3.11+")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n[CHECK] Dependencies...")
    
    required_packages = [
        ("google.adk", "Google ADK"),
        ("google.genai", "Google Gen AI"),
        ("mcp", "MCP"),
        ("dotenv", "python-dotenv"),
        ("httpx", "httpx"),
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"[OK] {name}")
        except ImportError:
            print(f"[ERROR] {name} not installed")
            all_installed = False
    
    if not all_installed:
        print("\n   From the repository root, run:")
        print("   python -m pip install -e .\\04-lab\\mcp-server -e .\\04-lab\\mcp-client")
    
    return all_installed

def check_agent_structure():
    """Check if agent directory structure is correct"""
    print("\n[CHECK] Agent structure...")
    
    required_files = [
        "weather_agent/agent.py",
        "weather_agent/__init__.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        path = CLIENT_DIR / file_path
        if path.exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[ERROR] {file_path} not found")
            all_exist = False
    
    return all_exist

def check_mcp_server():
    """Connect through MCP, discover tools, and call the health tool."""
    print("\n[CHECK] MCP server connectivity...")

    # Cùng URL mà weather_agent/agent.py dùng (biến môi trường MCP_SERVER_URL)
    from dotenv import load_dotenv
    load_dotenv(CLIENT_DIR / ".env")
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

    try:
        tools, health, weather = asyncio.run(_probe_mcp_server(server_url))
        expected = {"get_current_weather", "get_forecast", "health_check"}
        missing = expected.difference(tools)
        if missing:
            print(f"[ERROR] MCP server is missing tools: {', '.join(sorted(missing))}")
            return False

        print(f"[OK] MCP protocol connected at {server_url}")
        print(f"[OK] Tools discovered: {', '.join(sorted(tools))}")
        print(f"[OK] health_check: {health}")
        if "unable to fetch" in weather.lower() or "not configured" in weather.lower():
            print(f"[ERROR] Live WeatherAPI call failed: {weather.strip()}")
            return False
        summary = weather.strip().splitlines()[0]
        print(f"[OK] Live WeatherAPI call: {summary}")
        return True

    except Exception as e:
        print(f"[ERROR] Cannot reach MCP server at {server_url}: {e}")
        print("   Start it in another PowerShell window:")
        print("   cd ..\\mcp-server; python .\\weather.py")
        return False


async def _probe_mcp_server(server_url: str) -> tuple[set[str], str, str]:
    """Perform an MCP handshake and call both health and live weather tools."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(server_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            health_result = await session.call_tool("health_check", {})
            weather_result = await session.call_tool(
                "get_current_weather", {"city": "Hanoi"}
            )
            names = {tool.name for tool in response.tools}
            health = health_result.content[0].text if health_result.content else "no response"
            weather = weather_result.content[0].text if weather_result.content else "no response"
            return names, health, weather

def check_agent_import():
    """Try to import the agent"""
    print("\n[CHECK] Agent import...")
    
    try:
        # Suppress warnings during import
        import warnings
        warnings.filterwarnings("ignore")
        
        from weather_agent import root_agent
        print(f"[OK] Agent imported successfully: {root_agent.name}")
        print(f"   Model: {root_agent.model}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to import agent: {e}")
        return False

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Weather Agent Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        check_environment(),
        check_python_version(),
        check_dependencies(),
        check_agent_structure(),
        check_mcp_server(),
        check_agent_import(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("[OK] All checks passed!")
        print("\nReady to start!")
        print("   Run: adk web")
        print("\nThen open: http://localhost:8000")
        return 0
    else:
        print("[ERROR] Some checks failed")
        print("\nFix the issues above and run this script again")
        return 1

if __name__ == "__main__":
    sys.exit(main())

