from rest_framework import serializers
from data_pipeline.models import RawReport, OrcaSighting, Prediction


class OrcaSightingSerializer(serializers.ModelSerializer):
    """Serializer for Orca sightings."""
    class Meta:
        model = OrcaSighting
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    """Serializer for predictions about Orca sightings."""
    class Meta:
        model = Prediction
        fields = '__all__'


class RawReportSerializer(serializers.ModelSerializer):
    """Serializer for raw email reports."""
    class Meta:
        model = RawReport
        fields = '__all__'
