from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code

def error_response(message="An error occurred", error_code="ERROR", status_code=400, errors=None):
    response = {
        "success": False,
        "message": message,
        "error": error_code
    }
    if errors is not None:
        response["errors"] = errors
    return jsonify(response), status_code
