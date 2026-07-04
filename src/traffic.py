"""교통 결합: 출발지/도착지를 받아 자차(TMAP)/대중교통(ODsay) 소요시간을 조회.
좌표 변환(지오코딩)은 TMAP POI 검색 하나로 통일해서 자차·대중교통 둘 다에 재사용.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

TMAP_APP_KEY = os.environ["TMAP_APP_KEY"]
ODSAY_API_KEY = os.environ["ODSAY_API_KEY"]


def geocode(place: str) -> tuple[float, float]:
    """장소명 -> (경도, 위도). TMAP POI 검색 사용."""
    resp = requests.get(
        "https://apis.openapi.sk.com/tmap/pois",
        params={"version": 1, "searchKeyword": place, "resCoordType": "WGS84GEO", "count": 1},
        headers={"appKey": TMAP_APP_KEY},
        timeout=5,
    )
    resp.raise_for_status()
    poi = resp.json()["searchPoiInfo"]["pois"]["poi"][0]
    return float(poi["noorLon"]), float(poi["noorLat"])


def get_driving_eta(origin: str, destination: str) -> dict:
    """자차 소요시간(분)·거리(km). TMAP 자동차 길찾기."""
    start_lon, start_lat = geocode(origin)
    end_lon, end_lat = geocode(destination)
    resp = requests.post(
        "https://apis.openapi.sk.com/tmap/routes?version=1",
        json={
            "startX": str(start_lon), "startY": str(start_lat),
            "endX": str(end_lon), "endY": str(end_lat),
            "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO", "searchOption": "0",
        },
        headers={"appKey": TMAP_APP_KEY, "Content-Type": "application/json"},
        timeout=5,
    )
    resp.raise_for_status()
    props = resp.json()["features"][0]["properties"]
    return {
        "mode": "driving",
        "minutes": round(props["totalTime"] / 60),
        "distance_km": round(props["totalDistance"] / 1000, 1),
    }


def get_transit_eta(origin: str, destination: str) -> dict:
    """대중교통 소요시간(분)·환승횟수. ODsay 대중교통 길찾기."""
    start_lon, start_lat = geocode(origin)
    end_lon, end_lat = geocode(destination)
    resp = requests.get(
        "https://api.odsay.com/v1/api/searchPubTransPathT",
        params={"SX": start_lon, "SY": start_lat, "EX": end_lon, "EY": end_lat, "apiKey": ODSAY_API_KEY},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    if "result" not in data or not data["result"].get("path"):
        return {"mode": "transit", "minutes": None, "transfers": None, "error": "경로 없음"}
    best = min(data["result"]["path"], key=lambda p: p["info"]["totalTime"])
    return {
        "mode": "transit",
        "minutes": best["info"]["totalTime"],
        "transfers": best["info"]["busTransitCount"] + best["info"]["subwayTransitCount"],
    }


if __name__ == "__main__":
    print(get_driving_eta("강남역", "서울역"))
    print(get_transit_eta("강남역", "서울역"))
