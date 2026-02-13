from rest_framework import serializers
from route.models import RouteRequest, FuelStop


class RouteOptimizationSerializer(serializers.Serializer):
    start_location = serializers.CharField(max_length=255)
    end_location = serializers.CharField(max_length=255)

    vehicle_mpg = serializers.FloatField(required=False, default=10)
    tank_capacity = serializers.FloatField(required=False, default=50)
    initial_fuel = serializers.FloatField(required=False)

    def validate(self, data):
        start = data["start_location"].strip()
        end = data["end_location"].strip()

        if start.lower() == end.lower():
            raise serializers.ValidationError(
                "Start and end locations cannot be the same."
            )

        data["start_location"] = start
        data["end_location"] = end

        if "initial_fuel" not in data:
            data["initial_fuel"] = data.get("tank_capacity", 50)

        return data


class FuelStopSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source="station.name", read_only=True)
    city = serializers.CharField(source="station.city", read_only=True)
    state = serializers.CharField(source="station.state", read_only=True)

    price_per_gallon = serializers.DecimalField(
        source="station.retail_price",
        max_digits=6,
        decimal_places=3,
        read_only=True
    )

    latitude = serializers.FloatField(source="station.latitude", read_only=True)
    longitude = serializers.FloatField(source="station.longitude", read_only=True)

    class Meta:
        model = FuelStop
        fields = [
            "stop_order",
            "station_name",
            "city",
            "state",
            "latitude",
            "longitude",
            "price_per_gallon",
            "gallons_filled",
            "cost",
            "miles_from_start",
            "distance_from_route_miles",
        ]


class RouteResponseSerializer(serializers.ModelSerializer):
    fuel_stops = FuelStopSerializer(many=True, read_only=True)

    class Meta:
        model = RouteRequest
        fields = [
            "start_location",
            "end_location",
            "total_distance_miles",
            "total_fuel_cost",
            "vehicle_mpg",
            "vehicle_range_miles",
            "route_polyline",
            "fuel_stops",
        ]
