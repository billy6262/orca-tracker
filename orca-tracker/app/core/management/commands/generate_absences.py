from datetime import datetime
from typing import Optional

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import Min, Max, Q

from data_pipeline.models import OrcaSighting
from data_pipeline.report_absence_gen import generate_absence_reports_two_phase

class Command(BaseCommand):
    help = (
        "Generate absence reports (present=False) historically in hourly buckets, "
        "maintaining a global 1:3 sightings:absences ratio with effort×seasonality weighting."
    )

    def add_arguments(self, parser):
        parser.add_argument("--start", type=str, default=None, help="ISO datetime (e.g., 2024-01-01T00:00:00)")
        parser.add_argument("--end", type=str, default=None, help="ISO datetime (e.g., 2024-12-31T23:00:00)")
        parser.add_argument("--step-hours", type=int, default=1, help="Bucket step in hours (default 1)")
        parser.add_argument("--debug", action="store_true", help="Show diagnostic information")

    def handle(self, *args, **options):
        start: Optional[str] = options["start"]
        end: Optional[str] = options["end"]
        step_hours: int = options["step_hours"]
        debug: bool = options["debug"]

        def _parse(dt: Optional[str]) -> Optional[datetime]:
            if not dt:
                return None
            parsed = parse_datetime(dt)
            if parsed and timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed

        start_dt = _parse(start)
        end_dt = _parse(end)

        if debug:
            # Show current counts and ratio
            total_present = OrcaSighting.objects.filter(present=True).count()
            total_absent = OrcaSighting.objects.filter(present=False).count()
            target_absent = 3 * total_present
            remaining = max(0, target_absent - total_absent)
            
            # Show date ranges - use Q objects for filters
            bounds = OrcaSighting.objects.aggregate(
                min_present=Min("time", filter=Q(present=True)),
                max_present=Max("time", filter=Q(present=True)),
                min_absent=Min("time", filter=Q(present=False)),
                max_absent=Max("time", filter=Q(present=False))
            )
            
            self.stdout.write(f"Current Stats:")
            self.stdout.write(f"  Present sightings: {total_present}")
            self.stdout.write(f"  Absent records: {total_absent}")
            self.stdout.write(f"  Target absent (3:1 ratio): {target_absent}")
            self.stdout.write(f"  Remaining to create: {remaining}")
            self.stdout.write(f"  Current ratio: 1:{total_absent/max(total_present, 1):.1f}")
            
            self.stdout.write(f"\nDate Ranges:")
            self.stdout.write(f"  Present sightings: {bounds['min_present']} to {bounds['max_present']}")
            self.stdout.write(f"  Absent records: {bounds['min_absent']} to {bounds['max_absent']}")
            
            if remaining == 0:
                self.stdout.write(self.style.WARNING("No absences needed - target ratio already met!"))
                # Continue anyway with two-phase generation

        # Define progress callback that doesn't reference undefined variables
        def progress_callback(message: str):
            self.stdout.write(f"[Progress] {message}")

        buckets, generated, kept, deleted = generate_absence_reports_two_phase(
            start=start_dt, 
            end=end_dt, 
            step_hours=step_hours,
            progress_callback=progress_callback
        )
        
        self.stdout.write(self.style.SUCCESS(
            f"Generation complete:\n"
            f"  Buckets processed: {buckets}\n"
            f"  Absences generated: {generated}\n"
            f"  Absences kept after downsampling: {kept}\n"
            f"  Absences deleted: {deleted}\n"
            f"  Final ratio: 1:{kept/max(OrcaSighting.objects.filter(present=True).count(), 1):.1f}"
        ))