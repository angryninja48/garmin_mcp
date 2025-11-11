"""
HTTP-based MCP Server for Garmin Connect Data (for Kubernetes deployment)
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests

from fastmcp import FastMCP

# Try to load .env file if it exists (for local development)
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print("No .env file found, using environment variables from container/system")

from garth.exc import GarthHTTPError
from garminconnect import Garmin, GarminConnectAuthenticationError

# Import all modules
from modules import (
    activity_management,
    health_wellness,
    user_profile,
    devices,
    gear_management,
    weight_management,
    challenges,
    training,
    workouts,
    data_management,
    womens_health,
)

# Get credentials from environment with defaults
email = os.environ.get("GARMIN_EMAIL", "")
password = os.environ.get("GARMIN_PASSWORD", "")
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"

# Get MCP authentication token
bearer_token = os.environ.get("MCP_BEARER_TOKEN", "")

# Warn if credentials are not set
if not email or not password:
    print("⚠️  WARNING: GARMIN_EMAIL and/or GARMIN_PASSWORD environment variables are not set!")
    print("⚠️  Using default/empty credentials - authentication will likely fail.")
    print("⚠️  Please set these environment variables in your Kubernetes deployment.")
else:
    print(f"✓ Using Garmin credentials for: {email}")

# Warn if authentication is not set
if not bearer_token:
    print("⚠️  WARNING: MCP_BEARER_TOKEN environment variable is not set!")
    print("⚠️  Server will be accessible without authentication - NOT RECOMMENDED for production!")
    print("⚠️  Generate a token: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"")
else:
    print(f"✓ MCP authentication enabled (token: {bearer_token[:8]}...)")


def init_api(email, password):
    """Initialize Garmin API with your credentials."""
    if not email or not password:
        print("⚠️  Cannot initialize Garmin API: missing credentials")
        print("⚠️  Server will start but Garmin API calls will fail")
        return None
    
    try:
        print(f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...")
        garmin = Garmin()
        garmin.login(tokenstore)
        print("✓ Successfully logged in using existing tokens")
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print("Login tokens not present, login with your Garmin Connect credentials to generate them.")
        print(f"They will be stored in '{tokenstore}' for future use.")
        try:
            garmin = Garmin(email=email, password=password, is_cn=False)
            # Temporarily unset GARMINTOKENS to force credential-based authentication
            saved_token_env = os.environ.get("GARMINTOKENS")
            if saved_token_env:
                del os.environ["GARMINTOKENS"]
            try:
                garmin.login()  # This will now use credentials since GARMINTOKENS is unset
            finally:
                # Restore the environment variable
                if saved_token_env:
                    os.environ["GARMINTOKENS"] = saved_token_env
            
            # Save the tokens after successful authentication
            garmin.garth.dump(tokenstore)
            print(f"✓ OAuth tokens stored in '{tokenstore}' directory for future use.")
            
            # Also save base64 encoded tokens
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(f"✓ OAuth tokens encoded as base64 string and saved to '{dir_path}' file.")
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            print(f"❌ Error during authentication: {err}")
            print("⚠️  Server will start but Garmin API calls will fail")
            return None
    return garmin


# Initialize Garmin client at module level
print("=" * 60)
print("Initializing Garmin Connect client...")
print("=" * 60)
garmin_client = init_api(email, password)

if not garmin_client:
    print("=" * 60)
    print("⚠️  WARNING: Garmin Connect client not initialized")
    print("⚠️  Server will start in limited mode")
    print("⚠️  API calls will return error messages")
    print("=" * 60)
else:
    print("=" * 60)
    print("✓ Garmin Connect client initialized successfully")
    print("=" * 60)

# Configure all modules with the Garmin client (even if None)
activity_management.configure(garmin_client)
health_wellness.configure(garmin_client)
user_profile.configure(garmin_client)
devices.configure(garmin_client)
gear_management.configure(garmin_client)
weight_management.configure(garmin_client)
challenges.configure(garmin_client)
training.configure(garmin_client)
workouts.configure(garmin_client)
data_management.configure(garmin_client)
womens_health.configure(garmin_client)

# Create OAuth provider for Claude mobile/web integration
# TEMPORARY: Disable OAuth to test Claude connectivity
# TODO: Re-enable once basic connection is working
auth_provider = None
# if bearer_token:
#     from fastmcp.server.auth.providers.in_memory import InMemoryOAuthProvider
#     from fastmcp.server.auth.auth import ClientRegistrationOptions
#     
#     auth_provider = InMemoryOAuthProvider(
#         base_url=os.environ.get("MCP_BASE_URL", "http://localhost:8000"),
#         client_registration_options=ClientRegistrationOptions(
#             enabled=True,
#             valid_scopes=["read", "write"],
#             default_scopes=["read", "write"],
#         ),
#     )
#     
#     print(f"✓ OAuth provider configured with Dynamic Client Registration")

print("⚠️  RUNNING IN AUTHLESS MODE FOR TESTING")
print("=" * 60)
print(f"Server URL: {os.environ.get('MCP_BASE_URL', 'http://localhost:8000')}/mcp")
print("⚠️  WARNING: No authentication - anyone can access!")
print("=" * 60)

# Create the MCP server with OAuth authentication
mcp = FastMCP("Garmin Connect v1.0", auth=auth_provider)

# Configure host and port via settings (as per GitHub issue #873 workaround)
mcp.settings.host = "0.0.0.0"
mcp.settings.port = 8000

# Register tools from all modules
mcp = activity_management.register_tools(mcp)
mcp = health_wellness.register_tools(mcp)
mcp = user_profile.register_tools(mcp)
mcp = devices.register_tools(mcp)
mcp = gear_management.register_tools(mcp)
mcp = weight_management.register_tools(mcp)
mcp = challenges.register_tools(mcp)
mcp = training.register_tools(mcp)
mcp = workouts.register_tools(mcp)
mcp = data_management.register_tools(mcp)
mcp = womens_health.register_tools(mcp)


# Add activity listing tool directly to the server
@mcp.tool()
async def list_activities(limit: int = 5) -> str:
    """List recent Garmin activities"""
    if not garmin_client:
        return "❌ Garmin API not available: Missing GARMIN_EMAIL and/or GARMIN_PASSWORD environment variables"
    
    try:
        activities = garmin_client.get_activities(0, limit)
        if not activities:
            return "No activities found."

        result = f"Last {len(activities)} activities:\n\n"
        for idx, activity in enumerate(activities, 1):
            result += f"--- Activity {idx} ---\n"
            result += f"Activity: {activity.get('activityName', 'Unknown')}\n"
            result += f"Type: {activity.get('activityType', {}).get('typeKey', 'Unknown')}\n"
            result += f"Date: {activity.get('startTimeLocal', 'Unknown')}\n"
            result += f"ID: {activity.get('activityId', 'Unknown')}\n\n"
        return result
    except Exception as e:
        return f"Error retrieving activities: {str(e)}"


# Add a custom health check endpoint for Docker/Kubernetes
@mcp.custom_route(path="/health", methods=["GET"])
async def health_check(request):
    """Simple health check endpoint for container orchestration"""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "healthy",
        "server": "Garmin Connect MCP",
        "garmin_connected": garmin_client is not None
    })


# Run the server using FastMCP's built-in HTTP support
if __name__ == "__main__":
    # Note: host and port are configured via mcp.settings above
    mcp.run(transport="http")
