import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from route.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel stations from CSV"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                FuelStation.objects.get_or_create(
                    opis_id=int(row['OPIS Truckstop ID']),
                    defaults={
                        'name': row['Truckstop Name'],
                        'address': row['Address'],
                        'city': row['City'],
                        'state': row['State'],
                        'rack_id': int(row['Rack ID']) if row['Rack ID'] else None,
                        'retail_price': Decimal(row['Retail Price']),
                    }
                )

        self.stdout.write(self.style.SUCCESS("Fuel stations imported successfully"))
        