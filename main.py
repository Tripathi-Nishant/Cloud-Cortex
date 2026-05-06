import os
import boto3
import logging
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

# --- SETUP LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. MCP SERVER & AWS TOOLS ---
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

# --- 2. RUN THE SERVER ---
# This runs FastMCP directly using its built-in SSE server on port 10000
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    mcp.settings.port = port
    mcp.settings.host = "0.0.0.0"
    mcp.run(transport="sse")
