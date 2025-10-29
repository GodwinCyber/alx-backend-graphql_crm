"""
Cron job that logs a heartbeat message every 5 minutes
to confirm the CRM application's health.
Optionally queries the GraphQL 'hello' field to ensure the endpoint is active
"""

import logging
from datetime import datetime
import requests


# =================================================
# Configure logging to /tmp/crm_heartbeat.log.txt
# =================================================
logging.basicConfig(
    filename="/tmp/crm_heartbeat_log.txt",
    level=logging.INFO,
    format="%(message)s"
)

def log_crm_heartbeat():
    """Logs a heartbeat message and optionally pings GraphQL endpoints."""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Default status
    status = "CRM is alive"

    # Optional: Verify GraphQL helo field
    try:
        response = requests.post(
            "http://localhost:8000/graphql/",
            json={"query": "{ hello }"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("hello"):
                status = f"CRM is alive - GraphQL OK ({data['data']['hello']})"
            else:
                status = "CRM is alive - GraphQL response missing 'hello'"
        else:
            status = f"CRM is alive - GraphQL returned HTTP {response.status_code}"
    except Exception as e:
        status = f"CRM is alive - GraphQL check failed ({e})"

    # Log message
    log_message = f"{timestamp} {status}"
    logging.info(log_message)

# The usage
# # Apply cron jobs
# python manage.py crontab add

# # Confirm they’re registered
# python manage.py crontab show

# # To remove them later
# python manage.py crontab remove

