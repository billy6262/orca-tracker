from data_pipeline import models
from rest_framework.response import Response
from rest_framework.decorators import api_view
from app.serializers import RawReportSerializer, OrcaSightingSerializer,PredictionBatchSerializer, PredictionBucketSerializer, ZonePredictionSerializer
from django.db.models import Count
from core.management.commands.generate_predictions import Command
import time

@api_view(['GET'])
def get_raw_reports_by_date_range(request, start_date, end_date):
    """Get all raw reports for the date range. Must be in YYYY-MM-DD."""
    reports = models.RawReport.objects.filter(timeRecived__range=[start_date, end_date])
    serializer = RawReportSerializer(reports, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_sightings_by_date_range(request, start_date, end_date):
    """Get all sightings for the date range. Must be in YYYY-MM-DD."""
    sightings = models.OrcaSighting.objects.filter(time__range=[start_date, end_date], present=True)
    serializer = OrcaSightingSerializer(sightings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_sightings_by_zone_count(request, start_date, end_date):
    """Get aggregated sighting counts by zone number for the date range. Must be in YYYY-MM-DD."""
    
    # Group by zoneNumber instead of zone text field
    zone_counts = (
        models.OrcaSighting.objects
        .filter(time__range=[start_date, end_date], present=True)
        .values('ZoneNumber__zoneNumber') 
        .annotate(count=Count('id'))
        .order_by('ZoneNumber__zoneNumber')
    )
    
    # Convert to list of dicts with 'zone' and 'count' keys
    result = []
    for item in zone_counts:
        zone_number = item['ZoneNumber__zoneNumber']
        if zone_number is not None:
            result.append({
                'zone': zone_number,
                'count': item['count']
            })
    
    return Response(result)

@api_view(['GET'])
def get_predictions_most_recent(request):
    """Get predictions for the most recent sighting."""
    latest_sighting = models.OrcaSighting.objects.filter(present=True).order_by('-time').first()
    if not latest_sighting:
        return Response({"error": "No sightings found."}, status=404)
    
    latest_batch = models.PredictionBatch.objects.filter(source_sighting=latest_sighting).order_by('-created_at').first()
    if not latest_batch:
        Command().handle()
        time.sleep(2)  # Wait a moment for the batch to be created
        latest_batch = models.PredictionBatch.objects.filter(source_sighting=latest_sighting).order_by('-created_at').first()
    # Serialize the predictions and related data
    batch_serializer = PredictionBatchSerializer(latest_batch)
    bucket_serializer = PredictionBucketSerializer(models.PredictionBucket.objects.filter(batch=latest_batch).order_by('bucket_start_hour'), many=True)
    
    # For each bucket, get zone predictions
    bucket_data = bucket_serializer.data
    for bucket_item in bucket_data:
        bucket_id = bucket_item['id']
        zone_predictions = models.ZonePrediction.objects.filter(bucket_id=bucket_id).order_by('rank')
        zone_serializer = ZonePredictionSerializer(zone_predictions, many=True)
        bucket_item['zone_predictions'] = zone_serializer.data
    
    response_data = {
        'prediction_batch': batch_serializer.data,
        'buckets': bucket_data
    }
    
    return Response(response_data)

@api_view(['GET'])
def get_sightings_count_by_hour(request, start_date, end_date):
    """Get aggregated sighting counts by hour for the date range. Must be in YYYY-MM-DD."""
    sightings = (
        models.OrcaSighting.objects
        .filter(time__range=[start_date, end_date], present=True)
        .values('hour')
        .annotate(count=Count('id'))
    )

    return Response(sightings)