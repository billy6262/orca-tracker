from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import TruncHour

# Create your models here.
class Zone(models.Model):
    """Model to store geographic zones."""
    name = models.CharField(max_length=100, unique=True)
    zoneNumber = models.PositiveIntegerField(primary_key=True)
    adjacentZones = models.ManyToManyField("self", symmetrical=False, blank=True, related_name='adjacent_to')
    nextAdjacentZones = models.ManyToManyField("self", symmetrical=False, blank=True, related_name='next_adjacent_to')
    boundary = models.TextField()  # GeoJSON or WKT representation
    localities = models.TextField()  # List of localities within the zone


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
    raw_report = models.ForeignKey(
        RawReport,
        on_delete=models.CASCADE,
        related_name='sightings',
        null=True, blank=True,   # allow absence rows to have no raw report
    )
    time = models.DateTimeField()
    zone = models.CharField(max_length=100)
    ZoneNumber = models.ForeignKey(
        Zone, 
        on_delete=models.CASCADE,
        related_name='sightings', 
        to_field='zoneNumber',
        null=True, 
        blank=True
    )
    direction = models.CharField(max_length=50)
    count = models.PositiveIntegerField()
    month = models.PositiveIntegerField()   # for seasonality
    dayOfWeek = models.PositiveIntegerField()   # 1-7
    hour = models.PositiveIntegerField() # 0-23

    # Recency metrics - allow null so absences can leave blank
    reportsIn5h = models.PositiveIntegerField(null=True, blank=True)
    reportsIn24h = models.PositiveIntegerField(null=True, blank=True)
    reportsInAdjacentZonesIn5h = models.PositiveIntegerField(null=True, blank=True)
    reportsInAdjacentPlusZonesIn5h = models.PositiveIntegerField(null=True, blank=True)

    present = models.BooleanField(default=True)
    timeSinceLastSighting = models.DurationField(null=True, blank=True)
    isWeekend = models.BooleanField(default=False)

    # Leave sunUp blank for absences
    sunUp = models.BooleanField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                TruncHour('time'),
                models.F('zone'),
                name='uq_absence_zone_per_hour',
                condition=Q(present=False),
            ),
        ]


class Prediction(models.Model):
    """Model to store predictions about Orca sightings."""
    orca_sighting = models.ForeignKey(OrcaSighting, on_delete=models.CASCADE, related_name='predictions')
    date_created = models.DateTimeField(auto_now_add=True)
    predicted_time = models.DateTimeField()
    predicted_zone = models.CharField(max_length=100)
    confidence = models.FloatField()

class ZoneSeasonality(models.Model):
    """Model to store seasonal information about zones."""
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='seasonality')
    month = models.PositiveIntegerField()
    avg_sightings = models.FloatField()

class ZoneEffort(models.Model):
    """Model to store effort information about zones."""
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='effort')
    hour = models.PositiveIntegerField()
    avg_sightings = models.FloatField()