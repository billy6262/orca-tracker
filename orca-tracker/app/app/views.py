from data_pipeline import models
from rest_framework.response import Response
from rest_framework.decorators import api_view
from app.serializers import RawReportSerializer, OrcaSightingSerializer, PredictionSerializer
from django.utils import timezone
from django.db.models import Count

@api_view(['GET'])
def get_raw_reports_by_date_range(request, start_date, end_date):
    reports = models.RawReport.objects.filter(timeRecived__range=[start_date, end_date])
    serializer = RawReportSerializer(reports, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_sightings_by_date_range(request, start_date, end_date):
    sightings = models.OrcaSighting.objects.filter(time__range=[start_date, end_date], present=True)
    serializer = OrcaSightingSerializer(sightings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_sightings_by_zone_count(request, start_date, end_date):
    """Get aggregated sighting counts by zone for the date range."""
    zone_counts = (
        models.OrcaSighting.objects
        .filter(time__range=[start_date, end_date], present=True)
        .values('zone')
        .annotate(count=Count('id'))
        .order_by('zone')
    )
    
    # Convert to list of dicts with zone as integer for proper sorting
    result = []
    for item in zone_counts:
        try:
            zone_num = int(item['zone'])
            result.append({
                'zone': zone_num,
                'count': item['count']
            })
        except (ValueError, TypeError):
            # Skip invalid zone numbers
            continue
    
    # Sort by zone number
    result.sort(key=lambda x: x['zone'])
    
    return Response(result)

@api_view(['GET'])
def get_future_predictions(request):
    recentsighting = models.OrcaSighting.objects.order_by('time').first()
    predictions = models.Prediction.objects.filter(orca_sighting=recentsighting)
    serializer = serializers.PredictionSerializer(predictions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_predictions_by_date_range(request, start_date, end_date):
    predictions = models.Prediction.objects.filter(prediction_time__range=[start_date, end_date])
    serializer = PredictionSerializer(predictions, many=True)
    return Response(serializer.data)