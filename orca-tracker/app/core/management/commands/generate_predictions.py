import data_pipeline.prediction_generator as pg
from django.core.management.base import BaseCommand
from django.db import transaction
from data_pipeline.models import PredictionBatch, OrcaSighting
import logging


class Command(BaseCommand):
    help = "Generate and store orca presence predictions for most recent sighting."

    def handle(self, *args, **options):
        # Use a transaction to ensure no duplicate predictions are created
        with transaction.atomic():
            latest_sighting = OrcaSighting.objects.filter(present=True).select_for_update().order_by('-time').first()
            # Check if there are any prediction batches first
            latest_batch = PredictionBatch.objects.order_by('-created_at').first()


            if not latest_sighting:
                logging.info("No sightings found.")
                return

            if latest_batch and latest_batch.source_sighting == latest_sighting:
                logging.info("Predictions already generated for the latest sighting.")
                return

            try:
                pg.load_models()
            except Exception as e:
                logging.error(f"Error loading models: {e}")
                return

            try:
                pg.generate_predictions(latest_sighting)
            except Exception as e:
                logging.error(f"Error generating predictions: {e}")
                return
