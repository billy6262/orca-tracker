from django.db import models

# Create your models here.

class OrcaSighting(models.Model):
    """Model to store Orca sightings."""
    time = models.DateTimeField()
    zone = models.CharField(max_length=100)
    direction = models.CharField(max_length=50)
    count = models.PositiveIntegerField()
    month = models.PositiveIntegerField()   # for seasonality
    dayOfWeek = models.PositiveIntegerField()   # 1-7
    hour = models.PositiveIntegerField() # 0-23
    reportsIn5h = models.PositiveIntegerField() # in same zone
    reportsIn24h = models.PositiveIntegerField()
    reportsInAdjacentZonesIn5h = models.PositiveIntegerField() # imeadiately adjacent zones
    reportsInAdjacentPlusZonesIn5h = models.PositiveIntegerField() # next adjacent zones