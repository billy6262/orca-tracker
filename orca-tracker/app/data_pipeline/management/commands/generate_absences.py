from datetime import datetime
from typing import Optional

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from data_pipeline.report_absence_gen import generate_absence_reports_historical

class Command(BaseCommand):
    help = (
        "Generate absence reports (present=False) historically in hourly buckets, "
        "maintaining a global 1:3 sightings:absences ratio with effort×seasonality weighting."
    )

    def add_arguments(self, parser):
        parser.add_argument("--start", type=str, default=None, help="ISO datetime (e.g., 2024-01-01T00:00:00)")
        parser.add_argument("--end", type=str, default=None, help="ISO datetime (e.g., 2024-12-31T23:00:00)")
        parser.add_argument("--step-hours", type=int, default=1, help="Bucket step in hours (default 1)")

    def handle(self, *args, **options):
        start: Optional[str] = options["start"]
        end: Optional[str] = options["end"]
        step_hours: int = options["step_hours"]

        def _parse(dt: Optional[str]) -> Optional[datetime]:
            if not dt:
                return None
            parsed = parse_datetime(dt)
            if parsed and timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed

        start_dt = _parse(start)
        end_dt = _parse(end)

        buckets, selected, created = generate_absence_reports_historical(
            start=start_dt, end=end_dt, step_hours=step_hours
        )
        self.stdout.write(self.style.SUCCESS(
            f"Processed buckets: {buckets} | Selected: {selected} | Created: {created}"
        ))