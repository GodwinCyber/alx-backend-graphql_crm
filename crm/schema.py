import graphene
from graphene_django import DjangoObjectType
from crm.models import Customer, Product, Order
import re
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from .filters import CustomerFilter, ProductFilter, OrderFilter
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q


# =====================
# GraphQL object Types
# =====================

class CustomerType(DjangoObjectType):
    '''GraphQL type for Customer model'''
    class Meta:
        model = Customer
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)
        fields = ['id', 'name', 'email', 'phone', 'created_at']

class ProductType(DjangoObjectType):
    '''GraphQL type for Product model'''
    class Meta:
        model = Product
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)
        fields = ['id', 'name', 'price', 'stock']

class OrderType(DjangoObjectType):
    '''GraphQL type for Order model'''
    class Meta:
        model = Order
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)
        fields = ['id', 'customer', 'products', 'total_amount', 'order_date']


# =====================
# Filter Input Types for filtering and sorting   
# =====================
class CustomerFilterInput(graphene.InputObjectType):
    '''Input type for filtering customers'''
    name = graphene.String()
    email = graphene.String()
    created_at__gte = graphene.Date()
    created_at__lte = graphene.Date()
    phone_pattern = graphene.String()

class ProductFilterInput(graphene.InputObjectType):
    '''Input type for filtering products'''
    name = graphene.String()
    price__gte = Decimal()
    price__lte = Decimal()
    stock__gte = graphene.Int()
    stock__lte = graphene.Int()
    low_stock = graphene.Boolean()

class OrderByInput(graphene.InputObjectType):
    '''Input type for ordering results'''
    total_amount_gte = Decimal()
    total_amount_lte = Decimal()
    order_date_gte = graphene.Date()
    order_date_lte = graphene.Date()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()

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
    def mutate(cls, rootx, info, input):
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
    """Root Query with filtering and sorting support"""

    # Relay-style connections with filters
    all_customers = DjangoFilterConnectionField(CustomerType)
    all_products = DjangoFilterConnectionField(ProductType)
    all_orders = DjangoFilterConnectionField(OrderType)
    customers = graphene.List(
        CustomerType,
        filters=CustomerFilterInput(required=False),
        order_by=OrderByInput(required=False),
        description="Get customers with filtering and ordering"
    )
    products = graphene.List(
        ProductType,
        filters=ProductFilterInput(required=False),
        order_by=OrderByInput(required=False),
        description="Get products with filtering and ordering"
    )
    orders = graphene.List(
        OrderType,
        filters=OrderByInput(required=False),
        order_by=OrderByInput(required=False),
        description="Get orders with filtering and ordering"
    )

    # search queries
    search_customers = graphene.List(
        CustomerType,
        search_term=graphene.String(required=True),
        description="Search customers by name or email"
    )
    search_products = graphene.List(
        ProductType,
        search_term=graphene.String(required=True),
        description="Search products by name"
    )
    products_by_price_range = graphene.List(
        ProductType,
        min_price=graphene.Float(required=True),
        max_price=graphene.Float(required=True),
        description="Get products within a specific price range"
    )

    customer_order = graphene.List(
        OrderType,
        customer_id=graphene.ID(required=True),
        status=graphene.String(required=False),
        description="Get orders for a specific customer"
    )
    high_value_orders = graphene.List(
        OrderType,
        min_total=graphene.Float(required=True),
        description="Get orders with total amount greater than specified value"
    )

    # Non-Relay simple lists
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    # Simple resolvers
    def resolve_customers(self, info, filters=None, order_by=None):
        '''Resolve customers with optional filtering and ordering'''
        queryset = Customer.objects.all()
        if filters:
            filter_args = {}
            if filters.name:
                filter_args['name__icontains'] = filters.name
            if filters.email:
                filter_args['email__icontains'] = filters.email
            if filters.created_at__gte:
                filter_args['created_at__gte'] = filters.created_at__gte
            if filters.created_at__lte:
                filter_args['created_at__lte'] = filters.created_at__lte
            if filters.phone_pattern:
                filter_args['phone__startswith'] = filters.phone_pattern
            queryset = queryset.filter(**filter_args)
        if order_by:
            ordering = []
            for field, direction in order_by.items():
                if direction.lower() == 'desc':
                    ordering.append(f'-{field}')
                else:
                    ordering.append(field)
            queryset = queryset.order_by(*ordering)
        return queryset

    def resolve_products(self, info, filters=None, order_by=None):
        '''Resolve products with optional filtering and ordering'''
        queryset = Product.objects.all()
        if filters:
            filter_args = {}
            if filters.name:
                filter_args['name__icontains'] = filters.name
            if filters.price__gte is not None:
                filter_args['price__gte'] = filters.price__gte
            if filters.price__lte is not None:
                filter_args['price__lte'] = filters.price__lte
            if filters.stock__gte is not None:
                filter_args['stock__gte'] = filters.stock__gte
            if filters.stock__lte is not None:
                filter_args['stock__lte'] = filters.stock__lte
            if filters.low_stock is not None:
                if filters.low_stock:
                    filter_args['stock__lte'] = 10
            queryset = queryset.filter(**filter_args)
        if order_by:
            ordering = []
            for field, direction in order_by.items():
                if direction.lower() == 'desc':
                    ordering.append(f'-{field}')
                else:
                    ordering.append(field)
            queryset = queryset.order_by(*ordering)
        return queryset


    def resolve_orders(self, info, filters=None, order_by=None):
        '''Resolve orders with optional filtering and ordering'''
        queryset = Order.objects.all()
        if filters:
            filter_args = {}
            if filters.total_amount_gte is not None:
                filter_args['total_amount__gte'] = filters.total_amount_gte
            if filters.total_amount_lte is not None:
                filter_args['total_amount__lte'] = filters.total_amount_lte
            if filters.order_date_gte:
                filter_args['order_date__gte'] = filters.order_date_gte
            if filters.order_date_lte:
                filter_args['order_date__lte'] = filters.order_date_lte
            if filters.customer_name:
                filter_args['customer__name__icontains'] = filters.customer_name
            if filters.product_name:
                filter_args['products__name__icontains'] = filters.product_name
            if filters.product_id:
                filter_args['products__id'] = filters.product_id
            queryset = queryset.filter(**filter_args).distinct()
        if order_by:
            ordering = []
            for field, direction in order_by.items():
                if direction.lower() == 'desc':
                    ordering.append(f'-{field}')
                else:
                    ordering.append(field)
            queryset = queryset.order_by(*ordering)
        return queryset

    def resolve_search_customers(self, info, search_term):
        '''Search customers by name, phone or email'''
        if not search_term or len(search_term) < 2:
            return Customer.objects.none()
        
        return Customer.objects.filter(
            Q(name__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone__icontains=search_term)
        ).distinct()
    
    def resolve_search_products(self, info, search_term):
        '''Search products by name'''
        if not search_term or len(search_term) < 2:
            return Product.objects.none()
        
        return Product.objects.filter(
            name__icontains=search_term
        ).distinct()
    
    def resolve_products_by_price_range(self, info, min_price, max_price):
        '''Get products within a specific price range'''
        queryset = Product.objects.filter()

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset =queryset.filter(price__lte=max_price)
        return queryset
    
    def resolve_customer_order(self, info, customer_id, status=None):
        '''Get orders for a specific customer'''
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Order.objects.none()
        
        queryset = Order.objects.filter(customer=customer)
        return queryset
    
    def resolve_high_value_orders(self, info, min_total):
        '''Get orders with total amount greater than specified value'''
        queryset = Order.objects.filter(total_amount__gte=min_total)
        return queryset
    
# =================================
# UpdateLowStockProduct Mutations
# ==================================
class UpdateLowStockProducts(graphene.Mutation):
    '''Mutation to restock product with < 10'''
    class Arguments:
        restock_amount = graphene.Int(required=False, default_value=10)

    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, restock_amount):
        updated = []
        with transaction.atomic():
            low_stock_products = Product.objects.filter(stock__lt=10)
            for product in low_stock_products:
                product.stock += restock_amount
                product.save()
                updated.append(product)
        return UpdateLowStockProducts(
            updated_products=updated,
            message=f"{len(updated)} products restocked successfully."
        )
    
class Mutation(graphene.ObjectType):
    '''Root Mutation'''
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    UpdateLowStockProducts = UpdateLowStockProducts.Field()



