#!/usr/bin/env python3
"""
Test authentication setup
"""
import asyncio
from fastmcp import Client
import sys

async def test_auth(url: str, token: str = None):
    """Test server authentication"""
    print(f"\nTesting Garmin MCP Authentication")
    print(f"Server: {url}")
    print("=" * 60)
    
    # Test 1: Without authentication
    print("\n1. Testing without authentication...")
    try:
        async with Client(url) as client:
            tools = await client.list_tools()
            print(f"❌ SECURITY ISSUE: Server accessible without auth!")
            print(f"   Found {len(tools)} tools without providing credentials")
            print(f"\n   ⚠️  This means anyone can access your Garmin data!")
            print(f"   ⚠️  Set MCP_BEARER_TOKEN environment variable")
            return False
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "Authentication" in error_msg:
            print(f"✓ Correctly rejected unauthorized access")
        else:
            print(f"✗ Unexpected error: {error_msg[:100]}")
            return False
    
    # Test 2: With authentication
    if token:
        print("\n2. Testing with authentication...")
        try:
            async with Client(url, auth=token) as client:
                print("   Connecting...")
                tools = await client.list_tools()
                print(f"   ✓ Auth successful: {len(tools)} tools available")
                
                # Test a tool call
                print("\n3. Testing tool execution...")
                result = await client.call_tool("list_activities", {"limit": 2})
                print(f"   ✓ Tool execution works")
                print(f"   ✓ Data preview: {result.data[:100]}...")
                
                return True
        except Exception as e:
            print(f"   ❌ Auth failed: {e}")
            return False
    else:
        print("\n2. Skipping authenticated test (no token provided)")
        print("   Usage: python test_auth.py <url> <token>")
        return True
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python test_auth.py <url> [token]")
        print("\nExamples:")
        print("  python test_auth.py http://localhost:8000/mcp")
        print("  python test_auth.py http://localhost:8000/mcp your-token-here")
        print("  python test_auth.py https://garmin-mcp.example.com/mcp your-token-here")
        sys.exit(1)
    
    url = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = asyncio.run(test_auth(url, token))
    
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
        if not token:
            print("\n  Run with a token to test full authentication:")
            print(f"  python test_auth.py {url} <your-token>")
    else:
        print("❌ Some tests failed!")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
