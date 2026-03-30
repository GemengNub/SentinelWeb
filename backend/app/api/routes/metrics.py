"""
Metrics API routes for monitoring and analytics.
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.session import get_session
from app.models.alert import Alert
from app.models.event import Event
from app.models.prediction import Prediction

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def get_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get system metrics.
    
    Returns various metrics about alerts, events, and predictions.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Alert metrics
    alert_count_result = await session.execute(
        select(func.count(Alert.id)).where(Alert.event_time >= cutoff_time)
    )
    alert_count = alert_count_result.scalar() or 0
    
    # Alerts by severity
    severity_result = await session.execute(
        select(Alert.severity, func.count(Alert.id))
        .where(Alert.event_time >= cutoff_time)
        .group_by(Alert.severity)
    )
    alerts_by_severity = {row[0]: row[1] for row in severity_result.all()}
    
    # Alerts by type
    type_result = await session.execute(
        select(Alert.alert_type, func.count(Alert.id))
        .where(Alert.event_time >= cutoff_time)
        .group_by(Alert.alert_type)
    )
    alerts_by_type = {row[0]: row[1] for row in type_result.all()}
    
    # Event metrics
    event_count_result = await session.execute(
        select(func.count(Event.id)).where(Event.event_time >= cutoff_time)
    )
    event_count = event_count_result.scalar() or 0
    
    # Events by type
    event_type_result = await session.execute(
        select(Event.event_type, func.count(Event.id))
        .where(Event.event_time >= cutoff_time)
        .group_by(Event.event_type)
    )
    events_by_type = {row[0]: row[1] for row in event_type_result.all()}
    
    # Anomaly metrics
    anomaly_count_result = await session.execute(
        select(func.count(Alert.id)).where(
            and_(
                Alert.is_anomaly == True,
                Alert.event_time >= cutoff_time,
            )
        )
    )
    anomaly_count = anomaly_count_result.scalar() or 0
    
    # Prediction metrics
    prediction_count_result = await session.execute(
        select(func.count(Prediction.id)).where(
            Prediction.prediction_made_at >= cutoff_time
        )
    )
    prediction_count = prediction_count_result.scalar() or 0
    
    return {
        "time_window_hours": hours,
        "alerts": {
            "total": alert_count,
            "by_severity": alerts_by_severity,
            "by_type": alerts_by_type,
        },
        "events": {
            "total": event_count,
            "by_type": events_by_type,
        },
        "anomalies": {
            "detected": anomaly_count,
        },
        "predictions": {
            "total": prediction_count,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/hourly")
async def get_hourly_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get hourly aggregated metrics.
    
    Returns metrics aggregated by hour for trend analysis.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get hourly alert counts
    # Note: This is a simplified approach - in production, use proper time bucketing
    alerts = await session.execute(
        select(Alert).where(Alert.event_time >= cutoff_time)
    )
    all_alerts = alerts.scalars().all()
    
    hourly_data: Dict[str, Dict[str, int]] = {}
    
    for alert in all_alerts:
        hour_key = alert.event_time.strftime("%Y-%m-%d %H:00")
        
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "earthquake": 0,
                "storm": 0,
                "flood": 0,
            }
        
        hourly_data[hour_key]["total"] += 1
        
        if alert.severity == "CRITICAL":
            hourly_data[hour_key]["critical"] += 1
        elif alert.severity == "HIGH":
            hourly_data[hour_key]["high"] += 1
        elif alert.severity == "MEDIUM":
            hourly_data[hour_key]["medium"] += 1
        else:
            hourly_data[hour_key]["low"] += 1
        
        if alert.alert_type == "EARTHQUAKE":
            hourly_data[hour_key]["earthquake"] += 1
        elif alert.alert_type == "STORM":
            hourly_data[hour_key]["storm"] += 1
        elif alert.alert_type == "FLOOD":
            hourly_data[hour_key]["flood"] += 1
    
    # Sort by hour
    sorted_data = [
        {"hour": k, **v}
        for k, v in sorted(hourly_data.items())
    ]
    
    return {
        "time_window_hours": hours,
        "hourly_data": sorted_data,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/severity-trend")
async def get_severity_trend(
    days: int = Query(7, ge=1, le=30, description="Time window in days"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get severity trend over time.
    
    Returns daily counts of alerts by severity level.
    """
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    alerts = await session.execute(
        select(Alert).where(Alert.event_time >= cutoff_time)
    )
    all_alerts = alerts.scalars().all()
    
    daily_data: Dict[str, Dict[str, int]] = {}
    
    for alert in all_alerts:
        day_key = alert.event_time.strftime("%Y-%m-%d")
        
        if day_key not in daily_data:
            daily_data[day_key] = {
                "date": day_key,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "total": 0,
            }
        
        daily_data[day_key]["total"] += 1
        
        if alert.severity == "CRITICAL":
            daily_data[day_key]["critical"] += 1
        elif alert.severity == "HIGH":
            daily_data[day_key]["high"] += 1
        elif alert.severity == "MEDIUM":
            daily_data[day_key]["medium"] += 1
        else:
            daily_data[day_key]["low"] += 1
    
    sorted_data = sorted(daily_data.values(), key=lambda x: x["date"])
    
    return {
        "days": days,
        "daily_trend": sorted_data,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/geographic")
async def get_geographic_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get geographic distribution of alerts.
    
    Returns alerts grouped by geographic regions.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    alerts = await session.execute(
        select(Alert).where(Alert.event_time >= cutoff_time)
    )
    all_alerts = alerts.scalars().all()
    
    # Group by rough geographic regions (simplified)
    regions = {}
    
    for alert in all_alerts:
        # Simple region bucketing by latitude/longitude
        lat_bucket = round(alert.latitude / 10) * 10
        lon_bucket = round(alert.longitude / 10) * 10
        region_key = f"{lat_bucket},{lon_bucket}"
        
        if region_key not in regions:
            regions[region_key] = {
                "center_lat": lat_bucket,
                "center_lon": lon_bucket,
                "alert_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "types": {},
            }
        
        regions[region_key]["alert_count"] += 1
        
        if alert.severity == "CRITICAL":
            regions[region_key]["critical_count"] += 1
        elif alert.severity == "HIGH":
            regions[region_key]["high_count"] += 1
        
        alert_type = alert.alert_type
        if alert_type not in regions[region_key]["types"]:
            regions[region_key]["types"][alert_type] = 0
        regions[region_key]["types"][alert_type] += 1
    
    return {
        "time_window_hours": hours,
        "regions": list(regions.values()),
        "total_regions": len(regions),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/sla")
async def get_sla_metrics(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    threshold_minutes: int = Query(15, ge=1, le=60, description="SLA threshold in minutes"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get SLA (Service Level Agreement) metrics.
    
    Returns metrics about alert response times and SLA compliance.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    alerts = await session.execute(
        select(Alert).where(Alert.event_time >= cutoff_time)
    )
    all_alerts = alerts.scalars().all()
    
    total_alerts = 0
    acknowledged_alerts = 0
    within_sla = 0
    response_times = []
    
    for alert in all_alerts:
        total_alerts += 1
        
        if alert.acknowledged and alert.acknowledged_at:
            acknowledged_alerts += 1
            
            if alert.event_time and alert.acknowledged_at:
                response_time = (alert.acknowledged_at - alert.event_time).total_seconds() / 60
                response_times.append(response_time)
                
                if response_time <= threshold_minutes:
                    within_sla += 1
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    sla_compliance = (within_sla / acknowledged_alerts * 100) if acknowledged_alerts > 0 else 0
    
    return {
        "time_window_hours": hours,
        "threshold_minutes": threshold_minutes,
        "total_alerts": total_alerts,
        "acknowledged_alerts": acknowledged_alerts,
        "within_sla": within_sla,
        "sla_compliance_percent": round(sla_compliance, 2),
        "avg_response_time_minutes": round(avg_response_time, 2),
        "min_response_time_minutes": round(min(response_times), 2) if response_times else 0,
        "max_response_time_minutes": round(max(response_times), 2) if response_times else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/reports/daily")
async def get_daily_report(
    date: str = Query(None, description="Date in YYYY-MM-DD format (defaults to yesterday)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get daily report of alerts.
    """
    if date:
        report_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        report_date = datetime.utcnow() - timedelta(days=1)
    
    start_of_day = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    alerts = await session.execute(
        select(Alert).where(
            and_(
                Alert.event_time >= start_of_day,
                Alert.event_time < end_of_day,
            )
        )
    )
    all_alerts = alerts.scalars().all()
    
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    type_counts = {}
    total_acknowledged = 0
    
    for alert in all_alerts:
        if alert.severity in severity_counts:
            severity_counts[alert.severity] += 1
        
        type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
        
        if alert.acknowledged:
            total_acknowledged += 1
    
    return {
        "report_type": "daily",
        "date": start_of_day.strftime("%Y-%m-%d"),
        "total_alerts": len(all_alerts),
        "alerts_by_severity": severity_counts,
        "alerts_by_type": type_counts,
        "acknowledged_count": total_acknowledged,
        "acknowledgment_rate": round(total_acknowledged / len(all_alerts) * 100, 2) if all_alerts else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/reports/weekly")
async def get_weekly_report(
    weeks_ago: int = Query(0, ge=0, le=4, description="Weeks ago (0 = current week)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get weekly report of alerts.
    """
    end_date = datetime.utcnow() - timedelta(weeks=weeks_ago)
    start_date = end_date - timedelta(days=7)
    
    alerts = await session.execute(
        select(Alert).where(
            and_(
                Alert.event_time >= start_date,
                Alert.event_time < end_date,
            )
        )
    )
    all_alerts = alerts.scalars().all()
    
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    type_counts = {}
    total_acknowledged = 0
    anomaly_count = 0
    
    for alert in all_alerts:
        if alert.severity in severity_counts:
            severity_counts[alert.severity] += 1
        
        type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
        
        if alert.acknowledged:
            total_acknowledged += 1
        
        if alert.is_anomaly:
            anomaly_count += 1
    
    return {
        "report_type": "weekly",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "total_alerts": len(all_alerts),
        "alerts_by_severity": severity_counts,
        "alerts_by_type": type_counts,
        "acknowledged_count": total_acknowledged,
        "acknowledgment_rate": round(total_acknowledged / len(all_alerts) * 100, 2) if all_alerts else 0,
        "anomalies_detected": anomaly_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/system")
async def get_system_metrics():
    """
    Get system performance metrics.
    """
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_used_mb": round(psutil.virtual_memory().used / (1024 * 1024), 2),
        "memory_available_mb": round(psutil.virtual_memory().available / (1024 * 1024), 2),
        "disk_percent": psutil.disk_usage('/').percent,
        "timestamp": datetime.utcnow().isoformat(),
    }
