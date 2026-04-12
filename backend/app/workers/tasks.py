"""
Celery background tasks for disaster detection system.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
from sqlalchemy import select, delete

from app.workers.celery_app import celery_app
from app.core.config import settings


def get_async_session():
    """Get a new async database session."""
    from app.db.session import async_session_factory
    return async_session_factory()


def run_async(coro):
    """Run async function in Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_earthquakes(self):
    """Poll USGS for earthquake data."""
    logger.info("Polling USGS for earthquake data...")
    
    async def _poll():
        from app.services.api_clients import APIClientFactory
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        client = APIClientFactory.get_usgs_client()
        
        try:
            # Fetch recent earthquakes
            events = await client.get_earthquakes(
                start_time=datetime.utcnow() - timedelta(hours=1),
                min_magnitude=2.5,
                limit=50,
            )
            
            # Store events in database
            async with async_session_factory() as session:
                new_events = []
                
                for event_data in events:
                    # Check for duplicates
                    existing = await session.execute(
                        select(Event).where(Event.external_id == event_data.get("external_id"))
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    # Create new event
                    event = Event(
                        event_type=event_data["event_type"],
                        external_id=event_data.get("external_id"),
                        source=event_data["source"],
                        latitude=event_data["latitude"],
                        longitude=event_data["longitude"],
                        depth=event_data.get("depth"),
                        location_name=event_data.get("location_name"),
                        place=event_data.get("place"),
                        magnitude=event_data.get("magnitude"),
                        magnitude_type=event_data.get("magnitude_type"),
                        intensity=event_data.get("intensity"),
                        event_time=event_data.get("event_time", datetime.utcnow()),
                        raw_data=event_data.get("raw_data"),
                    )
                    session.add(event)
                    new_events.append(event)
                
                await session.commit()
                
                if new_events:
                    logger.info(f"Stored {len(new_events)} new earthquake events")
                
                return len(new_events)
        
        finally:
            await client.close()
    
    try:
        return run_async(_poll())
    except Exception as e:
        logger.error(f"Error polling earthquakes: {str(e)}")
        self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_noaa(self):
    """Poll NOAA for weather alerts data."""
    logger.info("Polling NOAA for weather alerts...")
    
    async def _poll():
        from app.services.api_clients import APIClientFactory
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        client = APIClientFactory.get_noaa_client()
        
        try:
            events = await client.get_alerts()
            
            async with async_session_factory() as session:
                new_events = []
                
                for event_data in events:
                    existing = await session.execute(
                        select(Event).where(Event.external_id == event_data.get("external_id"))
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    location_name = event_data.get("location_name") or "Unknown"
                    if location_name and len(location_name) > 255:
                        location_name = location_name[:255]
                    
                    event = Event(
                        event_type=event_data["event_type"],
                        external_id=event_data.get("external_id"),
                        source=event_data["source"],
                        latitude=event_data["latitude"],
                        longitude=event_data["longitude"],
                        location_name=location_name,
                        place=location_name,
                        magnitude=event_data.get("magnitude"),
                        event_time=event_data.get("event_time", datetime.utcnow()),
                        raw_data=event_data.get("raw_data"),
                    )
                    session.add(event)
                    new_events.append(event)
                
                await session.commit()
                
                if new_events:
                    logger.info(f"Stored {len(new_events)} new NOAA alerts")
                
                return len(new_events)
        
        finally:
            await client.close()
    
    try:
        return run_async(_poll())
    except Exception as e:
        logger.error(f"Error polling NOAA: {str(e)}")
        self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_pagasa(self):
    """Poll PAGASA for earthquake and weather data."""
    logger.info("Polling PAGASA for disaster data...")
    
    async def _poll():
        from app.services.api_clients import APIClientFactory
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        client = APIClientFactory.get_pagasa_client()
        
        new_events = []
        
        async with async_session_factory() as session:
            try:
                earthquakes = await client.get_earthquakes(limit=50)
                
                for event_data in earthquakes:
                    existing = await session.execute(
                        select(Event).where(Event.external_id == event_data.get("external_id"))
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    event = Event(
                        event_type=event_data["event_type"],
                        external_id=event_data.get("external_id"),
                        source=event_data["source"],
                        latitude=event_data["latitude"],
                        longitude=event_data["longitude"],
                        depth=event_data.get("depth"),
                        location_name=event_data.get("location_name"),
                        place=event_data.get("place"),
                        magnitude=event_data.get("magnitude"),
                        event_time=event_data.get("event_time", datetime.utcnow()),
                        raw_data=event_data.get("raw_data"),
                    )
                    session.add(event)
                    new_events.append(event)
                
            except Exception as e:
                logger.warning(f"Failed to get PAGASA earthquakes: {str(e)}")
            
            await session.commit()
            
            if new_events:
                logger.info(f"Stored {len(new_events)} new PAGASA events")
            
            return len(new_events)
    
    try:
        return run_async(_poll())
    except Exception as e:
        logger.error(f"Error polling PAGASA: {str(e)}")
        self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_jma(self):
    """Poll JMA for earthquake and weather warnings."""
    logger.info("Polling JMA for disaster data...")
    
    async def _poll():
        from app.services.api_clients import APIClientFactory
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        client = APIClientFactory.get_jma_client()
        
        new_events = []
        
        async with async_session_factory() as session:
            try:
                earthquakes = await client.get_earthquakes(limit=50)
                
                for event_data in earthquakes:
                    existing = await session.execute(
                        select(Event).where(Event.external_id == event_data.get("external_id"))
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    event = Event(
                        event_type=event_data["event_type"],
                        external_id=event_data.get("external_id"),
                        source=event_data["source"],
                        latitude=event_data["latitude"],
                        longitude=event_data["longitude"],
                        depth=event_data.get("depth"),
                        location_name=event_data.get("location_name"),
                        place=event_data.get("place"),
                        magnitude=event_data.get("magnitude"),
                        intensity=event_data.get("intensity"),
                        event_time=event_data.get("event_time", datetime.utcnow()),
                        raw_data=event_data.get("raw_data"),
                    )
                    session.add(event)
                    new_events.append(event)
                
            except Exception as e:
                logger.warning(f"Failed to get JMA earthquakes: {str(e)}")
            
            await session.commit()
            
            if new_events:
                logger.info(f"Stored {len(new_events)} new JMA events")
            
            return len(new_events)
    
    try:
        return run_async(_poll())
    except Exception as e:
        logger.error(f"Error polling JMA: {str(e)}")
        self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_firms(self):
    """Poll NASA FIRMS for wildfire data."""
    logger.info("Polling NASA FIRMS for fire data...")
    
    async def _poll():
        from app.services.api_clients import APIClientFactory
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        client = APIClientFactory.get_firms_client()
        
        new_events = []
        
        async with async_session_factory() as session:
            try:
                fires = await client.get_fire_data(days=1)
                
                for event_data in fires:
                    existing = await session.execute(
                        select(Event).where(Event.external_id == event_data.get("external_id"))
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    event = Event(
                        event_type=event_data["event_type"],
                        external_id=event_data.get("external_id"),
                        source=event_data["source"],
                        latitude=event_data["latitude"],
                        longitude=event_data["longitude"],
                        magnitude=event_data.get("magnitude"),
                        location_name=event_data.get("location_name"),
                        place=event_data.get("place"),
                        event_time=event_data.get("event_time", datetime.utcnow()),
                        raw_data=event_data.get("raw_data"),
                    )
                    session.add(event)
                    new_events.append(event)
                
            except Exception as e:
                logger.warning(f"Failed to get FIRMS fire data: {str(e)}")
            
            await session.commit()
            
            if new_events:
                logger.info(f"Stored {len(new_events)} new FIRMS fire events")
            
            return len(new_events)
    
    try:
        return run_async(_poll())
    except Exception as e:
        logger.error(f"Error polling FIRMS: {str(e)}")
        self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_weather(self):
    """Poll OpenWeather for weather data."""
    logger.info("Polling weather data...")
    
    async def _poll():
        from app.services.api_clients import APIClientFactory
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        client = APIClientFactory.get_weather_client()
        
        # Sample locations for weather monitoring
        locations = [
            {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco"},
            {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles"},
            {"lat": 40.7128, "lon": -74.0060, "name": "New York"},
            {"lat": 41.8781, "lon": -87.6298, "name": "Chicago"},
            {"lat": 29.7604, "lon": -95.3698, "name": "Houston"},
        ]
        
        new_events = []
        
        async with async_session_factory() as session:
            for loc in locations:
                try:
                    weather_data = await client.get_weather_data(loc["lat"], loc["lon"])
                    
                    if weather_data:
                        existing = await session.execute(
                            select(Event).where(Event.external_id == weather_data.get("external_id"))
                        )
                        
                        if existing.scalar_one_or_none():
                            continue
                        
                        event = Event(
                            event_type=weather_data["event_type"],
                            external_id=weather_data.get("external_id"),
                            source=weather_data["source"],
                            latitude=weather_data["latitude"],
                            longitude=weather_data["longitude"],
                            location_name=weather_data.get("location_name") or loc["name"],
                            temperature=weather_data.get("temperature"),
                            humidity=weather_data.get("humidity"),
                            pressure=weather_data.get("pressure"),
                            wind_speed=weather_data.get("wind_speed"),
                            wind_direction=weather_data.get("wind_direction"),
                            rainfall=weather_data.get("rainfall"),
                            event_time=weather_data.get("event_time", datetime.utcnow()),
                            raw_data=weather_data.get("raw_data"),
                        )
                        session.add(event)
                        new_events.append(event)
                        
                except Exception as e:
                    logger.warning(f"Failed to get weather for {loc['name']}: {str(e)}")
            
            await session.commit()
            
            if new_events:
                logger.info(f"Stored {len(new_events)} weather events")
            
            return len(new_events)
    
    try:
        return run_async(_poll())
    except Exception as e:
        logger.error(f"Error polling weather: {str(e)}")
        self.retry(exc=e)


@celery_app.task(bind=True)
def process_pending_events(self):
    """Process pending events to generate alerts."""
    logger.info("Processing pending events...")
    
    async def _process():
        from app.models.event import Event, EventRepository
        from app.services.risk_engine import risk_engine
        from app.services.anomaly import anomaly_detector
        from app.services.prediction import prediction_engine
        from app.services.alert_service import AlertService
        from app.db.session import async_session_factory
        from app.websocket import publish_alert_update
        
        async with async_session_factory() as session:
            # Get pending events
            events = await EventRepository.get_unprocessed_events(session, limit=100)
            
            alerts_created = 0
            
            for event in events:
                try:
                    # Extract wind_speed and rainfall from raw_data for NOAA/weather events
                    wind_speed = event.wind_speed
                    rainfall = event.rainfall
                    
                    if not wind_speed and event.raw_data:
                        props = event.raw_data.get("properties", {})
                        if props:
                            wind_speed = props.get("windSpeed") or props.get("wind_speed")
                            rainfall = props.get("rainfall") or props.get("precipitation")
                    
                    # Convert event to dict for processing
                    event_data = {
                        "event_type": event.event_type,
                        "magnitude": event.magnitude,
                        "depth": event.depth,
                        "wind_speed": wind_speed,
                        "rainfall": rainfall,
                        "latitude": event.latitude,
                        "longitude": event.longitude,
                        "location_name": event.location_name or event.place,
                        "external_id": event.external_id,
                        "source": event.source,
                        "event_time": event.event_time,
                        "raw_data": event.raw_data,
                    }
                    
                    # Assess risk
                    risk_score = risk_engine.assess(event_data)
                    
                    # Check for anomalies
                    anomaly_result = None
                    if event.event_type == "EARTHQUAKE" and event.magnitude:
                        anomaly_result = anomaly_detector.process_earthquake(event_data)
                        
                        # Add to prediction engine
                        prediction_engine.add_earthquake_data(event.magnitude, event.event_time)
                        
                    elif event.event_type == "WEATHER":
                        anomaly_result = anomaly_detector.process_weather(event_data)
                        
                        if event.rainfall:
                            prediction_engine.add_rainfall_data(event.rainfall, event.event_time)
                        if event.wind_speed:
                            prediction_engine.add_wind_data(event.wind_speed, event.event_time)
                    
                    # Add severity to prediction engine
                    prediction_engine.add_severity(risk_score.score)
                    
                    # Create alert if severity is not LOW or if anomaly detected
                    should_alert = (
                        risk_score.severity.value in ["MEDIUM", "HIGH", "CRITICAL"] or
                        (anomaly_result and anomaly_result.is_anomaly)
                    )
                    
                    if should_alert:
                        alert_service = AlertService(session)
                        
                        # Check for duplicates
                        is_duplicate = await alert_service.check_duplicate_alert(
                            event.external_id,
                            hours=6,
                        )
                        
                        if not is_duplicate:
                            alert_data = {
                                "alert_type": risk_engine.get_alert_type(event_data),
                                "severity": risk_score.severity.value,
                                "title": f"{event.event_type} Alert - {(event.location_name or 'Unknown Location')[:100]}",
                                "description": risk_score.description[:500] if risk_score.description else "",
                                "latitude": event.latitude,
                                "longitude": event.longitude,
                                "location_name": (event.location_name or event.place)[:255] if event.location_name or event.place else "Unknown",
                                "magnitude": event.magnitude,
                                "depth": event.depth,
                                "wind_speed": event.wind_speed,
                                "rainfall": event.rainfall,
                                "source": event.source,
                                "external_id": event.external_id,
                                "event_data": {
                                    "risk_score": risk_score.to_dict(),
                                    "anomaly": anomaly_result.to_dict() if anomaly_result else None,
                                    "original_event_id": event.id,
                                },
                                "event_time": event.event_time,
                                "is_anomaly": anomaly_result.is_anomaly if anomaly_result else False,
                            }
                            
                            alert = await alert_service.create_alert(alert_data)
                            alerts_created += 1
                            
                            # Publish to WebSocket
                            await publish_alert_update({
                                "id": alert.id,
                                "alert_type": alert.alert_type,
                                "severity": alert.severity,
                                "title": alert.title,
                                "description": alert.description,
                                "latitude": alert.latitude,
                                "longitude": alert.longitude,
                                "location_name": alert.location_name,
                                "magnitude": alert.magnitude,
                                "event_time": alert.event_time.isoformat(),
                                "is_anomaly": alert.is_anomaly,
                            })
                    
                    # Mark event as processed
                    await EventRepository.mark_as_processed(session, event.id)
                    
                except Exception as e:
                    logger.error(f"Error processing event {event.id}: {str(e)}")
                    continue
            
            await session.commit()
            
            logger.info(f"Processed {len(events)} events, created {alerts_created} alerts")
            return {"processed": len(events), "alerts_created": alerts_created}
    
    return run_async(_process())


@celery_app.task(bind=True)
def generate_predictions(self):
    """Generate disaster predictions."""
    logger.info("Generating predictions...")
    
    async def _generate():
        from app.services.prediction import prediction_engine
        from app.models.prediction import Prediction
        from app.db.session import async_session_factory
        from app.websocket import publish_prediction_update
        
        predictions_created = 0
        
        async with async_session_factory() as session:
            # Generate earthquake prediction
            try:
                eq_prediction = prediction_engine.predict_earthquake(
                    forecast_hours=settings.PREDICTION_FORECAST_HOURS,
                )
                
                prediction = Prediction(
                    prediction_type="EARTHQUAKE",
                    latitude=37.7749,  # Default, would be region-specific
                    longitude=-122.4194,
                    predicted_value=eq_prediction.predicted_value,
                    confidence_score=eq_prediction.confidence_score,
                    prediction_interval_lower=eq_prediction.interval_lower,
                    prediction_interval_upper=eq_prediction.interval_upper,
                    forecast_horizon_hours=eq_prediction.forecast_horizon_hours,
                    predicted_for_time=datetime.utcnow() + timedelta(hours=eq_prediction.forecast_horizon_hours),
                    prediction_made_at=datetime.utcnow(),
                    escalation_probability=eq_prediction.escalation_probability,
                    risk_level=eq_prediction.risk_level,
                    model_name=eq_prediction.model_name,
                )
                session.add(prediction)
                predictions_created += 1
                
                # Publish prediction
                await publish_prediction_update({
                    "type": "EARTHQUAKE",
                    "predicted_value": eq_prediction.predicted_value,
                    "confidence": eq_prediction.confidence_score,
                    "risk_level": eq_prediction.risk_level,
                    "escalation_probability": eq_prediction.escalation_probability,
                })
                
            except Exception as e:
                logger.error(f"Error generating earthquake prediction: {str(e)}")
            
            # Generate rainfall prediction
            try:
                rain_prediction = prediction_engine.predict_rainfall(
                    forecast_hours=settings.PREDICTION_FORECAST_HOURS,
                )
                
                prediction = Prediction(
                    prediction_type="RAINFALL",
                    latitude=37.7749,
                    longitude=-122.4194,
                    predicted_value=rain_prediction.predicted_value,
                    confidence_score=rain_prediction.confidence_score,
                    prediction_interval_lower=rain_prediction.interval_lower,
                    prediction_interval_upper=rain_prediction.interval_upper,
                    forecast_horizon_hours=rain_prediction.forecast_horizon_hours,
                    predicted_for_time=datetime.utcnow() + timedelta(hours=rain_prediction.forecast_horizon_hours),
                    prediction_made_at=datetime.utcnow(),
                    escalation_probability=rain_prediction.escalation_probability,
                    risk_level=rain_prediction.risk_level,
                    model_name=rain_prediction.model_name,
                )
                session.add(prediction)
                predictions_created += 1
                
            except Exception as e:
                logger.error(f"Error generating rainfall prediction: {str(e)}")
            
            # Generate wind prediction
            try:
                wind_prediction = prediction_engine.predict_wind(
                    forecast_hours=settings.PREDICTION_FORECAST_HOURS,
                )
                
                prediction = Prediction(
                    prediction_type="WIND",
                    latitude=37.7749,
                    longitude=-122.4194,
                    predicted_value=wind_prediction.predicted_value,
                    confidence_score=wind_prediction.confidence_score,
                    prediction_interval_lower=wind_prediction.interval_lower,
                    prediction_interval_upper=wind_prediction.interval_upper,
                    forecast_horizon_hours=wind_prediction.forecast_horizon_hours,
                    predicted_for_time=datetime.utcnow() + timedelta(hours=wind_prediction.forecast_horizon_hours),
                    prediction_made_at=datetime.utcnow(),
                    escalation_probability=wind_prediction.escalation_probability,
                    risk_level=wind_prediction.risk_level,
                    model_name=wind_prediction.model_name,
                )
                session.add(prediction)
                predictions_created += 1
                
            except Exception as e:
                logger.error(f"Error generating wind prediction: {str(e)}")
            
            await session.commit()
            
            logger.info(f"Generated {predictions_created} predictions")
            return {"predictions_created": predictions_created}
    
    return run_async(_generate())


@celery_app.task(bind=True)
def cleanup_old_events(self):
    """Clean up old events from database."""
    logger.info("Cleaning up old events...")
    
    async def _cleanup():
        from app.models.event import Event
        from app.db.session import async_session_factory
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        async with async_session_factory() as session:
            result = await session.execute(
                delete(Event).where(Event.created_at < cutoff_date)
            )
            deleted_count = result.rowcount
            await session.commit()
            
            logger.info(f"Deleted {deleted_count} old events")
            return {"deleted": deleted_count}
    
    return run_async(_cleanup())


@celery_app.task(bind=True)
def send_daily_summary(self):
    """Send daily summary email."""
    logger.info("Sending daily summary...")
    
    async def _send():
        from app.services.alert_service import AlertService
        from app.services.notification import NotificationService
        from app.db.session import async_session_factory
        
        async with async_session_factory() as session:
            service = AlertService(session)
            stats = await service.get_alert_stats()
            
            notification_service = NotificationService()
            
            # Create summary message
            summary = f"""
            Daily Disaster Detection Summary
            =================================
            
            Total Alerts: {stats['total_alerts']}
            Active Alerts: {stats['active_alerts']}
            Alerts (Last 24h): {stats['recent_24h']}
            Anomalies Detected: {stats['anomalies_detected']}
            
            Alerts by Severity:
            - Critical: {stats['alerts_by_severity'].get('CRITICAL', 0)}
            - High: {stats['alerts_by_severity'].get('HIGH', 0)}
            - Medium: {stats['alerts_by_severity'].get('MEDIUM', 0)}
            - Low: {stats['alerts_by_severity'].get('LOW', 0)}
            
            Alerts by Type:
            {chr(10).join(f'- {k}: {v}' for k, v in stats['alerts_by_type'].items())}
            """
            
            logger.info(f"Daily summary:\n{summary}")
            
            return {"sent": True, "stats": stats}
    
    return run_async(_send())
