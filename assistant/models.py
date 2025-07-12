from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sustainability = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    x_coord = models.IntegerField(default=0)
    y_coord = models.IntegerField(default=0)

    def __str__(self):
        return self.name
