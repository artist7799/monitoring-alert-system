from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE
import re

class RegisterSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # Ignore extra fields like role if passed in payload

    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100, error="Name must be between 2 and 100 characters.")
    )
    email = fields.Email(
        required=True,
        error_messages={"invalid": "Invalid email format."}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, error="Password must be at least 6 characters long.")
    )

    @validates("password")
    def validate_password_complexity(self, value):
        if not re.search(r"[A-Za-z]", value) or not re.search(r"[0-9]", value):
            raise ValidationError("Password must contain both letters and numbers.")

class LoginSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    email = fields.Email(
        required=True,
        error_messages={"invalid": "Invalid email format."}
    )
    password = fields.String(required=True)

class UserResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    email = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
