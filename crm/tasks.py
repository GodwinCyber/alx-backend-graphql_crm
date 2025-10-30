"""
Celery task that generate a weekly CRM report.
It fetches data frrom the GraphQL endpoint and logs summary statistics.
"""

import logging
from datetime import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure logging
logging.basicConfig(
    filename="/tmp/crm_report_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levename)s - %(message)s"
)

@shared_task
def generate_crm_report():
    '''Generate a weekly CRM report by querying GraphQL for summary data.'''
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Setup GraphQL client
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql/",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    # Query to get customers, orders and revenue
    query = gql("""
    query {
        customers {
            id
        }
        orders {
            id
            totalAmount
        }
    }
    """)

    try:
        result = client.execute(query)

        total_customers = len(result.get("customers", []))
        orders = result.get("orders", [])
        total_orders = len(orders)
        total_revenue = sum(o.get("totalAmount", 0) for o in orders)

        report_message = (
            f"{timestamp} - Report: "
            f"{total_customers} customers, {total_orders} orders, {total_revenue} total revenue"
        )
        logging.info(report_message)
        print(report_message)
    except Exception as e:
        logging.error(f"Error generating CRM report: {e}")
        print(f"Error generating CRM report: {e}")



