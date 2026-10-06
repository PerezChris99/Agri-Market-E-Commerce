import json
from django.core.management.base import BaseCommand
from store.services.national import readiness_snapshot


class Command(BaseCommand):
    help = "Report application readiness checks as JSON."
    requires_migrations_checks = True

    def handle(self, *args, **options):
        snapshot = readiness_snapshot()
        self.stdout.write(json.dumps(snapshot, indent=2, sort_keys=True))
        if not snapshot["ready"]:
            raise SystemExit(1)
