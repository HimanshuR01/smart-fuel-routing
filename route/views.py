import hashlib
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from route.models import RouteRequest
from route.serializers import RouteOptimizationSerializer
from route.services.ors_service import ORSService
from route.services.optimization_service import RouteOptimizationService


class RouteOptimizationAPIView(APIView):

    def post(self, request):
        serializer = RouteOptimizationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start_location = serializer.validated_data["start_location"]
        end_location = serializer.validated_data["end_location"]

        mpg = serializer.validated_data.get("vehicle_mpg", 10)
        tank_capacity = serializer.validated_data.get("tank_capacity", 50)
        initial_fuel = serializer.validated_data.get("initial_fuel", tank_capacity)

        if initial_fuel <= 0:
            return Response(
                {"error": "Vehicle cannot start with zero fuel."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            route_data = ORSService.get_route(start_location, end_location)
            total_distance = route_data["distance_miles"]

            stops, total_cost, total_fuel_used, fuel_remaining = \
                RouteOptimizationService.calculate_realistic_stops(
                    total_distance=total_distance,
                    mpg=mpg,
                    tank_capacity=tank_capacity,
                    initial_fuel=initial_fuel,
                    route_points=route_data["decoded_points"]
                )

            return Response({
                "start_location": start_location,
                "end_location": end_location,
                "total_distance_miles": round(total_distance, 2),
                "total_stops": len(stops),
                "vehicle_mpg": mpg,
                "tank_capacity": tank_capacity,
                "initial_fuel": initial_fuel,
                "total_fuel_used": round(float(total_fuel_used), 2),
                "total_fuel_cost": round(float(total_cost), 2),
                "fuel_remaining_at_destination": round(float(fuel_remaining), 2),
                "fuel_stops": stops,
                "route_polyline": route_data["polyline"]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Handle GET requests - API documentation
        """
        return Response({
            "message": "Fuel Route Optimizer API",
            "version": "1.0",
            "status": "operational",
            "endpoint": "/api/optimize-route/",
            "method": "POST",
            "parameters": {
                "required": {
                    "start_location": "string - Starting city/address (e.g., 'Dallas, Texas')",
                    "end_location": "string - Destination city/address (e.g., 'Phoenix, Arizona')"
                },
                "optional": {
                    "vehicle_mpg": "float - Miles per gallon (default: 10)",
                    "tank_capacity": "float - Tank capacity in gallons (default: 50)",
                    "initial_fuel": "float - Starting fuel in gallons (default: tank_capacity)"
                }
            },
            "response_fields": {
                "start_location": "Starting location",
                "end_location": "Destination location",
                "total_distance_miles": "Total trip distance in miles",
                "total_stops": "Number of fuel stops",
                "vehicle_mpg": "Vehicle fuel efficiency",
                "tank_capacity": "Tank size in gallons",
                "initial_fuel": "Starting fuel amount",
                "total_fuel_used": "Total fuel consumed",
                "total_fuel_cost": "Total cost of fuel",
                "fuel_remaining_at_destination": "Fuel left at destination",
                "fuel_stops": "Array of fuel stop details",
                "route_polyline": "Encoded route polyline for mapping"
            },
            "example_request": {
                "start_location": "Dallas, Texas",
                "end_location": "Phoenix, Arizona",
                "vehicle_mpg": 10,
                "tank_capacity": 50,
                "initial_fuel": 20
            },
            "fuel_stop_fields": {
                "stop_order": "Stop sequence number",
                "station_name": "Fuel station name",
                "city": "Station city",
                "state": "Station state",
                "latitude": "Station latitude",
                "longitude": "Station longitude",
                "price_per_gallon": "Fuel price at this station",
                "miles_from_start": "Distance from trip start",
                "distance_travelled_since_last_stop": "Miles since last stop",
                "fuel_used_before_stop": "Fuel consumed to reach this stop",
                "fuel_remaining_on_arrival": "Fuel left when arriving",
                "gallons_refilled": "Amount refueled at this stop",
                "fuel_after_refill": "Fuel level after refueling",
                "segment_cost": "Cost of this refuel",
                "cumulative_cost": "Total cost up to this stop",
                "distance_from_route_miles": "Station's distance from route"
            }
        }, status=status.HTTP_200_OK)