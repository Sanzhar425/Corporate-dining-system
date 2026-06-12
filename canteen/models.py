from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Әкімші'),
        ('user', 'Қызметкер'),
        ('cashier', 'Кассир'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.username} ({self.role})"


class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('first', 'Бірінші тағам'),
        ('second', 'Екінші тағам'),
        ('salad', 'Салат'),
        ('drink', 'Сусын'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_available = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price}₸"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Күтілуде'),
        ('preparing', 'Дайындалуда'),
        ('ready', 'Дайын'),
        ('completed', 'Аяқталды'),
        ('cancelled', 'Болдырылмады'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    ordered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Тапсырыс #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('deposit', 'Толтыру'),
        ('payment', 'Төлем'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}₸"