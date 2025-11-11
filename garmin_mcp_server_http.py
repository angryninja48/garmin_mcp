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

# Warn if credentials are not set
if not email or not password:
    print("⚠️  WARNING: GARMIN_EMAIL and/or GARMIN_PASSWORD environment variables are not set!")
    print("⚠️  Using default/empty credentials - authentication will likely fail.")
    print("⚠️  Please set these environment variables in your Kubernetes deployment.")
else:
    print(f"✓ Using Garmin credentials for: {email}")


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

# Create OAuth provider using GitHub authentication
# This ensures only authorized GitHub users can access the server
auth_provider = None
github_client_id = os.environ.get("GITHUB_CLIENT_ID", "")
github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
allowed_github_username = os.environ.get("ALLOWED_GITHUB_USERNAME", "angryninja48")

if github_client_id and github_client_secret:
    from fastmcp.server.auth.providers.github import GitHubProvider
    
    # Create GitHub OAuth provider
    # Users must authenticate with GitHub to access the server
    auth_provider = GitHubProvider(
        client_id=github_client_id,
        client_secret=github_client_secret,
        base_url=os.environ.get("MCP_BASE_URL", "http://localhost:8000"),
    )
    
    print(f"✓ GitHub OAuth provider configured")
    print(f"  Base URL: {os.environ.get('MCP_BASE_URL', 'http://localhost:8000')}")
    print(f"  Callback URL: {os.environ.get('MCP_BASE_URL', 'http://localhost:8000')}/auth/callback")
    print(f"  Allowed user: {allowed_github_username}")
    print()
    print("=" * 60)
    print("Claude Custom Connector Configuration:")
    print("=" * 60)
    print(f"Server URL: {os.environ.get('MCP_BASE_URL', 'http://localhost:8000')}/mcp")
    print(f"")
    print(f"Authentication: GitHub OAuth")
    print(f"Only GitHub user '{allowed_github_username}' can access this server.")
    print("=" * 60)
else:
    print("⚠️  WARNING: GitHub OAuth not configured!")
    print("⚠️  Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables")
    print("⚠️  Server will run WITHOUT authentication!")
    print("⚠️  Create OAuth App at: https://github.com/settings/developers")

# Create the MCP server with OAuth authentication
mcp = FastMCP("Garmin Connect v1.0", auth=auth_provider)

# Configure host and port via settings (as per GitHub issue #873 workaround)
mcp.settings.host = "0.0.0.0"
mcp.settings.port = 8000

# Helper function to check if user is authorized
def check_github_auth():
    """Check if the authenticated GitHub user is allowed to access the server."""
    if not auth_provider:
        # No auth configured - allow access (for local development)
        return None
    
    try:
        from fastmcp.server.dependencies import get_access_token
        token = get_access_token()
        github_username = token.claims.get("login", "")
        
        if github_username != allowed_github_username:
            return f"❌ Access denied: GitHub user '{github_username}' is not authorized. Only '{allowed_github_username}' can access this server."
        
        return None  # Authorized
    except Exception as e:
        return f"❌ Authentication error: {str(e)}"

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
    # Check GitHub authorization
    auth_error = check_github_auth()
    if auth_error:
        return auth_error
    
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
