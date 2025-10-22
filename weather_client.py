from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


class OpenWeatherClient:
    """
    간단한 OpenWeather API 클라이언트.

    - API 키는 인자로 전달하거나, 환경변수 OPENWEATHER_API_KEY에서 읽습니다.
    - 현재 날씨 조회(get_current_weather)만 기본 제공.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.openweathermap.org/data/2.5") -> None:
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeather API 키가 없습니다. st.secrets 또는 환경변수를 설정하세요.")
        self.base_url = base_url.rstrip("/")

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        with requests.Session() as s:
            resp = s.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            try:
                data = resp.json()
                msg = data.get("message", resp.text)
            except Exception:
                msg = resp.text
            raise RuntimeError(f"OpenWeather API 오류 ({resp.status_code}): {msg}")
        return resp.json()

    def get_current_weather(self, city: str, units: str = "metric", lang: str = "kr") -> Dict[str, Any]:
        """
        현재 날씨를 반환합니다.

        - city: 도시명 (예: "Seoul" 또는 "서울")
        - units: "metric"(섭씨) 또는 "imperial"(화씨)
        - lang: 언어 코드 (예: "kr", "en")
        """
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units,
            "lang": lang,
        }
        return self._request("weather", params)

    # --- 추가: 지오코딩 및 좌표 기반 조회 ---
    def geocode(self, query: str, limit: int = 1, lang: str = "kr") -> list[Dict[str, Any]]:
        """도시명을 좌표로 변환 (Direct Geocoding).

        https://openweathermap.org/api/geocoding-api
        """
        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {
            "q": query,
            "limit": limit,
            "appid": self.api_key,
        }
        if lang:
            params["lang"] = lang
        with requests.Session() as s:
            resp = s.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            try:
                data = resp.json()
                msg = data.get("message", resp.text)
            except Exception:
                msg = resp.text
            raise RuntimeError(f"OpenWeather Geocoding 오류 ({resp.status_code}): {msg}")
        return resp.json()

    def resolve_city_to_coords(self, city: str, lang: str = "kr") -> Optional[Dict[str, Any]]:
        results = self.geocode(city, limit=1, lang=lang)
        if not results:
            return None
        return results[0]

    def get_current_weather_by_coords(self, lat: float, lon: float, units: str = "metric", lang: str = "kr") -> Dict[str, Any]:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": units,
            "lang": lang,
        }
        return self._request("weather", params)

    def get_forecast_by_coords(self, lat: float, lon: float, units: str = "metric", lang: str = "kr") -> Dict[str, Any]:
        """
        5일 / 3시간 간격 예보를 반환합니다.
        참고: 무료 플랜에서 사용 가능한 /data/2.5/forecast 엔드포인트를 사용합니다.
        """
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": units,
            "lang": lang,
        }
        # forecast는 base_url 경로 하위
        return self._request("forecast", params)


def choose_units_for_country(country_code: Optional[str]) -> str:
    """국가 코드 기준으로 단위를 선택합니다.

    - 미국(US), 라이베리아(LR), 미얀마(MM)만 imperial, 그 외는 metric
    """
    if not country_code:
        return "metric"
    return "imperial" if country_code.upper() in {"US", "LR", "MM"} else "metric"


def get_icon_url(icon_code: str) -> str:
    """OpenWeather 아이콘 PNG URL 반환 (@2x)."""
    return f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
