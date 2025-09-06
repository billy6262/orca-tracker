from rest_framework import serializers
import data_pipeline.models as dp_models


class OrcaSightingSerializer(serializers.ModelSerializer):
    class Meta:
        model = dp_models.OrcaSighting
        fields = '__all__'


class RawReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = dp_models.RawReport
        fields = '__all__'

class PredictionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = dp_models.PredictionBatch
        fields = '__all__'

class PredictionBucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = dp_models.PredictionBucket
        fields = '__all__'

class ZonePredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = dp_models.ZonePrediction
        fields = '__all__'
