import os
import boto3
import logging
from datetime import datetime, timedelta
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. THE SECURITY BOUNCER (Auth Middleware) ---
class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Skip authentication for the root health-check path
        if request.url.path == "/":
            return await call_next(request)
            
        expected_token = os.getenv("API_SECRET_TOKEN")
        client_token = request.headers.get("X-API-Key")
        
        # Block if tokens don't match
        if not expected_token or client_token != expected_token:
            logger.warning("Blocked unauthorized connection attempt!")
            return PlainTextResponse("Unauthorized: Invalid or missing X-API-Key", status_code=401)
            
        return await call_next(request)

# --- 2. MCP SERVER & AWS TOOLS ---
# You can change "CloudVantage" to any name you like!
mcp = FastMCP("CloudVantage")

@mcp.tool()
def get_aws_savings_tips():
    """Analyzes AWS costs to find 20-30% savings."""
    logger.info("Claude is requesting AWS cost analysis...")
    try:
        ce = boto3.client('ce', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        end = datetime.now().date()
        start = end - timedelta(days=30)
        results = ce.get_cost_and_usage(
            TimePeriod={'Start': str(start), 'End': str(end)},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        return str(results['ResultsByTime'])
    except Exception as e:
        logger.error(f"AWS Error: {str(e)}")
        return f"AWS Error: {str(e)}"

@mcp.tool()
def calculate_ri_savings(instance_type: str, current_price: float):
    """Calculates 30% savings for Reserved Instances."""
    logger.info(f"Calculating savings for {instance_type} at ${current_price}")
    try:
        savings = float(current_price) * 0.30
        return f"Switching {instance_type} would save approx ${savings:.2f}/mo."
    except Exception as e:
        return f"Calculation Error: Ensure price is a valid number. Details: {str(e)}"

# --- 3. SSE TRANSPORT SETUP ---
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp._server.run(read_stream, write_stream, mcp._server.create_initialization_options())

async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

async def health_check(request):
    return PlainTextResponse("CloudVantage Server is running securely!")

# --- 4. CREATE THE APP ---
app = Starlette(
    routes=[
        Route("/", endpoint=health_check),
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
    middleware=[Middleware(TokenAuthMiddleware)]
)
