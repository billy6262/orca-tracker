from django.db import models

# Create your models here.

class RawReport(models.Model):
    """Model to store raw email reports."""
    timeRecived = models.DateTimeField(auto_now_add=True)
    messageId = models.CharField(max_length=255, unique=True)
    body = models.TextField()
    processed = models.BooleanField(default=False)
    subject = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)

class OrcaSighting(models.Model):
    """Model to store Orca sightings."""
    raw_report = models.ForeignKey(RawReport, on_delete=models.DO_NOTHING, related_name='sightings')
    time = models.DateTimeField()
    zone = models.CharField(max_length=100)
    direction = models.CharField(max_length=50)
    count = models.PositiveIntegerField()
    month = models.PositiveIntegerField()   # for seasonality
    dayOfWeek = models.PositiveIntegerField()   # 1-7
    hour = models.PositiveIntegerField() # 0-23
    reportsIn5h = models.PositiveIntegerField() # in same zone
    reportsIn24h = models.PositiveIntegerField()
    reportsInAdjacentZonesIn5h = models.PositiveIntegerField() # immediately adjacent zones
    reportsInAdjacentPlusZonesIn5h = models.PositiveIntegerField() # next adjacent zones
