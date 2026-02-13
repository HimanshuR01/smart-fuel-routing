import math
from decimal import Decimal
from route.models import FuelStation


class RouteOptimizationService:

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 3959  # miles
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        return 2 * R * math.asin(math.sqrt(a))

    @staticmethod
    def get_candidate_stations(route_points):

        lats = [pt[0] for pt in route_points]
        lons = [pt[1] for pt in route_points]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        return FuelStation.objects.filter(
            is_geocoded=True,
            latitude__gte=min_lat - 1,
            latitude__lte=max_lat + 1,
            longitude__gte=min_lon - 1,
            longitude__lte=max_lon + 1
        )

    @staticmethod
    def calculate_realistic_stops(
        total_distance,
        mpg,
        tank_capacity,
        initial_fuel,
        route_points
    ):
        stops = []
        total_cost = Decimal("0.00")
        total_fuel_used = Decimal("0.00")

        current_position = 0.0
        current_fuel = Decimal(str(initial_fuel))
        stop_order = 1

        max_range = Decimal(str(mpg)) * Decimal(str(tank_capacity))

        candidate_stations = RouteOptimizationService.get_candidate_stations(route_points)

        if not candidate_stations.exists():
            return [], Decimal("0.00"), Decimal("0.00"), current_fuel

        # Precompute cumulative route distances
        cumulative_distances = [0.0]
        total_route_distance = 0.0

        for i in range(len(route_points) - 1):
            lat1, lon1 = route_points[i]
            lat2, lon2 = route_points[i + 1]

            segment = RouteOptimizationService.haversine(lat1, lon1, lat2, lon2)
            total_route_distance += segment
            cumulative_distances.append(total_route_distance)

        while current_position < total_distance:

            remaining_distance = Decimal(str(total_distance - current_position))
            reachable_miles = current_fuel * Decimal(str(mpg))

            # If destination reachable, finish trip
            if reachable_miles >= remaining_distance:
                total_fuel_used += remaining_distance / Decimal(str(mpg))
                current_fuel -= remaining_distance / Decimal(str(mpg))
                break

            reachable_limit = float(current_position + float(reachable_miles))

            # Find reachable stations
            reachable_stations = []

            for idx, mile_marker in enumerate(cumulative_distances):
                if current_position < mile_marker <= reachable_limit:
                    lat, lon = route_points[idx]

                    for station in candidate_stations:
                        distance = RouteOptimizationService.haversine(
                            lat, lon,
                            station.latitude,
                            station.longitude
                        )

                        if distance <= 20:  # 20 mile deviation
                            reachable_stations.append(
                                (station, mile_marker, distance)
                            )

            if not reachable_stations:
                raise Exception("Route infeasible: no fuel station within reachable range.")

            # Choose cheapest station
            reachable_stations.sort(key=lambda x: (x[0].retail_price, -x[1]))
            station, station_mile, deviation = reachable_stations[0]

            distance_to_station = Decimal(str(station_mile - current_position))
            fuel_used = distance_to_station / Decimal(str(mpg))

            current_fuel -= fuel_used
            total_fuel_used += fuel_used
            current_position = float(station_mile)

            remaining_distance = Decimal(str(total_distance - current_position))

            # Refill logic
            if remaining_distance > max_range:
                refill_amount = Decimal(str(tank_capacity)) - current_fuel
            else:
                required_fuel = remaining_distance / Decimal(str(mpg))
                refill_amount = required_fuel - current_fuel
                if refill_amount < 0:
                    refill_amount = Decimal("0.00")

            refill_cost = refill_amount * station.retail_price

            current_fuel += refill_amount
            total_cost += refill_cost

            stops.append({
                "stop_order": stop_order,
                "station_name": station.name,
                "city": station.city,
                "state": station.state,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "price_per_gallon": float(station.retail_price),

                "miles_from_start": float(round(current_position, 2)),
                "distance_travelled_since_last_stop": float(round(distance_to_station, 2)),

                "fuel_used_before_stop": float(round(fuel_used, 2)),
                "fuel_remaining_on_arrival": float(round(current_fuel - refill_amount, 2)),

                "gallons_refilled": float(round(refill_amount, 2)),
                "fuel_after_refill": float(round(current_fuel, 2)),

                "segment_cost": float(round(refill_cost, 2)),
                "cumulative_cost": float(round(total_cost, 2)),

                "distance_from_route_miles": float(round(deviation, 2))
            })

            stop_order += 1

        return stops, total_cost, total_fuel_used, current_fuel
