#causes the back end to wait for the database to be ready before starting
from django.core.management.base import BaseCommand

import time

from psycopg2 import OperationalError as Pyscopg2Error
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Wait for the database to be ready'

    def handle(self, *args, **kwargs):
        self.stdout.write('Waiting for database...')
        db_up = False
        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Pyscopg2Error, OperationalError):
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database is ready!'))


        