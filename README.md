# Garmin Connect MCP Server

A Model Context Protocol (MCP) server that provides Claude AI with access to your Garmin Connect data. Access your activities, health metrics, training data, and more through natural language conversations with Claude.

## Features

- **78+ Garmin Connect Tools** - Complete access to your fitness data
- **OAuth 2.0 Authentication** - Secure integration with Claude mobile & web
- **Dynamic Client Registration** - No manual OAuth setup required
- **PKCE Support** - Secure mobile app integration
- **Docker Support** - Easy deployment with Docker Compose
- **Kubernetes Ready** - Production deployment manifests included
- **Health Check Endpoint** - Container orchestration support

## Available Data

- **Activities**: Running, cycling, swimming, and all Garmin activities
- **Health Metrics**: Heart rate, sleep, stress, SpO2, blood pressure
- **Training**: Workouts, training status, race predictions
- **Body Metrics**: Weight, body composition, hydration
- **Gear**: Track equipment usage and maintenance
- **Challenges**: View and participate in Garmin challenges
- **Devices**: Manage your Garmin devices and settings

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Garmin Connect account
- For Claude integration: HTTPS domain with valid SSL certificate

### 1. Clone and Configure

```bash
git clone https://github.com/angryninja48/garmin_mcp.git
cd garmin_mcp

# Create environment file
nano .env
```

### 2. Set Environment Variables

```bash
# .env file
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password

# Generate secure token
MCP_BEARER_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# For local testing
MCP_BASE_URL=http://localhost:8000

# For production (Claude requires HTTPS)
# MCP_BASE_URL=https://garmin-mcp.your-domain.com
```

### 3. Start Server

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f garmin-mcp

# Check health
curl http://localhost:8000/health
```

### 4. Test Connection

```bash
# Test OAuth endpoints
python3 test_oauth.py

# Test with authentication
python3 test_auth.py http://localhost:8000/mcp YOUR_TOKEN_HERE
```

## Claude Integration

### For Claude Mobile (iOS/Android) or Web

1. **Deploy with HTTPS** (required by OAuth 2.0):
   ```bash
   # Update .env
   MCP_BASE_URL=https://garmin-mcp.your-domain.com
   
   # Deploy to production
   kubectl apply -f k8s/
   ```

2. **Add Custom Connector in Claude**:
   - Open Claude app or visit claude.ai
   - Go to Settings → Custom Connectors
   - Click "Add connector"
   - Enter: `https://garmin-mcp.your-domain.com/mcp`

3. **Authorize**:
   - Click "Connect"
   - Complete OAuth flow
   - Grant Claude access to your Garmin data

4. **Start Using**:
   ```
   "Show me my last 5 activities"
   "What was my heart rate during my last run?"
   "How many steps did I take yesterday?"
   ```

### OAuth Endpoints

Your server automatically provides:

- **Discovery**: `/.well-known/oauth-authorization-server`
- **Authorization**: `/authorize`
- **Token Exchange**: `/token`
- **Registration**: `/register` (Dynamic Client Registration)

Claude discovers and uses these automatically.

## Testing Locally with Claude

For local testing before production deployment, use ngrok or Cloudflare Tunnel to get HTTPS:

### Option 1: ngrok

```bash
# Start server
docker-compose up -d

# In another terminal
ngrok http 8000

# Update MCP_BASE_URL to ngrok URL
# Restart server
docker-compose restart

# Use ngrok URL in Claude
# https://abc123.ngrok.io/mcp
```

### Option 2: Cloudflare Tunnel

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:8000

# Use provided URL in Claude
```

## Production Deployment

### Kubernetes

1. **Create namespace and secrets**:
   ```bash
   kubectl create namespace garmin-mcp
   
   kubectl create secret generic garmin-creds \
     --from-literal=email='your-email@example.com' \
     --from-literal=password='your-password' \
     --from-literal=bearer_token='your-token' \
     -n garmin-mcp
   ```

2. **Deploy**:
   ```bash
   # Update k8s/deployment.yaml with your domain
   kubectl apply -f k8s/deployment.yaml
   ```

3. **Verify**:
   ```bash
   kubectl get pods -n garmin-mcp
   kubectl logs -f deployment/garmin-mcp -n garmin-mcp
   
   curl https://garmin-mcp.your-domain.com/health
   ```

## Architecture

```
┌─────────────────┐
│   Claude App    │ (Mobile/Web)
└────────┬────────┘
         │ HTTPS + OAuth 2.0
         │
┌────────▼────────────────────────┐
│   Garmin MCP Server             │
│   - FastMCP Framework           │
│   - OAuth Provider (DCR + PKCE) │
│   - 78+ Tools                   │
└────────┬────────────────────────┘
         │ Garmin API
         │
┌────────▼────────┐
│ Garmin Connect  │
└─────────────────┘
```

## Available Tools

<details>
<summary><b>Activity Management (15 tools)</b></summary>

- `list_activities` - List recent activities
- `get_activity_details` - Get detailed activity information
- `get_activity_splits` - Get lap/split data
- `get_activity_weather` - Get weather conditions during activity
- `get_activity_hr_zones` - Get heart rate zones
- `get_activity_gear` - Get gear used in activity
- And more...
</details>

<details>
<summary><b>Health & Wellness (20 tools)</b></summary>

- `get_heart_rate` - Get heart rate data
- `get_sleep_data` - Get sleep metrics
- `get_stress_data` - Get stress levels
- `get_steps` - Get daily step count
- `get_spo2` - Get blood oxygen levels
- `get_respiration` - Get respiration rate
- And more...
</details>

<details>
<summary><b>Training (12 tools)</b></summary>

- `get_training_status` - Get current training status
- `get_training_readiness` - Get readiness score
- `get_race_predictions` - Get predicted race times
- `get_vo2_max` - Get VO2 max estimates
- And more...
</details>

<details>
<summary><b>Body Metrics (8 tools)</b></summary>

- `get_weight` - Get weight data
- `get_body_composition` - Get body fat, muscle mass, etc.
- `add_weight` - Log weight entry
- `get_hydration` - Get hydration data
- And more...
</details>

<details>
<summary><b>Workouts (6 tools)</b></summary>

- `list_workouts` - List saved workouts
- `get_workout` - Get workout details
- `create_workout` - Create new workout
- `schedule_workout` - Schedule workout
- And more...
</details>

<details>
<summary><b>Devices & Gear (8 tools)</b></summary>

- `list_devices` - List Garmin devices
- `get_device_settings` - Get device settings
- `list_gear` - List registered gear
- `get_gear_stats` - Get gear usage statistics
- And more...
</details>

<details>
<summary><b>Challenges (5 tools)</b></summary>

- `get_available_challenges` - List available challenges
- `get_active_challenges` - List active challenges
- `get_badge_challenges` - List badge challenges
- And more...
</details>

<details>
<summary><b>Women's Health (4 tools)</b></summary>

- `get_menstrual_calendar` - Get cycle data
- `get_pregnancy_summary` - Get pregnancy information
- And more...
</details>

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GARMIN_EMAIL` | Yes | - | Your Garmin Connect email |
| `GARMIN_PASSWORD` | Yes | - | Your Garmin Connect password |
| `MCP_BEARER_TOKEN` | Yes | - | OAuth bearer token (generate with `secrets.token_urlsafe(32)`) |
| `MCP_BASE_URL` | Yes | `http://localhost:8000` | Public HTTPS URL for OAuth callbacks |
| `GARMINTOKENS` | No | `/data/.garminconnect` | Path to store Garmin auth tokens |

### OAuth Scopes

- `read` - Read access to Garmin data
- `write` - Write access (add activities, workouts, etc.)

Default: Both read and write enabled

## Security

### Authentication

- **OAuth 2.0** with Dynamic Client Registration (DCR)
- **PKCE** (Proof Key for Code Exchange) for mobile security
- **Refresh tokens** for long-lived sessions
- **Automatic token rotation**

### Best Practices

1. **Always use HTTPS in production** - Required by OAuth 2.0 spec
2. **Secure your bearer token** - Store in secrets manager
3. **Rotate tokens regularly** - Generate new tokens periodically
4. **Monitor access logs** - Watch for unauthorized usage
5. **Use Kubernetes secrets** - Don't commit credentials to git
6. **Enable network policies** - Restrict pod-to-pod communication

### Token Storage

- Garmin OAuth tokens stored in `/data/.garminconnect`
- MCP OAuth clients stored in memory (use Redis for production)
- Persistent volume recommended for token storage

## Troubleshooting

### Server Won't Start

```bash
# Check logs
docker-compose logs garmin-mcp

# Common issues:
# 1. Missing environment variables
# 2. Invalid Garmin credentials
# 3. Port 8000 already in use
```

### Garmin Authentication Failed

```bash
# Clear stored tokens and re-authenticate
docker-compose down -v
docker-compose up -d

# Check Garmin credentials in .env
```

### OAuth Flow Fails

```bash
# Verify HTTPS is enabled (required for OAuth)
curl https://your-domain.com/health

# Check OAuth metadata
curl https://your-domain.com/.well-known/oauth-authorization-server

# Verify MCP_BASE_URL matches your actual domain
```

### Claude Can't Connect

1. **Check HTTPS**: OAuth requires HTTPS (HTTP won't work)
2. **Verify DNS**: `nslookup your-domain.com`
3. **Check certificate**: `curl -v https://your-domain.com/health`
4. **Review logs**: `kubectl logs -f deployment/garmin-mcp`

### Tools Not Appearing

```bash
# Check Garmin authentication status
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "server": "Garmin Connect MCP", "garmin_connected": true}

# If garmin_connected is false, check credentials
```

## Development

### Running Tests

```bash
# Test OAuth endpoints
python3 test_oauth.py

# Test authentication
python3 test_auth.py http://localhost:8000/mcp YOUR_TOKEN
```

### Adding New Tools

1. Add tool implementation to appropriate module in `modules/`
2. Register tool in module's `register_tools()` function
3. Restart server
4. Test with `test_auth.py`

### Building Docker Image

```bash
# Build
docker build -t garmin-mcp:latest .

# Push to registry
docker tag garmin-mcp:latest your-registry/garmin-mcp:latest
docker push your-registry/garmin-mcp:latest
```

## API Reference

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "server": "Garmin Connect MCP",
  "garmin_connected": true
}
```

### OAuth Discovery

```bash
GET /.well-known/oauth-authorization-server
```

Returns OAuth 2.0 server metadata with all endpoint URLs.

### MCP Endpoint

```bash
POST /mcp
Content-Type: application/json
Authorization: Bearer <token>
```

Standard MCP protocol requests.

## License

MIT License - See [LICENSE](LICENSE) file

## Credits

- **FastMCP** - [gofastmcp.com](https://gofastmcp.com)
- **garminconnect** - Python Garmin Connect API
- **Model Context Protocol** - [modelcontextprotocol.io](https://modelcontextprotocol.io)

## Support

- **Issues**: [GitHub Issues](https://github.com/angryninja48/garmin_mcp/issues)
- **FastMCP Docs**: [gofastmcp.com/servers/auth](https://gofastmcp.com/servers/auth)
- **Claude MCP Docs**: [support.claude.com](https://support.claude.com/en/articles/11175166)
- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

## Changelog

### v1.0.0
- Initial release
- OAuth 2.0 with Dynamic Client Registration
- 78+ Garmin Connect tools
- Docker and Kubernetes support
- Claude mobile/web integration