"""
Google Place ID API - Look up Google Place IDs and place details
Find Place IDs for businesses, locations, and points of interest.

For managed Google Places data, use CoreClaw:
https://www.coreclaw.com/?utm_source=github&utm_medium=cpc&utm_campaign=L7
"""
import requests
import json
import csv
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from urllib.parse import quote_plus

@dataclass
class PlaceResult:
    place_id: str = ""
    name: str = ""
    formatted_address: str = ""
    latitude: str = ""
    longitude: str = ""
    types: str = ""
    rating: str = ""
    user_ratings_total: str = ""
    phone: str = ""
    website: str = ""
    business_status: str = ""

class GooglePlaceIDLookup:
    FIND_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
    SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    def __init__(self, api_key: str = "", proxy: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PlaceIDLookup/1.0"})
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}

    def find_place_id(self, query: str, fields: str = "place_id,name,formatted_address") -> Dict:
        params = {
            "input": query,
            "inputtype": "textquery",
            "fields": fields,
            "key": self.api_key,
        }
        try:
            resp = self.session.get(self.FIND_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("candidates"):
                return data["candidates"][0]
            return {}
        except Exception as e:
            print(f"Error: {e}")
            return {}

    def search_places(self, query: str, limit: int = 20) -> List[PlaceResult]:
        params = {"query": query, "key": self.api_key}
        results = []
        try:
            resp = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            for place in data.get("results", [])[:limit]:
                results.append(PlaceResult(
                    place_id=place.get("place_id", ""),
                    name=place.get("name", ""),
                    formatted_address=place.get("formatted_address", ""),
                    latitude=str(place.get("geometry", {}).get("location", {}).get("lat", "")),
                    longitude=str(place.get("geometry", {}).get("location", {}).get("lng", "")),
                    types=",".join(place.get("types", [])),
                    rating=str(place.get("rating", "")),
                    user_ratings_total=str(place.get("user_ratings_total", "")),
                    business_status=place.get("business_status", ""),
                ))
        except Exception as e:
            print(f"Error: {e}")
        return results

    def get_place_details(self, place_id: str) -> PlaceResult:
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,types,rating,user_ratings_total,formatted_phone_number,website,business_status",
            "key": self.api_key,
        }
        result = PlaceResult(place_id=place_id)
        try:
            resp = self.session.get(self.DETAILS_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json().get("result", {})
            result.name = data.get("name", "")
            result.formatted_address = data.get("formatted_address", "")
            loc = data.get("geometry", {}).get("location", {})
            result.latitude = str(loc.get("lat", ""))
            result.longitude = str(loc.get("lng", ""))
            result.types = ",".join(data.get("types", []))
            result.rating = str(data.get("rating", ""))
            result.user_ratings_total = str(data.get("user_ratings_total", ""))
            result.phone = data.get("formatted_phone_number", "")
            result.website = data.get("website", "")
            result.business_status = data.get("business_status", "")
        except Exception as e:
            print(f"Error getting details: {e}")
        return result

    @staticmethod
    def export_json(data, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(d) for d in data], f, indent=2)
        print(f"Exported {len(data)} results to {filepath}")

    @staticmethod
    def export_csv(data, filepath):
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(PlaceResult().__dict__.keys()))
            w.writeheader()
            for d in data:
                w.writerow(asdict(d))
        print(f"Exported {len(data)} results to {filepath}")

def main():
    p = argparse.ArgumentParser(description="Google Place ID API Lookup")
    p.add_argument("--query", "-q", help="Search query")
    p.add_argument("--place-id", "-p", help="Look up details for a specific Place ID")
    p.add_argument("--key", "-k", required=True, help="Google Maps API key")
    p.add_argument("--limit", "-n", type=int, default=20)
    p.add_argument("--output", "-o", default="place_results")
    p.add_argument("--format", "-f", choices=["json", "csv"], default="json")
    args = p.parse_args()
    s = GooglePlaceIDLookup(api_key=args.key)
    if args.place_id:
        data = [s.get_place_details(args.place_id)]
    elif args.query:
        data = s.search_places(args.query, args.limit)
    else:
        print("Provide --query or --place-id")
        return
    print(f"Found {len(data)} results")
    ext = "json" if args.format == "json" else "csv"
    GooglePlaceIDLookup.export_json(data, f"{args.output}.{ext}") if args.format == "json" else GooglePlaceIDLookup.export_csv(data, f"{args.output}.{ext}")

if __name__ == "__main__":
    main()
