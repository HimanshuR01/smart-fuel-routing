import time
import hashlib
import requests

from django.core.management.base import BaseCommand
from django.db import transaction

from route.models import FuelStation, RouteRequest


class Command(BaseCommand):
    help = "Prepare system data: populate route hashes and geocode fuel stations using Nominatim"

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    REQUEST_DELAY = 1  # 1 request per second (respect policy)
    MAX_RETRIES = 3

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.SUCCESS("Starting data preparation...\n"))

        self.populate_route_hashes()
        self.geocode_stations()

        self.stdout.write(self.style.SUCCESS("\nData preparation completed."))

    # -----------------------------
    # Step 1: Populate Route Hashes
    # -----------------------------
    def populate_route_hashes(self):
        self.stdout.write("Populating route_hash for existing RouteRequest rows...")

        routes = RouteRequest.objects.filter(route_hash__isnull=True)
        count = routes.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("All routes already have route_hash.\n"))
            return

        updated = 0

        for route in routes:
            hash_value = hashlib.sha256(
                f"{route.start_location.strip().lower()}-{route.end_location.strip().lower()}".encode()
            ).hexdigest()

            route.route_hash = hash_value
            route.save(update_fields=["route_hash"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Route hash populated for {updated}/{count} routes.\n")
        )

    # -----------------------------
    # Step 2: Geocode Fuel Stations
    # -----------------------------
    def geocode_stations(self):
        self.stdout.write("Starting geocoding using Nominatim...\n")

        stations = FuelStation.objects.filter(is_geocoded=False)
        total = stations.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("All stations are already geocoded.\n"))
            return

        updated_count = 0
        failed_count = 0

        headers = {
            "User-Agent": "fuel-route-optimizer-app"
        }

        for index, station in enumerate(stations, start=1):

            # query = f"{station.address.strip()}, {station.city.strip()}, {station.state.strip()}, USA"
            query = f"{station.city.strip()}, {station.state.strip()}, USA"

            for attempt in range(self.MAX_RETRIES):

                try:
                    response = requests.get(
                        self.NOMINATIM_URL,
                        headers=headers,
                        params={
                            "q": query,
                            "format": "json",
                            "limit": 1
                        },
                        timeout=15
                    )

                    if response.status_code == 429:
                        wait_time = 5 * (attempt + 1)
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{index}/{total}] Rate limit hit. Sleeping {wait_time}s..."
                            )
                        )
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    if data:
                        station.latitude = float(data[0]["lat"])
                        station.longitude = float(data[0]["lon"])
                        station.is_geocoded = True

                        station.save(update_fields=[
                            "latitude",
                            "longitude",
                            "is_geocoded"
                        ])

                        updated_count += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"[{index}/{total}] ✔ {station.name}"
                            )
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{index}/{total}] ✖ No result: {station.name}"
                            )
                        )

                    break  # Exit retry loop

                except requests.exceptions.Timeout:
                    if attempt == self.MAX_RETRIES - 1:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"[{index}/{total}] Timeout: {station.name}"
                            )
                        )
                    else:
                        time.sleep(2)

                except requests.exceptions.RequestException as e:
                    if attempt == self.MAX_RETRIES - 1:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"[{index}/{total}] API Error: {station.name} | {str(e)}"
                            )
                        )
                    else:
                        time.sleep(2)

            time.sleep(self.REQUEST_DELAY)

        self.stdout.write("\n")
        self.stdout.write(
            self.style.SUCCESS(
                f"Geocoding completed: {updated_count} updated, {failed_count} failed."
            )
        )
