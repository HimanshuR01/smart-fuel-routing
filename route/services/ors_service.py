import requests
import polyline


class ORSService:

    OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"

    @staticmethod
    def geocode_location(location):

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            headers={"User-Agent": "fuel-route-optimizer"},
            params={
                "q": location,
                "format": "json",
                "limit": 1
            },
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        if not data:
            raise Exception(f"Could not geocode location: {location}")

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])

        return lat, lon

    @staticmethod
    def get_route(start_location, end_location):

        start_lat, start_lon = ORSService.geocode_location(start_location)
        end_lat, end_lon = ORSService.geocode_location(end_location)

        url = (
            f"{ORSService.OSRM_ROUTE_URL}/"
            f"{start_lon},{start_lat};{end_lon},{end_lat}"
            "?overview=full&geometries=polyline"
        )

        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        if "routes" not in data or not data["routes"]:
            raise Exception("No route found.")

        route = data["routes"][0]

        distance_meters = route["distance"]
        encoded_polyline = route["geometry"]

        decoded_points = polyline.decode(encoded_polyline)

        return {
            "distance_miles": distance_meters * 0.000621371,
            "polyline": encoded_polyline,
            "decoded_points": decoded_points
        }
        