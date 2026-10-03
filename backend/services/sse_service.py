import json
import time
from datetime import datetime
from database.db import db
from models.event import Event
from models.alert import Alert
from models.device import Device
from services.monitoring_service import MonitoringService

def format_sse_event(event_name: str, data: dict) -> str:
    """Format SSE payload according to W3C EventSource standard."""
    json_str = json.dumps(data)
    return f"event: {event_name}\ndata: {json_str}\n\n"

def generate_sse_stream(app, max_iterations: int = None, poll_interval: float = 1.0):
    """
    Server-Sent Events generator.
    Each connection runs an independent loop with isolated state and cursors.
    """
    with app.app_context():
        # Initialize client-specific state cursors
        latest_event = Event.query.order_by(Event.id.desc()).first()
        latest_alert = Alert.query.order_by(Alert.id.desc()).first()

        last_event_id = latest_event.id if latest_event else 0
        last_alert_id = latest_alert.id if latest_alert else 0
        last_overview_hash = None
        last_heartbeat_time = 0

        # 1. Emit Initial System Status Overview
        success, overview_data, _, _ = MonitoringService.get_system_overview()
        if success:
            last_overview_hash = json.dumps(overview_data, sort_keys=True)
            yield format_sse_event("system_status", overview_data)

        # 2. Emit Initial Active Device Statuses
        success, devices_payload, _, _ = MonitoringService.get_device_statuses({}, page=1, per_page=100)
        if success and "devices" in devices_payload:
            for dev in devices_payload["devices"]:
                yield format_sse_event("device_status", dev)

    iteration = 0
    try:
        while True:
            iteration += 1
            if max_iterations and iteration > max_iterations:
                break

            with app.app_context():
                current_time = time.time()

                # A. Check and emit Heartbeat (every 15 seconds)
                if current_time - last_heartbeat_time >= 15:
                    last_heartbeat_time = current_time
                    utc_now_str = datetime.utcnow().isoformat() + "Z"
                    yield format_sse_event("heartbeat", {"timestamp": utc_now_str})

                # B. Stream New Events
                new_events = Event.query.filter(Event.id > last_event_id)\
                    .order_by(Event.id.asc())\
                    .all()

                for ev in new_events:
                    last_event_id = ev.id
                    yield format_sse_event("event", ev.to_dict())

                    # If device last_seen updated, emit device status update
                    if ev.device and ev.device.is_active:
                        yield format_sse_event("device_status", {
                            "device_id": ev.device.id,
                            "device_code": ev.device.device_code,
                            "status": ev.device.status,
                            "last_seen": ev.device.last_seen.isoformat() if ev.device.last_seen else None
                        })

                # C. Stream New Alerts
                new_alerts = Alert.query.filter(Alert.id > last_alert_id)\
                    .order_by(Alert.id.asc())\
                    .all()

                for al in new_alerts:
                    last_alert_id = al.id
                    yield format_sse_event("alert", al.to_dict())

                # D. Emit System Overview if state changed
                success, overview_data, _, _ = MonitoringService.get_system_overview()
                if success:
                    current_hash = json.dumps(overview_data, sort_keys=True)
                    if current_hash != last_overview_hash:
                        last_overview_hash = current_hash
                        yield format_sse_event("system_status", overview_data)

            time.sleep(poll_interval)

    except (GeneratorExit, BrokenPipeError, ConnectionResetError):
        # Clean disconnect handling without crashing Flask or logging errors
        return
