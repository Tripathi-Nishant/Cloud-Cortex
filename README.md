# ☁️ Cloud Cortex: AWS Cost Optimization MCP Server

Cloud Cortex is an enterprise-grade Model Context Protocol (MCP) server that empowers AI assistants (like Claude) to securely interact with your AWS infrastructure. It acts as an autonomous DevOps agent, retrieving live AWS billing data, analyzing expenditures, and providing actionable cost-saving recommendations directly within your AI chat interface.

## ✨ Features

- **Live AWS Cost Analysis:** Integrates directly with AWS Cost Explorer via `boto3`.
- **Reserved Instance Calculator:** Instantly calculates potential savings for RI migrations.
- **Enterprise Security:** Secured via token-based HTTP middleware (`X-API-Key`) to ensure only authorized clients can access your cloud data.
- **Server-Sent Events (SSE):** Built on `FastMCP` and `Starlette` for stable, long-running AI streaming connections.
- **Cloud-Ready:** Designed to be deployed instantly on platforms like Render, Railway, or Heroku.

---

## 🏗 Architecture

1. **Client (Claude Desktop):** Sends a secure request with an API Token to the CloudVantage Server.
2. **Server (Render.com):** Validates the token, processes the MCP request, and calls the AWS API.
3. **Cloud (AWS):** Returns cost data (last 30 days) to the server.
4. **Response:** Claude reads the JSON data and presents a human-readable financial analysis.

---

## 🚀 Deployment Guide

### Phase 1: AWS IAM Setup (Security First)
For maximum security, **do not use your AWS Root Account keys.**
1. Log into the AWS Console.
2. Go to **IAM > Users** and create a new user (e.g., `cloudvantage-mcp`).
3. Attach the `AWSBillingReadOnlyAccess` policy (or a custom policy scoped only to `ce:GetCostAndUsage`).
4. Generate an **Access Key** and **Secret Access Key** for this user. Save these for Phase 3.

### Phase 2: GitHub Setup
1. Create a private repository on GitHub.
2. Commit the following files to your repository:
   - `main.py` (The FastMCP server)
   - `requirements.txt` (Dependencies)
   - `.gitignore`

### Phase 3: Cloud Hosting (Render.com)
1. Create an account on [Render.com](https://render.com) and connect your GitHub.
2. Create a new **Web Service** and select your repository.
3. Configure the build settings:
   - **Language:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add the following **Environment Variables** securely in the Render dashboard:
   - `API_SECRET_TOKEN` (Create a strong custom password, e.g., `my-secure-token-123`)
   - `AWS_ACCESS_KEY_ID` (From Phase 1)
   - `AWS_SECRET_ACCESS_KEY` (From Phase 1)
   - `AWS_DEFAULT_REGION` (e.g., `us-east-1`)
5. Deploy the service. Once live, copy your public URL (e.g., `https://cloudvantage.onrender.com`).

---

## 💻 Client Configuration (Claude Desktop)

To connect Claude Desktop to your newly deployed server, update your local configuration file. 

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following configuration, ensuring you replace `YOUR_RENDER_URL` and `YOUR_SECRET_TOKEN`:

```json
{
  "mcpServers": {
    "cloudvantage": {
      "command": "python",
      "args": [
        "-c",
        "import asyncio, os\nos.environ['HTTPX_EXTRA_HEADERS'] = '{\"X-API-Key\": \"YOUR_SECRET_TOKEN\"}'\nfrom mcp.client.sse import sse_client\nfrom mcp.client.stdio import stdio_client\nasync def run():\n    async with sse_client('https://YOUR_RENDER_URL.onrender.com/sse') as sse:\n        async with stdio_client(sse) as stdio:\n            await asyncio.Future()\nasyncio.run(run())"
      ]
    }
  }
}
```

*Note: Requires Python to be installed on the client machine to run the bridge script.*

---

## 🛠️ Usage Examples

Once connected, simply ask Claude questions like:
- *"Analyze my AWS costs using the Cloud Cortex tool."*
- *"Where am I spending the most money on AWS over the last 30 days?"*
- *"Use the RI calculator to tell me how much I'd save if I switch my $500/mo EC2 fleet to Reserved Instances."*

---

## 🔒 Security Best Practices
- Keep your GitHub repository **Private**.
- Never hardcode keys in `main.py`. Always use environment variables.
- Rotate your `API_SECRET_TOKEN` and AWS IAM keys periodically.
