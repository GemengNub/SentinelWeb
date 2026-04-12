"""
API clients for external disaster data sources.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger
from app.core.config import settings
from app.schemas.event import USGSEarthquakeResponse, OpenWeatherResponse


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base


class BaseAPIClient:
    """Base class for API clients with retry logic."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = RetryConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "DisasterDetector/1.0",
                    "Accept": "application/json",
                },
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def geocode_location(self, location_name: str) -> Optional[tuple[float, float]]:
        """Geocode a location name to lat/lon using Nominatim."""
        if not location_name:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": location_name,
                        "format": "json",
                        "limit": 1,
                    },
                    headers={"User-Agent": "DisasterDetector/1.0"},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return (float(data[0]["lat"]), float(data[0]["lon"]))
        except Exception as e:
            logger.warning(f"Geocoding failed for '{location_name}': {e}")
        return None
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry."""
        client = await self._get_client()
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # If endpoint is empty, use base_url directly to avoid extra slash
                request_url = self.base_url if not endpoint else endpoint
                response = await client.request(
                    method=method,
                    url=request_url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code >= 500:
                    logger.warning(f"Server error {e.response.status_code} on attempt {attempt + 1}")
                elif e.response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = min(
                        self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt) * 2,
                        self.retry_config.max_delay,
                    )
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                raise
            
            if attempt < self.retry_config.max_retries:
                wait_time = min(
                    self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
                    self.retry_config.max_delay,
                )
                logger.info(f"Retrying in {wait_time}s (attempt {attempt + 1}/{self.retry_config.max_retries})")
                await asyncio.sleep(wait_time)
        
        raise last_exception or Exception("Max retries exceeded")


class USGSClient(BaseAPIClient):
    """Client for USGS Earthquake API."""
    
    def __init__(self):
        super().__init__(base_url=settings.USGS_API_BASE_URL)
    
    async def get_earthquakes(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_magnitude: float = 2.5,
        max_magnitude: Optional[float] = None,
        min_latitude: Optional[float] = None,
        max_latitude: Optional[float] = None,
        min_longitude: Optional[float] = None,
        max_longitude: Optional[float] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch earthquake data from USGS API."""
        
        params = {
            "format": "geojson",
            "starttime": (start_time or datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime": (end_time or datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S"),
            "minmagnitude": min_magnitude,
            "orderby": "time",
            "limit": limit,
        }
        
        if max_magnitude is not None:
            params["maxmagnitude"] = max_magnitude
        if min_latitude is not None:
            params["minlatitude"] = min_latitude
        if max_latitude is not None:
            params["maxlatitude"] = max_latitude
        if min_longitude is not None:
            params["minlongitude"] = min_longitude
        if max_longitude is not None:
            params["maxlongitude"] = max_longitude
        
        try:
            response = await self._request_with_retry("GET", "", params=params)
            data = response.json()
            
            features = data.get("features", [])
            logger.info(f"Fetched {len(features)} earthquakes from USGS")
            
            return self._normalize_earthquake_data(features)
            
        except Exception as e:
            logger.error(f"Failed to fetch USGS data: {str(e)}")
            return []

    def _normalize_earthquake_data(self, features: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize USGS earthquake data to standard format."""
        normalized = []
        
        for feature in features:
            try:
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])
                
                normalized.append({
                    "external_id": feature.get("id"),
                    "event_type": "EARTHQUAKE",
                    "source": "USGS",
                    "latitude": coords[1] if len(coords) > 1 else 0,
                    "longitude": coords[0] if len(coords) > 0 else 0,
                    "depth": coords[2] if len(coords) > 2 else None,
                    "magnitude": props.get("mag"),
                    "magnitude_type": props.get("magType"),
                    "intensity": props.get("mmi"),
                    "location_name": props.get("place"),
                    "place": props.get("place"),
                    "event_time": datetime.fromtimestamp(props.get("time", 0) / 1000) if props.get("time") else datetime.utcnow(),
                    "raw_data": feature,
                })
            except Exception as e:
                logger.warning(f"Failed to normalize earthquake feature: {str(e)}")
                continue

        return normalized


class OpenWeatherClient(BaseAPIClient):
    """Client for OpenWeather API."""
    
    def __init__(self):
        super().__init__(base_url=settings.OPENWEATHER_API_BASE_URL)
        self.api_key = settings.OPENWEATHER_API_KEY
    
    async def get_weather_data(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[Dict[str, Any]]:
        """Fetch weather data for a location."""
        
        if not self.api_key:
            logger.warning("OpenWeather API key not configured")
            return None
        
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }
        
        try:
            response = await self._request_with_retry("GET", "/weather", params=params)
            data = response.json()
            return self._normalize_weather_data(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenWeather data: {str(e)}")
            return None

    def _normalize_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenWeather data to standard format."""
        main = data.get("main", {})
        wind = data.get("wind", {})
        rain = data.get("rain", {})
        
        return {
            "external_id": str(data.get("id", "")),
            "event_type": "WEATHER",
            "source": "OpenWeather",
            "latitude": data.get("coord", {}).get("lat", 0),
            "longitude": data.get("coord", {}).get("lon", 0),
            "temperature": main.get("temp"),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "rainfall": rain.get("1h", 0.0),
            "location_name": data.get("name"),
            "event_time": datetime.utcnow(),
            "raw_data": data,
        }


class NOAAClient(BaseAPIClient):
    """Client for NOAA National Weather Service API."""
    
    def __init__(self):
        super().__init__(base_url=settings.NOAA_API_BASE_URL)
    
    async def get_alerts(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        state: Optional[str] = None,
        zone: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch weather alerts from NOAA NWS."""
        
        params = {}
        
        if latitude and longitude:
            params["point"] = f"{latitude},{longitude}"
        elif state:
            params["state"] = state
        elif zone:
            params["zone"] = zone
        else:
            params["status"] = "actual"
            params["message_type"] = "alert"
        
        try:
            response = await self._request_with_retry("GET", "/alerts", params=params)
            data = response.json()
            
            features = data.get("features", [])
            logger.info(f"Fetched {len(features)} alerts from NOAA")
            
            return await self._normalize_alert_data(features)
            
        except Exception as e:
            logger.error(f"Failed to fetch NOAA data: {str(e)}")
            return []
    
    async def _normalize_alert_data(self, features: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize NOAA alert data to standard format."""
        normalized = []
        
        for feature in features:
            try:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates") if geometry else None
                
                latitude = 0
                longitude = 0
                
                if coords:
                    if geometry.get("type") == "Point":
                        if isinstance(coords, list) and len(coords) >= 2:
                            longitude = coords[0]
                            latitude = coords[1]
                    elif geometry.get("type") in ("Polygon", "MultiPolygon"):
                        if isinstance(coords, list) and len(coords) > 0:
                            if geometry.get("type") == "Polygon":
                                outer_ring = coords[0]
                                if outer_ring and len(outer_ring) > 0:
                                    centroid_lon = sum(p[0] for p in outer_ring) / len(outer_ring)
                                    centroid_lat = sum(p[1] for p in outer_ring) / len(outer_ring)
                                    longitude = centroid_lon
                                    latitude = centroid_lat
                            elif geometry.get("type") == "MultiPolygon":
                                all_points = []
                                for polygon in coords:
                                    if polygon and len(polygon) > 0:
                                        all_points.extend(polygon[0])
                                if all_points:
                                    centroid_lon = sum(p[0] for p in all_points) / len(all_points)
                                    centroid_lat = sum(p[1] for p in all_points) / len(all_points)
                                    longitude = centroid_lon
                                    latitude = centroid_lat
                
                severity_map = {
                    "Extreme": "CRITICAL",
                    "Severe": "HIGH",
                    "Moderate": "MEDIUM",
                    "Minor": "LOW",
                }
                
                noaa_severity = props.get("severity", "Unknown")
                mapped_severity = severity_map.get(noaa_severity, "LOW")
                
                event_type = self._map_event_type(props.get("event", ""))
                
                description = props.get("description", "")
                if description and len(description) > 500:
                    description = description[:500] + "..."
                
                headline = props.get("headline", "")
                if headline and len(headline) > 255:
                    headline = headline[:255]
                
                area_desc = props.get("areaDesc", "Unknown")
                if area_desc and ";" in area_desc:
                    area_desc = area_desc.split(";")[0].strip()
                if area_desc and len(area_desc) > 255:
                    area_desc = area_desc[:255]
                
                if (latitude == 0 and longitude == 0) and area_desc and area_desc != "Unknown":
                    logger.info(f"Attempting to geocode location: {area_desc}")
                    coords = await self.geocode_location(area_desc)
                    if coords:
                        latitude, longitude = coords
                        logger.info(f"Geocoded {area_desc} to ({latitude}, {longitude})")
                    else:
                        logger.warning(f"Could not geocode location: {area_desc}, skipping alert")
                        continue
                
                if latitude == 0 and longitude == 0:
                    logger.warning(f"Alert without valid coordinates, skipping: {area_desc}")
                    continue
                
                normalized.append({
                    "external_id": feature.get("id"),
                    "event_type": event_type,
                    "source": "NOAA",
                    "latitude": latitude,
                    "longitude": longitude,
                    "magnitude": None,
                    "location_name": area_desc,
                    "place": area_desc,
                    "event_time": datetime.fromisoformat(props.get("sent", "").replace("Z", "+00:00")) if props.get("sent") else datetime.utcnow(),
                    "severity": mapped_severity,
                    "headline": headline,
                    "description": description,
                    "instruction": props.get("instruction"),
                    "raw_data": feature,
                })
            except Exception as e:
                logger.warning(f"Failed to normalize NOAA feature: {str(e)}")
                continue
        
        return normalized
    
    def _map_event_type(self, event: str) -> str:
        """Map NOAA event type to standard event type."""
        event = event.lower()
        if any(x in event for x in ["tornado", "severe thunderstorm", "wind"]):
            return "STORM"
        elif any(x in event for x in ["flood", "flash flood"]):
            return "FLOOD"
        elif any(x in event for x in ["hurricane", "tropical"]):
            return "HURRICANE"
        elif any(x in event for x in ["winter", "snow", "ice", "blizzard"]):
            return "WINTER_STORM"
        elif any(x in event for x in ["heat", "excessive heat"]):
            return "HEAT"
        elif any(x in event for x in ["fire", "red flag"]):
            return "WILDFIRE"
        else:
            return "WEATHER"


class PAGASAClient(BaseAPIClient):
    """Client for PAGASA (Philippines) API."""
    
    def __init__(self):
        super().__init__(base_url=settings.PAGASA_API_BASE_URL)
    
    async def get_earthquakes(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch earthquake data from PAGASA."""
        
        try:
            response = await self._request_with_retry(
                "GET",
                "/eqws/v1/json/earthquakes",
                params={"limit": limit},
            )
            data = response.json()
            
            earthquakes = data.get("earthquakes", [])
            logger.info(f"Fetched {len(earthquakes)} earthquakes from PAGASA")
            
            return self._normalize_earthquake_data(earthquakes)
            
        except Exception as e:
            logger.error(f"Failed to fetch PAGASA earthquake data: {str(e)}")
            return []
    
    async def get_weather_data(
        self,
        station_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch weather data from PAGASA."""
        
        try:
            endpoint = f"/synop/v1/json/stations/{station_id}" if station_id else "/synop/v1/json/stations"
            response = await self._request_with_retry("GET", endpoint)
            data = response.json()
            
            logger.info(f"Fetched weather data from PAGASA station {station_id or 'all'}")
            
            return self._normalize_weather_data(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch PAGASA weather data: {str(e)}")
            return None
    
    def _normalize_earthquake_data(self, earthquakes: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize PAGASA earthquake data."""
        normalized = []
        
        for eq in earthquakes:
            try:
                normalized.append({
                    "external_id": eq.get("earthquake_id"),
                    "event_type": "EARTHQUAKE",
                    "source": "PAGASA",
                    "latitude": float(eq.get("latitude", 0)),
                    "longitude": float(eq.get("longitude", 0)),
                    "depth": float(eq.get("depth", 0)) if eq.get("depth") else None,
                    "magnitude": float(eq.get("magnitude", 0)),
                    "location_name": eq.get("location"),
                    "place": eq.get("location"),
                    "event_time": datetime.fromisoformat(eq.get("date_time", "").replace("Z", "+00:00")) if eq.get("date_time") else datetime.utcnow(),
                    "raw_data": eq,
                })
            except Exception as e:
                logger.warning(f"Failed to normalize PAGASA earthquake: {str(e)}")
                continue
        
        return normalized
    
    def _normalize_weather_data(self, data: Dict) -> Dict[str, Any]:
        """Normalize PAGASA weather data."""
        station = data.get("station", {})
        observations = data.get("observations", [{}])[0] if data.get("observations") else {}
        
        return {
            "external_id": station.get("station_id"),
            "event_type": "WEATHER",
            "source": "PAGASA",
            "latitude": float(station.get("latitude", 0)),
            "longitude": float(station.get("longitude", 0)),
            "temperature": float(observations.get("air_temperature", 0)) if observations.get("air_temperature") else None,
            "humidity": float(observations.get("relative_humidity", 0)) if observations.get("relative_humidity") else None,
            "pressure": float(observations.get("station_pressure", 0)) if observations.get("station_pressure") else None,
            "wind_speed": float(observations.get("wind_speed", 0)) if observations.get("wind_speed") else None,
            "wind_direction": float(observations.get("wind_direction", 0)) if observations.get("wind_direction") else None,
            "rainfall": float(observations.get("rainfall", 0)) if observations.get("rainfall") else None,
            "location_name": station.get("station_name"),
            "event_time": datetime.utcnow(),
            "raw_data": data,
        }


class JMAClient(BaseAPIClient):
    """Client for Japan Meteorological Agency API."""
    
    def __init__(self):
        super().__init__(base_url=settings.JMA_API_BASE_URL)
    
    async def get_earthquakes(
        self,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Fetch earthquake data from JMA."""
        
        try:
            response = await self._request_with_retry(
                "GET",
                "/json/v1/list/earthquakes",
                params={"limit": limit},
            )
            data = response.json()
            
            earthquakes = data.get("earthquakes", [])
            logger.info(f"Fetched {len(earthquakes)} earthquakes from JMA")
            
            return self._normalize_earthquake_data(earthquakes)
            
        except Exception as e:
            logger.error(f"Failed to fetch JMA earthquake data: {str(e)}")
            return []
    
    async def get_warnings(
        self,
        area: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch weather warnings from JMA."""
        
        try:
            endpoint = f"/json/v1/list/warnings/{area}" if area else "/json/v1/list/warnings"
            response = await self._request_with_retry("GET", endpoint)
            data = response.json()
            
            warnings = data.get("warnings", [])
            logger.info(f"Fetched {len(warnings)} warnings from JMA")
            
            return self._normalize_warning_data(warnings)
            
        except Exception as e:
            logger.error(f"Failed to fetch JMA warnings: {str(e)}")
            return []
    
    def _normalize_earthquake_data(self, earthquakes: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize JMA earthquake data."""
        normalized = []
        
        for eq in earthquakes:
            try:
                hypocenter = eq.get("hypocenter", {})
                magnitude = eq.get("magnitude", {})
                
                normalized.append({
                    "external_id": eq.get("earthquake_id"),
                    "event_type": "EARTHQUAKE",
                    "source": "JMA",
                    "latitude": float(hypocenter.get("latitude", 0)),
                    "longitude": float(hypocenter.get("longitude", 0)),
                    "depth": float(hypocenter.get("depth", 0)) if hypocenter.get("depth") else None,
                    "magnitude": float(magnitude.get("value", 0)) if magnitude.get("value") else None,
                    "location_name": hypocenter.get("name"),
                    "place": hypocenter.get("name"),
                    "event_time": datetime.fromisoformat(eq.get("origin_time", "").replace("Z", "+00:00")) if eq.get("origin_time") else datetime.utcnow(),
                    "intensity": magnitude.get("scale"),
                    "raw_data": eq,
                })
            except Exception as e:
                logger.warning(f"Failed to normalize JMA earthquake: {str(e)}")
                continue
        
        return normalized
    
    def _normalize_warning_data(self, warnings: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize JMA warning data."""
        normalized = []
        
        for warning in warnings:
            try:
                severity_map = {
                    5: "CRITICAL",
                    4: "HIGH",
                    3: "MEDIUM",
                    2: "LOW",
                    1: "LOW",
                }
                
                level = warning.get("level", 1)
                mapped_severity = severity_map.get(level, "LOW")
                
                event_type = self._map_event_type(warning.get("phenomenon", ""))
                
                normalized.append({
                    "external_id": warning.get("warning_id"),
                    "event_type": event_type,
                    "source": "JMA",
                    "latitude": 0,
                    "longitude": 0,
                    "magnitude": None,
                    "location_name": warning.get("area", {}).get("name"),
                    "place": warning.get("area", {}).get("name"),
                    "event_time": datetime.fromisoformat(warning.get("issue_time", "").replace("Z", "+00:00")) if warning.get("issue_time") else datetime.utcnow(),
                    "severity": mapped_severity,
                    "headline": warning.get("title"),
                    "description": warning.get("text"),
                    "raw_data": warning,
                })
            except Exception as e:
                logger.warning(f"Failed to normalize JMA warning: {str(e)}")
                continue
        
        return normalized
    
    def _map_event_type(self, phenomenon: str) -> str:
        """Map JMA phenomenon to standard event type."""
        phenomenon = phenomenon.lower()
        if "earthquake" in phenomenon or "tsunami" in phenomenon:
            return "EARTHQUAKE"
        elif "typhoon" in phenomenon or "tropical" in phenomenon:
            return "HURRICANE"
        elif "flood" in phenomenon:
            return "FLOOD"
        elif "snow" in phenomenon or "blizzard" in phenomenon:
            return "WINTER_STORM"
        elif "heat" in phenomenon:
            return "HEAT"
        else:
            return "WEATHER"


class FIRMSClient(BaseAPIClient):
    """Client for NASA FIRMS (Fire Information Resource Management System) API."""
    
    def __init__(self):
        super().__init__(base_url="https://firms.modaps.eosdis.nasa.gov")
        self.api_key = settings.FIRMS_API_KEY
    
    async def get_fire_data(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        country: Optional[str] = None,
        days: int = 1,
    ) -> List[Dict[str, Any]]:
        """Fetch active fire data from NASA FIRMS."""
        
        if not self.api_key:
            logger.warning("FIRMS API key not configured")
            return []
        
        try:
            params = {
                "map_key": self.api_key,
                "temporal": days,
            }
            
            if latitude and longitude:
                bounds = f"{longitude-5},{latitude-5},{longitude+5},{latitude+5}"
                params["bounds"] = bounds
                params["source"] = "VIIRS_SNPP"
                response = await self._request_with_retry("GET", "/api/v2/area", params=params)
            else:
                country_code = self._country_to_code(country) if country else "USA"
                params["source"] = "VIIRS_SNPP"
                response = await self._request_with_retry("GET", f"/api/v2/country/{country_code}", params=params)
            
            lines = response.text.strip().split("\n")
            
            if len(lines) <= 1:
                logger.info("No fire data found from FIRMS")
                return []
            
            header = lines[0].split(",")
            fires = []
            
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                try:
                    values = line.split(",")
                    fire_data = dict(zip(header, values))
                    
                    lat = float(fire_data.get("latitude", 0))
                    lon = float(fire_data.get("longitude", 0))
                    
                    if lat == 0 and lon == 0:
                        continue
                    
                    brightness = float(fire_data.get("brightness", 0))
                    
                    severity = "LOW"
                    if brightness > 400:
                        severity = "CRITICAL"
                    elif brightness > 330:
                        severity = "HIGH"
                    elif brightness > 300:
                        severity = "MEDIUM"
                    
                    fires.append({
                        "external_id": f"firms-{fire_data.get('acq_date', '')}-{fire_data.get('acq_time', '')}",
                        "event_type": "WILDFIRE",
                        "source": "FIRMS",
                        "latitude": lat,
                        "longitude": lon,
                        "magnitude": brightness,
                        "location_name": fire_data.get("location", "Unknown"),
                        "place": fire_data.get("country", "Unknown"),
                        "event_time": datetime.strptime(
                            f"{fire_data.get('acq_date', '')} {fire_data.get('acq_time', '')}",
                            "%Y-%m-%d %H%M"
                        ) if fire_data.get("acq_date") and fire_data.get("acq_time") else datetime.utcnow(),
                        "severity": severity,
                        "brightness": brightness,
                        "scan": fire_data.get("scan"),
                        "track": fire_data.get("track"),
                        "raw_data": fire_data,
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse fire data line: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(fires)} fire events from FIRMS")
            return fires
            
        except Exception as e:
            logger.error(f"Failed to fetch FIRMS data: {str(e)}")
            return []
    
    def _country_to_code(self, country_name: Optional[str]) -> str:
        """Convert country name to FIRMS country code."""
        country_codes = {
            "US": "USA", "USA": "USA", "United States": "USA",
            "AU": "AUS", "Australia": "AUS",
            "BR": "BRA", "Brazil": "BRA",
            "CA": "CAN", "Canada": "CAN",
            "IN": "IND", "India": "IND",
            "ID": "IDN", "Indonesia": "IDN",
            "MX": "MEX", "Mexico": "MEX",
            "RU": "RUS", "Russia": "RUS",
            "ZA": "ZAF", "South Africa": "ZAF",
        }
        if country_name:
            return country_codes.get(country_name.upper()[:3], "USA")
        return "USA"


class APIClientFactory:
    """Factory for creating API clients."""
    
    _instances: Dict[str, BaseAPIClient] = {}
    
    @classmethod
    def get_usgs_client(cls) -> USGSClient:
        """Get USGS client instance."""
        if "usgs" not in cls._instances:
            cls._instances["usgs"] = USGSClient()
        return cls._instances["usgs"]
    
    @classmethod
    def get_weather_client(cls) -> OpenWeatherClient:
        """Get OpenWeather client instance."""
        if "weather" not in cls._instances:
            cls._instances["weather"] = OpenWeatherClient()
        return cls._instances["weather"]
    
    @classmethod
    def get_noaa_client(cls) -> NOAAClient:
        """Get NOAA client instance."""
        if "noaa" not in cls._instances:
            cls._instances["noaa"] = NOAAClient()
        return cls._instances["noaa"]
    
    @classmethod
    def get_pagasa_client(cls) -> PAGASAClient:
        """Get PAGASA client instance."""
        if "pagasa" not in cls._instances:
            cls._instances["pagasa"] = PAGASAClient()
        return cls._instances["pagasa"]
    
    @classmethod
    def get_jma_client(cls) -> JMAClient:
        """Get JMA client instance."""
        if "jma" not in cls._instances:
            cls._instances["jma"] = JMAClient()
        return cls._instances["jma"]
    
    @classmethod
    def get_firms_client(cls) -> FIRMSClient:
        """Get FIRMS client instance."""
        if "firms" not in cls._instances:
            cls._instances["firms"] = FIRMSClient()
        return cls._instances["firms"]
    
    @classmethod
    async def close_all(cls):
        """Close all client instances."""
        for client in cls._instances.values():
            await client.close()
        cls._instances.clear()
