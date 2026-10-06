from django.core.management.base import BaseCommand
from store.services.national import issue_api_key


class Command(BaseCommand):
    help = "Create an institutional API client and print the secret once."

    def add_arguments(self, parser):
        parser.add_argument("name")
        parser.add_argument("--scope", action="append", default=None)

    def handle(self, *args, **options):
        client, raw = issue_api_key(name=options["name"], scopes=options["scope"])
        self.stdout.write(self.style.SUCCESS("Client: " + client.name))
        self.stdout.write("Key prefix: " + client.key_prefix)
        self.stdout.write("API key (store securely; it cannot be recovered): " + raw)
