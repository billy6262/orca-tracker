from django.core.management.base import BaseCommand
#this command fetches text reports from emails and stores them in the database
from data_pipeline.email_retriver import get_emails
from data_pipeline.email_processor import process_unprocessed_reports

class Command(BaseCommand):
    help = 'Fetch and store raw email reports'

    def handle(self, *args, **kwargs):
        self.stdout.write('Fetching email reports...')
        
        get_emails()        
        self.stdout.write(self.style.SUCCESS('Successfully fetched and stored email reports.'))
        process_unprocessed_reports()
        self.stdout.write(self.style.SUCCESS('Successfully processed unprocessed reports.'))
