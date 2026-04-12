"""
Risk assessment engine for evaluating disaster severity.
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger
from app.core.config import settings


class SeverityLevel(str, Enum):
    """Alert severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskScore:
    """Container for risk assessment results."""
    
    def __init__(
        self,
        severity: SeverityLevel,
        score: float,
        factors: Dict[str, float],
        description: str,
    ):
        self.severity = severity
        self.score = score
        self.factors = factors
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "score": self.score,
            "factors": self.factors,
            "description": self.description,
        }


class RiskStrategy(ABC):
    """Abstract base class for risk assessment strategies."""
    
    @abstractmethod
    def assess(self, event_data: Dict[str, Any]) -> RiskScore:
        """Assess risk from event data."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Check if this strategy can handle the event type."""
        pass


class EarthquakeRiskStrategy(RiskStrategy):
    """Risk assessment strategy for earthquakes."""
    
    def can_handle(self, event_type: str) -> bool:
        return event_type.upper() == "EARTHQUAKE"
    
    def assess(self, event_data: Dict[str, Any]) -> RiskScore:
        """Assess earthquake risk based on magnitude and depth."""
        magnitude = event_data.get("magnitude", 0) or 0
        depth = event_data.get("depth", 0) or 0
        
        factors = {}
        score = 0.0
        
        # Magnitude scoring (0-50 points)
        if magnitude >= settings.EARTHQUAKE_CRITICAL_THRESHOLD:
            magnitude_score = 50.0
        elif magnitude >= settings.EARTHQUAKE_HIGH_THRESHOLD:
            magnitude_score = 40.0 + (magnitude - settings.EARTHQUAKE_HIGH_THRESHOLD) * 2.0
        elif magnitude >= settings.EARTHQUAKE_MEDIUM_THRESHOLD:
            magnitude_score = 25.0 + (magnitude - settings.EARTHQUAKE_MEDIUM_THRESHOLD) * 3.0
        elif magnitude >= settings.EARTHQUAKE_LOW_THRESHOLD:
            magnitude_score = 10.0 + (magnitude - settings.EARTHQUAKE_LOW_THRESHOLD) * 3.0
        else:
            magnitude_score = magnitude * 2.0
        
        factors["magnitude_score"] = magnitude_score
        score += magnitude_score
        
        # Depth scoring (0-15 points, shallower = more dangerous)
        if depth < 10:
            depth_score = 15.0
        elif depth < 30:
            depth_score = 10.0
        elif depth < 70:
            depth_score = 5.0
        else:
            depth_score = 2.0
        
        factors["depth_score"] = depth_score
        score += depth_score
        
        # Determine severity
        severity = self._score_to_severity(score)
        
        # Generate description
        description = self._generate_description(magnitude, depth, severity)
        
        return RiskScore(
            severity=severity,
            score=min(score, 100.0),
            factors=factors,
            description=description,
        )
    
    def _score_to_severity(self, score: float) -> SeverityLevel:
        """Convert numeric score to severity level."""
        if score >= 45:
            return SeverityLevel.CRITICAL
        elif score >= 35:
            return SeverityLevel.HIGH
        elif score >= 20:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_description(self, magnitude: float, depth: float, severity: SeverityLevel) -> str:
        """Generate human-readable description."""
        if severity == SeverityLevel.CRITICAL:
            return f"CRITICAL: Major earthquake (M{magnitude}) at {depth}km depth. Potential for significant damage."
        elif severity == SeverityLevel.HIGH:
            return f"HIGH: Strong earthquake (M{magnitude}) at {depth}km depth. Damage possible."
        elif severity == SeverityLevel.MEDIUM:
            return f"MEDIUM: Moderate earthquake (M{magnitude}) at {depth}km depth. Light shaking felt."
        else:
            return f"LOW: Minor earthquake (M{magnitude}) at {depth}km depth. Barely noticeable."


class StormRiskStrategy(RiskStrategy):
    """Risk assessment strategy for storms and weather events."""
    
    def can_handle(self, event_type: str) -> bool:
        return event_type.upper() in ["STORM", "WEATHER", "HURRICANE", "TYPHOON", "WINTER_STORM", "WILDFIRE"]
    
    def assess(self, event_data: Dict[str, Any]) -> RiskScore:
        """Assess storm risk based on wind speed and rainfall."""
        wind_speed = event_data.get("wind_speed", 0) or 0
        rainfall = event_data.get("rainfall", 0) or 0
        event_type = event_data.get("event_type", "").upper()
        
        factors = {}
        score = 0.0
        
        # Base score for alert types that always have some risk
        base_scores = {
            "HURRICANE": 50.0,
            "TYPHOON": 50.0,
            "WINTER_STORM": 35.0,
            "WILDFIRE": 40.0,
            "STORM": 25.0,
        }
        
        if event_type in base_scores:
            score = base_scores[event_type]
            factors["base_score"] = base_scores[event_type]
        
        # Wind speed scoring (0-50 points, mph)
        # Convert m/s to mph if needed
        wind_mph = wind_speed * 2.237 if wind_speed < 100 else wind_speed
        
        if wind_mph >= settings.WIND_SPEED_CRITICAL_THRESHOLD:
            wind_score = 50.0
        elif wind_mph >= settings.WIND_SPEED_HIGH_THRESHOLD:
            wind_score = 40.0 + (wind_mph - settings.WIND_SPEED_HIGH_THRESHOLD) * 0.3
        elif wind_mph >= settings.WIND_SPEED_MEDIUM_THRESHOLD:
            wind_score = 25.0 + (wind_mph - settings.WIND_SPEED_MEDIUM_THRESHOLD) * 0.5
        elif wind_mph >= settings.WIND_SPEED_LOW_THRESHOLD:
            wind_score = 10.0 + (wind_mph - settings.WIND_SPEED_LOW_THRESHOLD) * 0.5
        else:
            wind_score = wind_mph * 0.2
        
        factors["wind_score"] = wind_score
        score = max(score, wind_score)
        
        # Rainfall scoring (0-30 points, mm/hour)
        if rainfall >= settings.RAINFALL_CRITICAL_THRESHOLD:
            rain_score = 30.0
        elif rainfall >= settings.RAINFALL_HIGH_THRESHOLD:
            rain_score = 20.0 + (rainfall - settings.RAINFALL_HIGH_THRESHOLD) * 0.5
        elif rainfall >= settings.RAINFALL_MEDIUM_THRESHOLD:
            rain_score = 10.0 + (rainfall - settings.RAINFALL_MEDIUM_THRESHOLD) * 0.7
        elif rainfall >= settings.RAINFALL_LOW_THRESHOLD:
            rain_score = 5.0 + (rainfall - settings.RAINFALL_LOW_THRESHOLD) * 0.5
        else:
            rain_score = rainfall * 0.5
        
        factors["rainfall_score"] = rain_score
        score += rain_score
        
        # Determine severity
        severity = self._score_to_severity(score)
        
        # Generate description
        description = self._generate_description(wind_mph, rainfall, severity)
        
        return RiskScore(
            severity=severity,
            score=min(score, 100.0),
            factors=factors,
            description=description,
        )
    
    def _score_to_severity(self, score: float) -> SeverityLevel:
        """Convert numeric score to severity level."""
        if score >= 40:
            return SeverityLevel.CRITICAL
        elif score >= 30:
            return SeverityLevel.HIGH
        elif score >= 15:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_description(self, wind_mph: float, rainfall: float, severity: SeverityLevel) -> str:
        """Generate human-readable description."""
        if severity == SeverityLevel.CRITICAL:
            return f"CRITICAL: Extreme weather conditions with {wind_mph:.0f} mph winds and {rainfall:.1f}mm/hr rainfall."
        elif severity == SeverityLevel.HIGH:
            return f"HIGH: Severe weather with {wind_mph:.0f} mph winds and {rainfall:.1f}mm/hr rainfall."
        elif severity == SeverityLevel.MEDIUM:
            return f"MEDIUM: Moderate weather with {wind_mph:.0f} mph winds and {rainfall:.1f}mm/hr rainfall."
        else:
            return f"LOW: Minor weather conditions with {wind_mph:.0f} mph winds and {rainfall:.1f}mm/hr rainfall."


class FloodRiskStrategy(RiskStrategy):
    """Risk assessment strategy for flooding events."""
    
    def can_handle(self, event_type: str) -> bool:
        return event_type.upper() in ["FLOOD", "FLOODING"]
    
    def assess(self, event_data: Dict[str, Any]) -> RiskScore:
        """Assess flood risk based on rainfall and historical data."""
        rainfall = event_data.get("rainfall", 0) or 0
        
        factors = {}
        score = 0.0
        
        # Rainfall intensity scoring
        if rainfall >= settings.RAINFALL_CRITICAL_THRESHOLD:
            rain_score = 60.0
        elif rainfall >= settings.RAINFALL_HIGH_THRESHOLD:
            rain_score = 45.0
        elif rainfall >= settings.RAINFALL_MEDIUM_THRESHOLD:
            rain_score = 30.0
        elif rainfall >= settings.RAINFALL_LOW_THRESHOLD:
            rain_score = 15.0
        else:
            rain_score = 5.0
        
        factors["rainfall_score"] = rain_score
        score += rain_score
        
        severity = self._score_to_severity(score)
        description = self._generate_description(rainfall, severity)
        
        return RiskScore(
            severity=severity,
            score=min(score, 100.0),
            factors=factors,
            description=description,
        )
    
    def _score_to_severity(self, score: float) -> SeverityLevel:
        if score >= 50:
            return SeverityLevel.CRITICAL
        elif score >= 40:
            return SeverityLevel.HIGH
        elif score >= 25:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _generate_description(self, rainfall: float, severity: SeverityLevel) -> str:
        if severity == SeverityLevel.CRITICAL:
            return f"CRITICAL: Extreme flooding expected with {rainfall:.1f}mm/hr rainfall."
        elif severity == SeverityLevel.HIGH:
            return f"HIGH: Significant flooding possible with {rainfall:.1f}mm/hr rainfall."
        elif severity == SeverityLevel.MEDIUM:
            return f"MEDIUM: Moderate flooding risk with {rainfall:.1f}mm/hr rainfall."
        else:
            return f"LOW: Minor flooding risk with {rainfall:.1f}mm/hr rainfall."


class RiskEngine:
    """Main risk assessment engine using strategy pattern."""
    
    def __init__(self):
        self.strategies: List[RiskStrategy] = [
            EarthquakeRiskStrategy(),
            StormRiskStrategy(),
            FloodRiskStrategy(),
        ]
    
    def register_strategy(self, strategy: RiskStrategy):
        """Register a new risk assessment strategy."""
        self.strategies.append(strategy)
        logger.info(f"Registered risk strategy: {strategy.__class__.__name__}")
    
    def assess(self, event_data: Dict[str, Any]) -> RiskScore:
        """Assess risk for an event using appropriate strategy."""
        event_type = event_data.get("event_type", "GENERAL")
        
        for strategy in self.strategies:
            if strategy.can_handle(event_type):
                logger.debug(f"Using {strategy.__class__.__name__} for {event_type}")
                return strategy.assess(event_data)
        
        # Default: low risk for unknown event types
        logger.warning(f"No strategy found for event type: {event_type}")
        return RiskScore(
            severity=SeverityLevel.LOW,
            score=5.0,
            factors={},
            description=f"Unknown event type: {event_type}",
        )
    
    def get_alert_type(self, event_data: Dict[str, Any]) -> str:
        """Determine alert type from event data."""
        event_type = event_data.get("event_type", "GENERAL").upper()
        
        mapping = {
            "EARTHQUAKE": "EARTHQUAKE",
            "WEATHER": "STORM",
            "STORM": "STORM",
            "HURRICANE": "STORM",
            "TYPHOON": "STORM",
            "FLOOD": "FLOOD",
            "FLOODING": "FLOOD",
        }
        
        return mapping.get(event_type, "GENERAL")


# Singleton instance
risk_engine = RiskEngine()
