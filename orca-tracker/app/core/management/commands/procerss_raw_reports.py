import os
from django.core.management.base import BaseCommand
from data_pipeline.email_processor import process_unprocessed_reports

class Command(BaseCommand):
    help = 'Process unprocessed email reports'

    def handle(self, *args, **options):
        process_unprocessed_reports()