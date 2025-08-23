import serializers
from data_pipeline import models
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def get_raw_reports_by_date_range(request, start_date, end_date):
    reports = models.RawReport.objects.filter(receivedAt__range=[start_date, end_date])
    serializer = serializers.RawReportSerializer(reports, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_sightings_by_date_range(request, start_date, end_date):
    sightings = models.OrcaSighting.objects.filter(date__range=[start_date, end_date])
    serializer = serializers.OrcaSightingSerializer(sightings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_future_predictions(request):
    recentsighting = models.OrcaSighting.objects.order_by('time').first()
    predictions = models.Prediction.objects.filter(orca_sighting=recentsighting)
    serializer = serializers.PredictionSerializer(predictions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_predictions_by_date_range(request, start_date, end_date):
    predictions = models.Prediction.objects.filter(date__range=[start_date, end_date])
    serializer = serializers.PredictionSerializer(predictions, many=True)
    return Response(serializer.data)