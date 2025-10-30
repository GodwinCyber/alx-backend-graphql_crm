"""
Cron job that logs a heartbeat message every 5 minutes
to confirm the CRM application's health.
Optionally queries the GraphQL 'hello' field to ensure the endpoint is alive.
"""

import logging
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# ============================================
# Configure logging to /tmp/crm_heartbeat_log.txt
# ============================================
logging.basicConfig(
    filename="/tmp/crm_heartbeat_log.txt",
    level=logging.INFO,
    format="%(message)s"
)

def log_crm_heartbeat():
    """Logs a heartbeat message and queries the GraphQL 'hello' field."""
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    status = "CRM is alive"

    # ============================================
    # GraphQL endpoint setup
    # ============================================
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",  # trailing slash required
        verify=True,
        retries=2,
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    # GraphQL query to check 'hello' field
    query = gql("""
    query {
        hello
    }
    """)

    try:
        result = client.execute(query)
        hello_value = result.get("hello")
        if hello_value:
            status = f"CRM is alive - GraphQL OK ({hello_value})"
        else:
            status = "CRM is alive - GraphQL response missing 'hello'"
    except Exception as e:
        status = f"CRM is alive - GraphQL check failed ({e})"

    # Log message
    log_message = f"{timestamp} {status}"
    logging.info(log_message)


# ============================================
# LOW STOCKER LOGGER
# ============================================
logging.basicConfig(
    filename="/tmp/low_stock_updates_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def update_low_stock():
    '''Runs the graphql mutations to restock low-stock product and logs updates'''
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",
        verify=True,
        retries=3,
    )

    mutation = gql("""
    mutation UpdateLowStockProducts($restockAmount: Int!) {
        updateLowStockProducts(restockAmount: $restockAmount) {
            updatedProducts {
                id
                name
                stock
            }
            message
        }
    }
    """)

    try:
        params = {"restock-amount": 10}
        result = Client.execute(mutation, variable_values=params)
        updated = result.get("updateLowStockProducts", {}).get("updatedProducts", [])
        message = result.get("updateLowStockProducts", {}).get("message", [])

        if updated:
            for product in updated:
                logging.info(f"Product '{product['name']}' updated to stock {product['stock']}")
        logging.info(f"Low stock update: {message}")

        print(f"Low stock products updated: {len(updated)}")

    except Exception as e:
        logging.error(f"Error updating low-stock products: {e}")
        print(f"Error occured while updating low-stock products: {e}")


# The usage
# check for erro
# python manage.py check --settings=crm.settings

# # Apply cron jobs
# python manage.py crontab add --settings=crm.settings

# # Confirm they’re registered
# python manage.py crontab show --settings=crm.settings

# # To remove them later
# python manage.py crontab remove --settings=crm.settings

