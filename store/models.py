from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')  # Путь для загрузки изображений

    def __str__(self):
        return self.name

    @property
    def price_rb(self):
        return self.price * 3

class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Привязка к пользователю
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) для {self.user.username}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    game_username = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    telegram_username = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)  # Дата и время создания заказа
    link_sent = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ("Created", "Created"),
        ("In progress", "In Progress"),
        ("Completed", "Completed"),
        ("Rejected", "Rejected"),
    ]
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default="created")

    def __str__(self):
        return f"Order #{self.id} от {self.user.username}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} для Order #{self.order.id}"