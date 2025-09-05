from rest_framework import serializers
import data_pipeline.models as dp_models


class OrcaSightingSerializer(serializers.ModelSerializer):
    """Serializer for Orca sightings."""
    class Meta:
        model = dp_models.OrcaSighting
        fields = '__all__'


class RawReportSerializer(serializers.ModelSerializer):
    """Serializer for raw email reports."""
    class Meta:
        model = dp_models.RawReport
        fields = '__all__'

class PredictionBatchSerializer(serializers.ModelSerializer):
    """Serializer for PredictionBatch model."""
    class Meta:
        model = dp_models.PredictionBatch
        fields = '__all__'

class PredictionBucketSerializer(serializers.ModelSerializer):
    """Serializer for PredictionBucket model."""
    class Meta:
        model = dp_models.PredictionBucket
        fields = '__all__'

class ZonePredictionSerializer(serializers.ModelSerializer):
    """Serializer for ZonePrediction model."""
    class Meta:
        model = dp_models.ZonePrediction
        fields = '__all__'
