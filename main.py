import os
import boto3
import logging
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. THE SECURITY BOUNCER (Auth Middleware) ---
class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        expected_token = os.getenv("API_SECRET_TOKEN")
        client_token = request.headers.get("X-API-Key")
        
        if not expected_token or client_token != expected_token:
            logger.warning("Blocked unauthorized connection attempt!")
            return PlainTextResponse("Unauthorized", status_code=401)
            
        return await call_next(request)

# --- 2. MCP SERVER & AWS TOOLS ---
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

# --- 3. CREATE THE APP ---
# We let FastMCP generate the ASGI app for us, then add our Bouncer!
app = mcp.get_asgi_app()
app.add_middleware(TokenAuthMiddleware)
