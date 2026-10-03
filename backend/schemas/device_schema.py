from marshmallow import Schema, fields, validate, EXCLUDE
from models.enums import DeviceStatus

VALID_DEVICE_STATUSES = [s.value for s in DeviceStatus]

class DeviceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    device_code = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100, error="Device code must be between 2 and 100 characters.")
    )
    device_name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=255, error="Device name must be between 2 and 255 characters.")
    )
    location = fields.String(
        required=True,
        validate=validate.Length(min=2, max=255, error="Location must be between 2 and 255 characters.")
    )
    device_type = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100, error="Device type must be between 2 and 100 characters.")
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(VALID_DEVICE_STATUSES, error=f"Status must be one of: {VALID_DEVICE_STATUSES}")
    )

class DeviceUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    device_name = fields.String(
        required=False,
        validate=validate.Length(min=2, max=255, error="Device name must be between 2 and 255 characters.")
    )
    location = fields.String(
        required=False,
        validate=validate.Length(min=2, max=255, error="Location must be between 2 and 255 characters.")
    )
    device_type = fields.String(
        required=False,
        validate=validate.Length(min=2, max=100, error="Device type must be between 2 and 100 characters.")
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(VALID_DEVICE_STATUSES, error=f"Status must be one of: {VALID_DEVICE_STATUSES}")
    )
