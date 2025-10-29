#!/bin/bash
# =======================================================
# Script: Clean inactive customers
# Purpose: Delete customers with no order for 1 year
# Logs the number of deleted customers with timestamps
# =======================================================

source /Users/pioneer/virt/bin/activate
cd /Users/pioneer/alx-backend-graphql_crm

# Run Djnago shell command to delete inactive customers
NUM_DELETE=$(python manage.py shell -c "
from crm.models import Customer
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

one_year_ago = timezone.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(
    Q(orders__isnull=True) | Q(orders__order_date__lt=one_year_ago)
).distinct()
count = inactive_customers.count()
inactive_customers.delete()
print(count)
")


# Log the deletion with timestamp
echo \"$(date '+%Y-%m-%d %H:%M:%S') - Deleted $NUM_DELETE inactive customers\" >> /tmp/customer_cleanup_log.txt


