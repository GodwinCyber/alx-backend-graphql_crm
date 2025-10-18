import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()


from crm.models import Customer, Product, Order

def seed_data():
    '''Function to seed initial data into the database'''
    if not Customer.objects.exists():
        Customer.objects.create(name="Alice", email="alice@example.com", phone="+1234567890")
        Customer.objects.create(name="Bob", email="bob@example.com", phone="123-456-7890")
        print("Seeded Customers")

    if not Product.objects.exists():
        Product.objects.create(name="Laptop", price=999.99, stock=10)
        Product.objects.create(name="Phone", price=499.99, stock=20)
        print("Seeded Products")

    if not Order.objects.exists():
        customer = Customer.objects.first()
        product = Product.objects.first()
        if customer and product:
            order = Order.objects.create(customer=customer, product=product, total_amount=product.price)
            order.products.add(product)
            print("Seeded Orders")
            
if __name__ == "__main__":
    seed_data()



