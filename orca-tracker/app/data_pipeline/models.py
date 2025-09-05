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
    direction = models.CharField(max_length=50, null=True, blank=True)
    count = models.PositiveIntegerField()
    month = models.PositiveIntegerField()   # for seasonality
    dayOfWeek = models.PositiveIntegerField()   # 1-7
    hour = models.PositiveIntegerField() # 0-23

    # Recency metrics and feature engineering - allow null so absences can leave blank - populated by sql database trigger functions
    reportsIn5h = models.PositiveIntegerField(null=True, blank=True)
    reportsIn24h = models.PositiveIntegerField(null=True, blank=True)
    reportsInAdjacentZonesIn5h = models.PositiveIntegerField(null=True, blank=True)
    reportsInAdjacentPlusZonesIn5h = models.PositiveIntegerField(null=True, blank=True)
    present = models.BooleanField(default=True)
    timeSinceLastSighting = models.DurationField(null=True, blank=True)
    isWeekend = models.BooleanField(default=False)
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


class PredictionBatch(models.Model):
    """Model to store a batch of predictions generated at one time."""
    source_sighting = models.ForeignKey(
        OrcaSighting, 
        on_delete=models.CASCADE, 
        related_name='prediction_batches'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    model_version = models.CharField(
        max_length=50, 
        default='xgboost_v1',
        help_text="Version of the prediction model used"
    )
    overall_confidence = models.CharField()
    



class PredictionBucket(models.Model):
    """Model to store predictions for a specific time bucket."""
    batch = models.ForeignKey(
        PredictionBatch, 
        on_delete=models.CASCADE, 
        related_name='buckets'
    )
    time_bucket = models.CharField(
        max_length=20,
        help_text="Time bucket (e.g., '0-6h', '6-12h', '12-18h')"
    )
    bucket_start_hour = models.PositiveIntegerField()
    bucket_end_hour = models.PositiveIntegerField()
    forecast_start_time = models.DateTimeField()
    forecast_end_time = models.DateTimeField()
    overall_probability = models.FloatField()
    
    class Meta:
        unique_together = ['batch', 'time_bucket']
        ordering = ['bucket_start_hour']



class ZonePrediction(models.Model):
    """Model to store individual zone predictions within a time bucket."""
    bucket = models.ForeignKey(
        PredictionBucket, 
        on_delete=models.CASCADE, 
        related_name='zone_predictions'
    )
    zone = models.CharField(max_length=100)
    zone_number = models.ForeignKey(
        Zone, 
        on_delete=models.CASCADE,
        related_name='predictions', 
        to_field='zoneNumber',
        null=True, 
        blank=True
    )
    probability = models.FloatField()
    rank = models.PositiveIntegerField()
    is_top_5 = models.BooleanField(
        default=False,
        help_text="Whether this zone is in the top 5 predictions"
    )
    
    class Meta:
        unique_together = ['bucket', 'zone']
        ordering = ['rank']
    
    def __str__(self):
        return f"Zone {self.zone} - {self.probability:.3f} probability (rank {self.rank})"



class ZoneSeasonality(models.Model):
    """Model to store seasonal information about zones. mostly for absence generation"""
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='seasonality')
    month = models.PositiveIntegerField()
    avg_sightings = models.FloatField()

class ZoneEffort(models.Model):
    """Model to store effort information about zones. mostly for absence generation"""
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='effort')
    hour = models.PositiveIntegerField()
    avg_sightings = models.FloatField()