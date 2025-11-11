# Tests

Test suite for Garmin MCP Server.

## Important: Testing with GitHub OAuth

⚠️ **These tests DO NOT work with GitHub OAuth in production** because:
- Tests use bearer token authentication internally
- GitHub OAuth requires browser-based authorization flow
- No way to programmatically complete GitHub login in tests

**For production testing**, see "Production Testing" section below.

## Available Tests

### test_auth.py

Tests bearer token authentication (for local development only).

**Usage:**
```bash
python3 tests/test_auth.py http://localhost:8000/mcp YOUR_BEARER_TOKEN
```

**What it tests:**
- Bearer token validation
- MCP protocol communication
- Tool availability
- Basic functionality

**When to use:**
- Local development without GitHub OAuth
- Testing server functionality
- Debugging tool implementations

**Not suitable for:**
- Production testing (GitHub OAuth required)
- End-to-end authorization testing
- Username validation testing

## Production Testing with GitHub OAuth

Since automated tests can't complete GitHub's web-based login, use manual testing:

### Testing OAuth Flow

1. **Deploy server** with GitHub OAuth configuration
2. **Open Claude.ai** → Settings → Custom Connectors
3. **Add connector** with your server URL: `https://garmin-mcp.your-domain.com/mcp`
4. **Click "Connect"** - you'll be redirected to GitHub
5. **Log in** with your GitHub account
6. **Authorize** the application
7. **Verify redirect** back to Claude

### Testing Username Validation

To verify that only your username can access:

1. **Test with your account**: Should work ✅
   - Complete OAuth flow as your GitHub user
   - Try calling tools in Claude
   - Should work normally

2. **Test with another account**: Should be blocked ❌
   - Have someone else try to connect (or use a different GitHub account)
   - They can complete OAuth flow
   - But all tool calls return: "Access denied: GitHub user 'X' is not authorized"

### Testing Tool Functionality

In Claude, try these commands:

```
"Show me my last 5 activities"
"What was my heart rate during my last run?"
"How many steps did I take yesterday?"
"What's my current training status?"
```

All should return data if authenticated as the allowed GitHub user.

### Checking Logs

Monitor server logs to see authentication flow:

```bash
# Kubernetes
kubectl logs -f deployment/garmin-mcp -n garmin-mcp

# Docker Compose
docker-compose logs -f garmin-mcp
```

Look for:
```
✓ GitHub OAuth provider configured
  Allowed user: your-github-username
```

When someone connects, you'll see:
```
INFO: GET /authorize?... HTTP/1.1" 302 Found
INFO: POST /token HTTP/1.1" 200 OK
INFO: POST /mcp HTTP/1.1" 200 OK
```

### Testing Unauthorized Access

If someone unauthorized tries to access:

```bash
# In logs, you'll see their username in token claims
# Tools will return: "Access denied: GitHub user 'unauthorized-user' is not authorized"
```

This confirms your username validation is working correctly.

## Development Mode (Local Testing)

For local development without GitHub OAuth:

1. **Don't set GitHub environment variables**:
   ```bash
   # .env - for development only
   GARMIN_EMAIL=your-email@example.com
   GARMIN_PASSWORD=your-password
   MCP_BEARER_TOKEN=your-token
   # GITHUB_CLIENT_ID=  # Leave commented out
   # GITHUB_CLIENT_SECRET=  # Leave commented out
   ```

2. **Server will run without GitHub OAuth**:
   ```
   ⚠️  WARNING: GitHub OAuth not configured!
   ⚠️  Server will run WITHOUT authentication!
   ```

3. **Now tests will work**:
   ```bash
   python3 tests/test_auth.py http://localhost:8000/mcp YOUR_BEARER_TOKEN
   ```

**⚠️ Never deploy to production without GitHub OAuth** - it would be unprotected!

## Summary

| Test | Works Locally | Works in Production (GitHub OAuth) |
|------|---------------|-----------------------------------|
| `test_auth.py` | ✅ Yes (bearer token) | ❌ No (requires GitHub OAuth) |
| `test_oauth.py` | ✅ Yes (with InMemoryOAuth) | ❌ No (incompatible with GitHub) |
| Manual testing via Claude | ❌ No (requires HTTPS) | ✅ Yes (proper testing method) |

**Best practice:**
- Use `test_auth.py` for local development
- Use Claude.ai for production testing
- Monitor logs to verify authentication flow
