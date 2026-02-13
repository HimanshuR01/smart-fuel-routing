from django.db import models
from decimal import Decimal


class FuelStation(models.Model):
    opis_id = models.IntegerField(unique=True)

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)

    rack_id = models.IntegerField(null=True, blank=True)

    retail_price = models.DecimalField(max_digits=6, decimal_places=3)

    latitude = models.FloatField(null=True, blank=True, db_index=True)
    longitude = models.FloatField(null=True, blank=True, db_index=True)

    is_geocoded = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["retail_price"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"
    
class RouteRequest(models.Model):
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)

    route_hash = models.CharField(max_length=64, db_index=True, null=True, blank=True)

    total_distance_miles = models.FloatField()

    total_fuel_cost = models.DecimalField(max_digits=10, decimal_places=2)

    vehicle_mpg = models.FloatField(default=10)
    vehicle_range_miles = models.FloatField(default=500)

    route_polyline = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["route_hash"]),
        ]

    def __str__(self):
        return f"{self.start_location} → {self.end_location}"

class FuelStop(models.Model):
    route = models.ForeignKey(
        RouteRequest,
        on_delete=models.CASCADE,
        related_name="fuel_stops"
    )

    station = models.ForeignKey(
        FuelStation,
        on_delete=models.CASCADE
    )

    stop_order = models.IntegerField()

    miles_from_start = models.FloatField()

    gallons_filled = models.FloatField()

    cost = models.DecimalField(max_digits=8, decimal_places=2)

    distance_from_route_miles = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["route", "stop_order"],
                name="unique_stop_order_per_route"
            )
        ]

    def __str__(self):
        return f"Stop {self.stop_order} - {self.station.name}"
    