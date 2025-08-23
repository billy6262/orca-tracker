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


class Zone(models.Model):
    """Model to store geographic zones."""
    name = models.CharField(max_length=100, unique=True)
    zoneNumber = models.PositiveIntegerField(primary_key=True)
    adjacentZones = models.ManyToManyField("self", symmetrical=False, blank=True, related_name='adjacent_to')
    nextAdjacentZones = models.ManyToManyField("self", symmetrical=False, blank=True, related_name='next_adjacent_to')
    boundary = models.TextField()  # GeoJSON or WKT representation
    localities = models.TextField()  # List of localities within the zone

class Prediction(models.Model):
    """Model to store predictions about Orca sightings."""
    orca_sighting = models.ForeignKey(OrcaSighting, on_delete=models.CASCADE, related_name='predictions')
    predicted_time = models.DateTimeField()
    predicted_zone = models.CharField(max_length=100)
    confidence = models.FloatField()