from django.db import models


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        DOUBLE = "DOUBLE", "Double"
        TRIPLE = "TRIPLE", "Triple"
        FOUR_BED = "FOUR_BED", "Four-bed suite"

    number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=RoomType.choices, default=RoomType.DOUBLE)
    capacity = models.PositiveSmallIntegerField(default=2)
    monthly_fee = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("number",)

    @property
    def occupied_count(self):
        return self.residents.count()

    @property
    def status(self):
        if self.occupied_count == 0:
            return "Vacant"
        if self.occupied_count >= self.capacity:
            return "Occupied"
        return "Partially Occupied"

    def __str__(self):
        return self.number

    @property
    def name(self):
        return self.get_room_type_display()

    @property
    def price(self):
        return f"₹{self.monthly_fee:,.0f}"

    @property
    def features(self):
        return f"Up to {self.capacity} residents"

    @property
    def image(self):
        return "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=900&q=85"
