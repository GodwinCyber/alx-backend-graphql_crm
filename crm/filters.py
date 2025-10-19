import django_filters
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    '''Custom filter for Customer model'''
    name = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    created_at__gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    phone_pattern = django_filters.CharFilter(method='phone_pattern')

    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at']

    def phone_pattern(self, queryset, name, value):
        '''Filter customers whose number start with the given pattern'''
        return queryset.filter(phone__startswith=value)

class ProductFilter(django_filters.FilterSet):
    '''Custom filter for product model'''
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    price__gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price__lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    stock__gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock__lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')

    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']

    def filter_low_stock(self, queryset, name,value):
        if value:
            return queryset.filter(stock__lte=10)
        return queryset


class OrderFilter(django_filters.FilterSet):
    '''Custom filter for Order model'''
    total_amount__gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount__lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date__get = django_filters.DateRangeFilter(field_name='order_date', lookup_expr='gte')
    order_date__lte = django_filters.DateRangeFilter(field_name='order_date', lookup_expr='lte')
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains') 
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains')
    product_id = django_filters.NumberFilter(field_name='products__id', lookup_expr='exact')

    class Meta:
        model = Order
        fields = ['total_amount', 'order_date', 'customer_name', 'product_name', 'product_id']
