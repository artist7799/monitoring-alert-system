from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE
from datetime import datetime
from models.enums import EventType

VALID_EVENT_TYPES = [e.value for e in EventType]

class EventCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    device_id = fields.Int(
        required=True,
        error_messages={"required": "device_id is required."}
    )
    event_type = fields.String(
        required=True,
        validate=validate.OneOf(VALID_EVENT_TYPES, error=f"event_type must be one of: {VALID_EVENT_TYPES}")
    )
    metric_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="metric_name must be between 1 and 100 characters.")
    )
    metric_value = fields.Float(
        required=True,
        error_messages={"required": "metric_value is required and must be numeric."}
    )
    unit = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20, error="unit must be between 1 and 20 characters.")
    )
    message = fields.String(
        required=False,
        validate=validate.Length(max=500, error="message maximum length is 500 characters.")
    )
    timestamp = fields.DateTime(
        required=False,
        error_messages={"invalid": "Invalid ISO datetime format for timestamp."}
    )

class EventResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    device_id = fields.Int(dump_only=True)
    event_type = fields.Str(dump_only=True)
    metric_name = fields.Str(dump_only=True)
    metric_value = fields.Float(dump_only=True)
    unit = fields.Str(dump_only=True)
    message = fields.Str(dump_only=True)
    timestamp = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
