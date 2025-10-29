"""
Python script that fetches pending orders from a GraphQL endpoint
and logs reminders. Intended to run daily via cron.
"""

import logging
from datetime import datetime, timedelta, timezone
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# ============================================
# Configure logging (checker expects this path)
# ============================================
logging.basicConfig(
    filename="/tmp/order_reminders_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ============================================
# GraphQL endpoint setup
# ============================================
transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql/",
    verify=True,
    retries=3,
)
client = Client(transport=transport, fetch_schema_from_transport=True)

# ============================================
# GraphQL query — fetch all orders
# ============================================
query = gql("""
query GetAllOrders {
  orders {
    id
    customer {
      email
      name
    }
    orderDate
  }
}
""")

# ============================================
# Execute query and log results
# ============================================
try:
    result = client.execute(query)
    all_orders = result.get("orders", [])

    # Define pending orders (last 7 days) — all in UTC
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    pending_orders = [
        o for o in all_orders
        if datetime.fromisoformat(o['orderDate']).astimezone(timezone.utc) >= seven_days_ago
    ]

    logging.info(f"Found {len(pending_orders)} pending orders.")

    for order in pending_orders:
        logging.info(
            f"Order ID: {order['id']}, "
            f"Customer: {order['customer']['name']} <{order['customer']['email']}>, "
            f"Order Date: {order.get('orderDate', 'N/A')}"
        )

    print("Order reminders processed!")

except Exception as e:
    import traceback
    logging.error(f"Error fetching pending orders: {e}")
    logging.error(traceback.format_exc())
    print(f"Error occurred while processing order reminders: {e}")
