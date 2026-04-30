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
            return self._get_mock_earthquake_data()
    
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
    
    def _get_mock_earthquake_data(self) -> List[Dict[str, Any]]:
        """Return mock earthquake data when API fails."""
        logger.warning("Using mock earthquake data")
        return [
            {
                "external_id": "mock-1",
                "event_type": "EARTHQUAKE",
                "source": "MOCK",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "depth": 10.0,
                "magnitude": 4.5,
                "magnitude_type": "ml",
                "location_name": "San Francisco, CA",
                "place": "San Francisco, CA",
                "event_time": datetime.utcnow(),
                "raw_data": {},
            },
            {
                "external_id": "mock-2",
                "event_type": "EARTHQUAKE",
                "source": "MOCK",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "depth": 15.0,
                "magnitude": 6.2,
                "magnitude_type": "ml",
                "location_name": "Los Angeles, CA",
                "place": "Los Angeles, CA",
                "event_time": datetime.utcnow(),
                "raw_data": {},
            },
        ]


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
            logger.warning("OpenWeather API key not configured, using mock data")
            return self._get_mock_weather_data(latitude, longitude)
        
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
            return self._get_mock_weather_data(latitude, longitude)
    
    def _normalize_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize OpenWeather data to standard format."""
        main = data.get("main", {})
        wind = data.get("wind", {})
        rain = data.get("rain", {})
        coord = data.get("coord", {})
        latitude = coord.get("lat", 0)
        longitude = coord.get("lon", 0)
        city_id = data.get("id")
        observation_ts = data.get("dt")

        if city_id and observation_ts:
            external_id = f"ow-{city_id}-{observation_ts}"
        elif city_id:
            external_id = f"ow-{city_id}-{int(datetime.utcnow().timestamp())}"
        else:
            external_id = (
                f"ow-{latitude:.4f}-{longitude:.4f}-{int(datetime.utcnow().timestamp())}"
            )

        event_time = (
            datetime.fromtimestamp(observation_ts)
            if observation_ts
            else datetime.utcnow()
        )
        
        return {
            "external_id": external_id,
            "event_type": "WEATHER",
            "source": "OpenWeather",
            "latitude": latitude,
            "longitude": longitude,
            "temperature": main.get("temp"),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "rainfall": rain.get("1h", 0.0),
            "location_name": data.get("name"),
            "event_time": event_time,
            "raw_data": data,
        }
    
    def _get_mock_weather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Return mock weather data when API fails."""
        logger.warning("Using mock weather data")
        now = datetime.utcnow()
        return {
            "external_id": (
                f"mock-weather-{latitude:.4f}-{longitude:.4f}-{int(now.timestamp())}"
            ),
            "event_type": "WEATHER",
            "source": "MOCK",
            "latitude": latitude,
            "longitude": longitude,
            "temperature": 25.0,
            "humidity": 60.0,
            "pressure": 1013.25,
            "wind_speed": 15.0,
            "wind_direction": 180.0,
            "rainfall": 0.0,
            "location_name": "Mock Location",
            "event_time": now,
            "raw_data": {},
        }


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
    async def close_all(cls):
        """Close all client instances."""
        for client in cls._instances.values():
            await client.close()
        cls._instances.clear()
