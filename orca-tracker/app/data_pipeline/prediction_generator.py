from .models import PredictionBatch, PredictionBucket, OrcaSighting, ZonePrediction, Zone
import xgboost as xgb
import pandas as pd
import numpy as np
import joblib
import os
from django.conf import settings
from datetime import timedelta
import logging

number_of_buckets = 8
MODEL_DIRECTORY = os.path.join(settings.BASE_DIR, "MLmodels")
BUCKET_MODELS = {}
ZONE_ENCODING = None
FEATURE_COLUMNS = None

TIME_BUCKETS = [(i , i +6) for i in range(0, number_of_buckets * 6, 6)] 
BUCKET_LABELS = [f"{start}-{end}h" for start, end in TIME_BUCKETS]


def load_models():
    """loads models in from file locations for use in making predictions"""
    global BUCKET_MODELS, ZONE_ENCODING, FEATURE_COLUMNS

    try: 
        # label encoding for the model
        ZONE_ENCODING = joblib.load(os.path.join(MODEL_DIRECTORY, "zone_encoder.pkl")) 
        # feature columns to match trained model
        FEATURE_COLUMNS = joblib.load(os.path.join(MODEL_DIRECTORY, "features.pkl"))

        for bucket in range(len(TIME_BUCKETS)):  #loading individual models for each time bucket
            model_path = os.path.join(MODEL_DIRECTORY, f"orca_model_bucket_{bucket}.pkl")
            model = joblib.load(model_path)
            BUCKET_MODELS[bucket] = model
        logging.info("Models loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading models: {e}")


def prep_sightings(sighting):
    """Prepares sighting data for model prediction."""
    
    feature_data = {}
        
    # Direct feature mappings from sighting fields with handling for None values
    feature_data['month'] = sighting.month
    feature_data['dayOfWeek'] = sighting.dayOfWeek
    feature_data['hour'] = sighting.hour
    feature_data['isWeekend'] = sighting.isWeekend
    feature_data['sunUp'] = sighting.sunUp if sighting.sunUp is not None else False
    feature_data['count'] = sighting.count
    feature_data['present'] = 1 if sighting.present else 0
    feature_data['reportsIn5h'] = sighting.reportsIn5h if sighting.reportsIn5h is not None else 0
    feature_data['reportsIn24h'] = sighting.reportsIn24h if sighting.reportsIn24h is not None else 0
    feature_data['reportsInAdjacentZonesIn5h'] = sighting.reportsInAdjacentZonesIn5h if sighting.reportsInAdjacentZonesIn5h is not None else 0
    feature_data['reportsInAdjacentPlusZonesIn5h'] = sighting.reportsInAdjacentPlusZonesIn5h if sighting.reportsInAdjacentPlusZonesIn5h is not None else 0
    feature_data['ZoneNumber_id'] = sighting.ZoneNumber.zoneNumber
    if sighting.timeSinceLastSighting:
        feature_data['timeSinceLastSighting_hours'] = sighting.timeSinceLastSighting.total_seconds() / 3600
        feature_data['hours_since_last'] = sighting.timeSinceLastSighting.total_seconds() / 3600
    else:
        feature_data['timeSinceLastSighting_hours'] = 0
        feature_data['hours_since_last'] = 0

    feature_data['zone_num'] = ZONE_ENCODING.transform([sighting.zone])[0]
    # Zone number handling

    sighting_df = pd.DataFrame([feature_data])

        # Ensure all required feature columns are present
    missing_columns = set(FEATURE_COLUMNS) - set(sighting_df.columns)
    if missing_columns:
        logging.warning(f"Missing feature columns: {missing_columns}. Adding with default values.")
        for col in missing_columns:
            sighting_df[col] = 0

    sighting_df = sighting_df[FEATURE_COLUMNS]  # Reorder columns to match model training
    sighting_df = sighting_df.fillna(0)  # Fill any remaining NaN values with 0
    return sighting_df


def calculate_timeframes(start_time):
    """Calculates the timeframes for the prediction buckets and projects actual time windows based on sighting time."""
    timeframes = []
    for start, end in TIME_BUCKETS:
        bucket_start = start_time + timedelta(hours=start)
        bucket_end = start_time + timedelta(hours=end)
        timeframes.append((bucket_start, bucket_end))
    return timeframes


def generate_predictions(sighting):
    """Generates predictions for the given sighting for each zone and time bucket."""
    features = prep_sightings(sighting) #formating the sighting data for model input
    bucket_times = calculate_timeframes(sighting.time) #projecting bucket times to sighting time
    prediction_batch = PredictionBatch.objects.create(source_sighting=sighting) # new batch object to hold all bucket predictions
    batch_overall_prob = 0
    

    for bucket_idx, zone_models in BUCKET_MODELS.items():
        bucket_name = BUCKET_LABELS[bucket_idx]
        start_time, end_time = bucket_times[bucket_idx]
        # Create PredictionBucket instance to store individual zone predictions
        bucket = PredictionBucket.objects.create(
            batch=prediction_batch,
            time_bucket=bucket_name,
            bucket_start_hour=TIME_BUCKETS[bucket_idx][0],
            bucket_end_hour=TIME_BUCKETS[bucket_idx][1],
            forecast_start_time=start_time,
            forecast_end_time=end_time,
            overall_probability=0.0  # Placeholder, will be updated later
        )
        zone_probabilities = {}

        for zoneCol, model in zone_models.items():
            zoneName = zoneCol.split('_zone_')[-1] # Extract zone name from column name

            try:
                prob = model.predict_proba(features)  # Probability of presence
                if len(prob[0]) > 1: 
                    zoneProb = prob[0][1]  # Get probability of class 1 (sighting)
                else:
                    zoneProb = 0
                zone_probabilities[zoneName] = zoneProb
            except Exception as e:
                logging.error(f"Error predicting for zone {zoneName} in bucket {bucket_name}: {e}")
                zone_probabilities[zoneName] = 0
                

        # Sort predictions first
        sorted_zone_predictions = sorted(zone_probabilities.items(), key=lambda item: item[1], reverse=True)

        # Create predictions with proper ranking
        for rank, (zoneName, prob) in enumerate(sorted_zone_predictions, start=1): 
            is_top_5 = rank <= 5  # Mark top 5 zones
            try:
                # Look up by zoneNumber (which works)
                zone_number = int(zoneName)
                zone_obj = Zone.objects.get(zoneNumber=zone_number)
                zoneName = zone_obj.name  # Get actual name for display
            except Zone.DoesNotExist:
                zone_obj = None
                logging.warning(f"Zone '{zoneName}' not found in database")

            ZonePrediction.objects.create(
                bucket=bucket,
                zone=zoneName,
                zone_number=zone_obj, 
                probability=prob,
                rank=rank,
                is_top_5=is_top_5
            )
        total_prob = 0
        for _, zoneProb in zone_probabilities.items():
            total_prob = total_prob + zoneProb - (zoneProb * total_prob) #union of probabilities formula non exclusive
        total_prob = min(1.0, total_prob)  # Caps it at exactly 1.0 incase of rounding errors

        bucket.overall_probability = total_prob # Update overall probability for the bucket
        batch_overall_prob = batch_overall_prob + total_prob 
        bucket.save()
    
    batch_overall_prob = batch_overall_prob / number_of_buckets

    confidence = 'low'
    if batch_overall_prob > 0.6:
        confidence = 'high'
    elif batch_overall_prob > 0.3:
        confidence = 'medium'

    prediction_batch.overall_confidence = confidence
    prediction_batch.save()

    return prediction_batch