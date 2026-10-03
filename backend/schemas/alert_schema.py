from marshmallow import Schema, fields, validate, EXCLUDE
from models.enums import AlertSeverity, AlertStatus

VALID_SEVERITIES = [s.value for s in AlertSeverity]
VALID_STATUSES = [s.value for s in AlertStatus]

class AlertFilterSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    severity = fields.String(
        required=False,
        validate=validate.OneOf(VALID_SEVERITIES, error=f"severity must be one of: {VALID_SEVERITIES}")
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(VALID_STATUSES, error=f"status must be one of: {VALID_STATUSES}")
    )
    device_id = fields.Int(required=False)
    alert_type = fields.String(required=False)

class AlertResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    event_id = fields.Int(dump_only=True)
    device_id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    alert_type = fields.Str(dump_only=True)
    message = fields.Str(dump_only=True)
    severity = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    acknowledged_at = fields.Str(dump_only=True)
    resolved_at = fields.Str(dump_only=True)
