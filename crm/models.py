from django.db import models

# Create your models here.

class Customer(models.Model):
    '''Model representing a customer.'''
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    '''Model representing a product'''
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    '''Models representing an order'''
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_date = models.DateTimeField(auto_now_add=True)

    def calculate_totalPrice(self):
        '''Calculate the total price of the order based on the product price and quantity.'''
        total = sum(p.price for p in self.product.all())
        self.total_amount = total
        self.save()
        return total
    
    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"
