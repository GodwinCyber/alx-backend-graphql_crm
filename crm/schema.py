import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
import re
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation


# =====================
# GraphQL object Types
# =====================

class CustomerType(DjangoObjectType):
    '''GraphQL type for Customer model'''
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone']

class ProductType(DjangoObjectType):
    '''GraphQL type for Product model'''
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock']

class OrderType(DjangoObjectType):
    '''GraphQL type for Order model'''
    class Meta:
        model = Order
        fields = ['id', 'customer', 'products', 'total_amount', 'order_date']

# =====================
# CreateCustomer Mutation
# =====================

class CreateCustomerInput(graphene.InputObjectType):
    '''Input type for creating a new customer'''
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class CreateCustomer(graphene.Mutation):
    '''Mutation to create a new customer'''
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()


    @staticmethod
    def validate_email(email):
        '''Ensure the email is unique'''
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists.")

    @staticmethod
    def validate_phone(phone):
        '''Validate the phone number format (+1234567890 0r 123-456-7890)'''
        if phone and not re.match(r'^\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', phone):
            raise Exception("Invalid phone number format.")
        

    @classmethod
    def mutate(cls, root, info, input):
        '''Create a new customer'''
        cls.validate_email(input.email)
        cls.validate_phone(input.phone)

        customer = Customer(
            name=input.name,
            email=input.email,
            phone=input.phone
        )
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully.")



# =============================
# BulkCreateCustomers Mutation
# =============================

class BulkCreateCustomers(graphene.Mutation):
    '''Mutation to bulk create customers'''
    class Arguments:
        input = graphene.List(CreateCustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        '''Bulk create customers'''
        created_customers = []
        errors = []

        with transaction.atomic():
            for i, data in enumerate(input):
                try:
                    # validate email and phone
                    if Customer.objects.filter(email=data.email).exists():
                        raise Exception(f"Email '{data.email}' already exists.")
                    
                    if data.phone and not re.match(r'^\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', data.phone):
                        raise Exception(f"Invalid phone number format: '{data.phone}'.")

                    customer = Customer.objects.create(
                        name=data.name,
                        email=data.email,
                        phone=data.phone
                    )    
                    created_customers.append(customer)
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
        return BulkCreateCustomers(customers=created_customers, errors=errors, message="Bulk customer creation completed.")


# =====================
# CreateProduct Mutation
# =====================

class CreateProductInput(graphene.InputObjectType):
    '''Input type for creating a new product'''
    name = graphene.String(required=True)
    price = graphene.Float()
    stock = graphene.Int(required=False, default_value=0)


class CreateProduct(graphene.Mutation):
    '''Mutation to create a new product'''
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        '''Create a new product'''
        if not isinstance(input.price, (float, int)): # Ensure float or decimal
            raise Exception("Invalid price format. Must be a float or decimal")
        if input.price <= 0:
            raise Exception("Price must be a positive value.")
        if input.stock < 0:
            raise Exception("Stock cannot be negative value.")
        
        try:
            price = Decimal(str(input.price))
        except (InvalidOperation, ValueError):
            raise Exception("Invalid price format. Must be a float or decimal")
        
        product = Product.objects.create(
            name=input.name,
            price=price,
            stock=input.stock
        )
        product.save()
        return CreateProduct(product=product, message="Product created successfully.")


# =====================
# CreateOrder Mutation
# =====================
class CreateOrderInput(graphene.InputObjectType):
    '''Input type for creating a new order'''
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False, default_value=None)

class CreateOrder(graphene.Mutation):
    '''Mutation to create a new order'''
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        '''Create a new order'''
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        if not input.product_ids:
            raise Exception("At least one product must be included in the order.") 

        products = Product.objects.filter(id__in=input.product_ids)
        if products.count() != len(input.product_ids):
            raise Exception("One or more product IDs are invalid.")
        
        order = Order.objects.create(
            customer=customer,
            # products=products.first(),  # Assuming single product per order for simplicity
            # total_amount=products.first().price,  # Initial total amount
            order_date=input.order_date or timezone.now()
        )
        order.products.set(products)
        total = sum(p.price for p in products)
        order.total_amount = total
        order.save()

        return CreateOrder(order=order, message="Order created successfully.")


# =====================
# Root Mutation
# =====================
class Query(graphene.ObjectType):
    '''Root Query'''
    customers = graphene.List(lambda: CustomerType)
    products = graphene.List(lambda: ProductType)
    orders = graphene.List(lambda: OrderType)

    def resolve_customers(root, info):
        '''Resolve all customers'''
        return Customer.objects.all()
    
    def resolve_products(root, info):
        '''Resolve all products'''
        return Product.objects.all()
    
    def resolve_orders(root, info):
        '''Resolve all orders'''
        return Order.objects.all()
    
class Mutation(graphene.ObjectType):
    '''Root Mutation'''
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()



