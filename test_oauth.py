#!/usr/bin/env python3
"""
Test OAuth flow with Garmin MCP Server
"""
import asyncio
import httpx
from fastmcp import Client

SERVER_URL = "http://localhost:8000/mcp"

async def test_oauth_discovery():
    """Test OAuth metadata discovery"""
    print("\n" + "=" * 60)
    print("Testing OAuth Discovery")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test discovery endpoint
        response = await client.get("http://localhost:8000/.well-known/oauth-authorization-server")
        metadata = response.json()
        
        print(f"\n✅ OAuth Discovery Working")
        print(f"   Issuer: {metadata['issuer']}")
        print(f"   Authorization: {metadata['authorization_endpoint']}")
        print(f"   Token: {metadata['token_endpoint']}")
        print(f"   Registration: {metadata['registration_endpoint']}")
        print(f"   Supported Scopes: {', '.join(metadata['scopes_supported'])}")
        print(f"   PKCE: {', '.join(metadata['code_challenge_methods_supported'])}")
        
        return metadata

async def test_client_registration():
    """Test dynamic client registration"""
    print("\n" + "=" * 60)
    print("Testing Dynamic Client Registration")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Register a client
        registration_data = {
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:12345/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": "read write"
        }
        
        response = await client.post(
            "http://localhost:8000/register",
            json=registration_data
        )
        
        if response.status_code == 201:
            client_info = response.json()
            print(f"\n✅ Client Registration Working")
            print(f"   Client ID: {client_info['client_id']}")
            print(f"   Client Secret: {client_info['client_secret'][:10]}...")
            print(f"   Redirect URIs: {client_info['redirect_uris']}")
            return client_info
        else:
            print(f"\n❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

async def test_unauthorized_access():
    """Test that unauthorized access is blocked"""
    print("\n" + "=" * 60)
    print("Testing Unauthorized Access Protection")
    print("=" * 60)
    
    try:
        async with Client(SERVER_URL) as client:
            tools = await client.list_tools()
            print(f"\n❌ SECURITY ISSUE: Server accepted unauthenticated request")
            print(f"   Tools accessible: {len(tools)}")
            return False
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "invalid_token" in error_msg:
            print(f"\n✅ Unauthorized Access Blocked")
            print(f"   Error: {error_msg[:100]}")
            return True
        else:
            print(f"\n⚠️  Unexpected error: {error_msg[:100]}")
            return False

async def test_mcp_endpoint():
    """Test MCP endpoint is available"""
    print("\n" + "=" * 60)
    print("Testing MCP Endpoint")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SERVER_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
        )
        
        if response.status_code == 401:
            print(f"\n✅ MCP Endpoint Protected by OAuth")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"\n⚠️  Unexpected status: {response.status_code}")
            return False

async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("GARMIN MCP OAUTH TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: OAuth Discovery
        metadata = await test_oauth_discovery()
        
        # Test 2: Dynamic Client Registration
        client_info = await test_client_registration()
        
        # Test 3: Unauthorized Access
        auth_protected = await test_unauthorized_access()
        
        # Test 4: MCP Endpoint
        mcp_protected = await test_mcp_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"✅ OAuth Discovery: {'PASS' if metadata else 'FAIL'}")
        print(f"✅ Client Registration: {'PASS' if client_info else 'FAIL'}")
        print(f"✅ Auth Protection: {'PASS' if auth_protected else 'FAIL'}")
        print(f"✅ MCP Protection: {'PASS' if mcp_protected else 'FAIL'}")
        
        all_passed = all([metadata, client_info, auth_protected, mcp_protected])
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nYour server is ready for Claude integration:")
            print("  1. Deploy with HTTPS (required for OAuth)")
            print("  2. Update MCP_BASE_URL to your HTTPS domain")
            print("  3. Add custom connector in Claude")
            print(f"  4. Use URL: https://your-domain.com/mcp")
        else:
            print("\n⚠️  SOME TESTS FAILED")
            print("   Check server logs for details")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
