"""
Grafana dashboard JSON schema and validation utilities.
"""

import json
from typing import Any, Dict, List, Tuple

import jsonschema
from jsonschema import validators
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError

from app.schemas.models import DashboardValidationResult, ValidationError

# This is a simplified version of the Grafana dashboard schema
# In a production setting, you would want to use the complete schema from Grafana
GRAFANA_DASHBOARD_SCHEMA = {
    "type": "object",
    "required": ["panels", "title"],
    "properties": {
        "id": {"type": "integer"},
        "uid": {"type": "string"},
        "title": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"}
        },
        "timezone": {"type": "string"},
        "schemaVersion": {"type": "integer"},
        "version": {"type": "integer"},
        "refresh": {"type": ["string", "null"]},
        "time": {
            "type": "object",
            "properties": {
                "from": {"type": "string"},
                "to": {"type": "string"}
            },
            "required": ["from", "to"]
        },
        "panels": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "title"],
                "properties": {
                    "id": {"type": "integer"},
                    "type": {"type": "string"},
                    "title": {"type": "string"},
                    "gridPos": {
                        "type": "object",
                        "properties": {
                            "h": {"type": "integer"},
                            "w": {"type": "integer"},
                            "x": {"type": "integer"},
                            "y": {"type": "integer"}
                        },
                        "required": ["h", "w", "x", "y"]
                    },
                    "datasource": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "object",
                                "required": ["type", "uid"],
                                "properties": {
                                    "type": {"type": "string"},
                                    "uid": {"type": "string"}
                                }
                            },
                            {"type": "null"}
                        ]
                    },
                    "targets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "refId": {"type": "string"},
                                "expr": {"type": "string"},
                                "format": {"type": "string"},
                                "intervalMs": {"type": "integer"},
                                "legendFormat": {"type": "string"},
                                "datasource": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {
                                            "type": "object",
                                            "required": ["type", "uid"],
                                            "properties": {
                                                "type": {"type": "string"},
                                                "uid": {"type": "string"}
                                            }
                                        },
                                        {"type": "null"}
                                    ]
                                }
                            }
                        }
                    },
                    "options": {"type": "object"},
                    "fieldConfig": {"type": "object"}
                }
            }
        },
        "templating": {
            "type": "object",
            "properties": {
                "list": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "query": {"type": ["string", "object"]},
                            "current": {"type": "object"},
                            "hide": {"type": "integer"},
                            "label": {"type": ["string", "null"]}
                        },
                        "required": ["name", "type"]
                    }
                }
            }
        }
    }
}


def validate_dashboard_json(dashboard_json: Dict[str, Any]) -> DashboardValidationResult:
    """
    Validate a Grafana dashboard JSON against the schema.
    
    Args:
        dashboard_json: The dashboard JSON to validate
        
    Returns:
        DashboardValidationResult object with validation status and errors
    """
    errors = []
    is_valid = True
    
    try:
        jsonschema.validate(instance=dashboard_json, schema=GRAFANA_DASHBOARD_SCHEMA)
    except JSONSchemaValidationError as e:
        is_valid = False
        # Convert jsonschema error to our ValidationError model
        path = "/".join(str(p) for p in e.path) if e.path else "root"
        errors.append(
            ValidationError(
                path=path,
                message=e.message
            )
        )
    
    return DashboardValidationResult(
        is_valid=is_valid,
        errors=errors
    )


def extract_error_patterns(validation_result: DashboardValidationResult) -> List[str]:
    """
    Extract common error patterns from validation errors to help with fixes.
    
    Args:
        validation_result: The validation result containing errors
        
    Returns:
        List of human-readable error patterns with suggestions
    """
    patterns = []
    
    for error in validation_result.errors:
        if "required property" in error.message:
            property_name = error.message.split("'")[1]
            patterns.append(f"Missing required property '{property_name}' at path '{error.path}'")
        
        elif "is not of type" in error.message:
            expected_type = error.message.split("is not of type ")[1].strip("'")
            patterns.append(f"Type error at '{error.path}': expected {expected_type}")
        
        elif "is not valid under any of the given schemas" in error.message:
            patterns.append(f"Invalid value at '{error.path}': doesn't match any valid schema")
        
        else:
            patterns.append(f"Validation error at '{error.path}': {error.message}")
    
    return patterns 