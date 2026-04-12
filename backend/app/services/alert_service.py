"""
Alert service for managing disaster alerts.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.alert import Alert, SeverityLevel, AlertType
from app.schemas.alert import AlertCreate, AlertUpdate, AlertFilter
from app.services.notification import NotificationService


class AlertService:
    """Service for managing disaster alerts."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService()
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Create a new alert."""
        alert = Alert(
            alert_type=alert_data.get("alert_type", "GENERAL"),
            severity=alert_data.get("severity", "LOW"),
            title=alert_data.get("title", "Disaster Alert"),
            description=alert_data.get("description"),
            latitude=alert_data["latitude"],
            longitude=alert_data["longitude"],
            location_name=alert_data.get("location_name"),
            country=alert_data.get("country"),
            magnitude=alert_data.get("magnitude"),
            depth=alert_data.get("depth"),
            wind_speed=alert_data.get("wind_speed"),
            rainfall=alert_data.get("rainfall"),
            source=alert_data.get("source", "SYSTEM"),
            external_id=alert_data.get("external_id"),
            event_data=alert_data.get("event_data"),
            event_time=alert_data.get("event_time", datetime.utcnow()),
            is_anomaly=alert_data.get("is_anomaly", False),
        )
        
        self.session.add(alert)
        await self.session.flush()
        
        logger.info(f"Created alert: {alert.id} - {alert.alert_type} - {alert.severity}")
        
        # Send notifications for high severity alerts
        if alert.severity in ["HIGH", "CRITICAL"]:
            try:
                await self._send_notifications(alert)
            except Exception as e:
                logger.error(f"Failed to send notifications: {str(e)}")
        
        return alert
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    async def get_alerts(
        self,
        filters: Optional[AlertFilter] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[Alert], int]:
        """Get alerts with filtering and pagination."""
        query = select(Alert)
        count_query = select(func.count(Alert.id))
        
        conditions = []
        conditions.append(Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"]))
        
        if filters:
            if filters.alert_type:
                conditions.append(Alert.alert_type == filters.alert_type.value)
            if filters.severity:
                conditions.append(Alert.severity == filters.severity.value)
            if filters.start_date:
                conditions.append(Alert.event_time >= filters.start_date)
            if filters.end_date:
                conditions.append(Alert.event_time <= filters.end_date)
            if filters.min_magnitude is not None:
                conditions.append(Alert.magnitude >= filters.min_magnitude)
            if filters.max_magnitude is not None:
                conditions.append(Alert.magnitude <= filters.max_magnitude)
            if filters.latitude_min is not None:
                conditions.append(Alert.latitude >= filters.latitude_min)
            if filters.latitude_max is not None:
                conditions.append(Alert.latitude <= filters.latitude_max)
            if filters.longitude_min is not None:
                conditions.append(Alert.longitude >= filters.longitude_min)
            if filters.longitude_max is not None:
                conditions.append(Alert.longitude <= filters.longitude_max)
            if filters.is_active is not None:
                conditions.append(Alert.is_active == filters.is_active)
            if filters.is_anomaly is not None:
                conditions.append(Alert.is_anomaly == filters.is_anomaly)
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        query = query.order_by(desc(Alert.event_time)).offset(offset).limit(page_size)
        
        result = await self.session.execute(query)
        alerts = list(result.scalars().all())
        
        return alerts, total
    
    async def update_alert(self, alert_id: str, update_data: AlertUpdate) -> Optional[Alert]:
        """Update an alert."""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None
        
        if update_data.severity is not None:
            alert.severity = update_data.severity.value
        if update_data.description is not None:
            alert.description = update_data.description
        if update_data.is_active is not None:
            alert.is_active = update_data.is_active
        if update_data.acknowledged is not None:
            alert.acknowledged = update_data.acknowledged
            if update_data.acknowledged:
                alert.acknowledged_at = datetime.utcnow()
        
        alert.updated_at = datetime.utcnow()
        
        await self.session.flush()
        logger.info(f"Updated alert: {alert_id}")
        
        return alert
    
    async def acknowledge_alert(self, alert_id: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        return await self.update_alert(
            alert_id,
            AlertUpdate(acknowledged=True)
        )
    
    async def deactivate_alert(self, alert_id: str) -> Optional[Alert]:
        """Deactivate an alert."""
        return await self.update_alert(
            alert_id,
            AlertUpdate(is_active=False)
        )
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        result = await self.session.execute(
            select(Alert)
            .where(
                and_(
                    Alert.is_active == True,
                    Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"])
                )
            )
            .order_by(desc(Alert.event_time))
        )
        return list(result.scalars().all())
    
    async def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(Alert)
            .where(
                and_(
                    Alert.event_time >= cutoff,
                    Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"])
                )
            )
            .order_by(desc(Alert.event_time))
        )
        return list(result.scalars().all())
    
    async def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        # Total alerts (excluding mock/test data)
        total_result = await self.session.execute(
            select(func.count(Alert.id)).where(
                Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"])
            )
        )
        total = total_result.scalar() or 0
        
        # Active alerts
        active_result = await self.session.execute(
            select(func.count(Alert.id)).where(
                and_(
                    Alert.is_active == True,
                    Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"])
                )
            )
        )
        active = active_result.scalar() or 0
        
        # Alerts by severity
        severity_result = await self.session.execute(
            select(Alert.severity, func.count(Alert.id))
            .where(Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"]))
            .group_by(Alert.severity)
        )
        by_severity = {row[0]: row[1] for row in severity_result.all()}
        
        # Alerts by type
        type_result = await self.session.execute(
            select(Alert.alert_type, func.count(Alert.id))
            .where(Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"]))
            .group_by(Alert.alert_type)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        # Recent alerts (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_result = await self.session.execute(
            select(func.count(Alert.id)).where(
                and_(
                    Alert.event_time >= recent_cutoff,
                    Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"])
                )
            )
        )
        recent_24h = recent_result.scalar() or 0
        
        # Anomalies count
        anomaly_result = await self.session.execute(
            select(func.count(Alert.id)).where(
                and_(
                    Alert.is_anomaly == True,
                    Alert.source.not_in(["MOCK", "TEST", "GLOBAL_TEST"])
                )
            )
        )
        anomalies = anomaly_result.scalar() or 0
        
        return {
            "total_alerts": total,
            "active_alerts": active,
            "alerts_by_severity": by_severity,
            "alerts_by_type": by_type,
            "recent_24h": recent_24h,
            "anomalies_detected": anomalies,
        }
    
    async def check_duplicate_alert(
        self,
        external_id: str,
        hours: int = 1,
    ) -> bool:
        """Check if an alert with the same external ID exists recently."""
        if not external_id:
            return False
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(func.count(Alert.id))
            .where(
                and_(
                    Alert.external_id == external_id,
                    Alert.event_time >= cutoff,
                )
            )
        )
        count = result.scalar() or 0
        return count > 0
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        # Send SMS
        if alert.severity in ["HIGH", "CRITICAL"]:
            await self.notification_service.send_sms(alert)
        
        # Send Email
        await self.notification_service.send_email(alert)
        
        # Update alert notification status
        alert.sms_sent = True
        alert.email_sent = True
        await self.session.flush()
