"""
Grafana dashboard JSON schema and validation utilities.
"""

import json
from typing import Any, Dict, List, Tuple

import jsonschema
from jsonschema import validators
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError

from app.schemas.models import DashboardValidationResult, ValidationError

# Enhanced version of the Grafana dashboard schema with documentation
# This schema includes documentation for each field to provide context for the generation
GRAFANA_DASHBOARD_SCHEMA = {
    "type": "object",
    "description": "Grafana dashboard configuration schema with detailed documentation for each field",
    "required": ["panels", "title"],
    "properties": {
        "id": {
            "type": "integer",
            "description": "Unique numeric identifier for the dashboard"
        },
        "uid": {
            "type": "string",
            "description": "Unique dashboard identifier that can be used in URLs"
        },
        "title": {
            "type": "string",
            "description": "Title of the dashboard displayed at the top"
        },
        "description": {
            "type": "string",
            "description": "Detailed dashboard description providing context about its purpose and content"
        },
        "tags": {
            "type": "array",
            "description": "List of tags for categorizing and filtering dashboards",
            "items": {"type": "string"}
        },
        "timezone": {
            "type": "string",
            "description": "Timezone used for date display (e.g., 'browser', 'utc')",
            "default": "browser"
        },
        "schemaVersion": {
            "type": "integer",
            "description": "Version of the dashboard schema being used"
        },
        "version": {
            "type": "integer",
            "description": "Dashboard revision number for tracking changes"
        },
        "refresh": {
            "type": ["string", "null"],
            "description": "Auto-refresh interval (e.g., '5s', '1m', '30m', '1h', '1d')"
        },
        "time": {
            "type": "object",
            "description": "Default time range for the dashboard",
            "properties": {
                "from": {
                    "type": "string",
                    "description": "Start time (e.g., 'now-6h', 'now-1d')"
                },
                "to": {
                    "type": "string",
                    "description": "End time (e.g., 'now')"
                }
            },
            "required": ["from", "to"]
        },
        "panels": {
            "type": "array",
            "description": "Array of visualization panels in the dashboard",
            "items": {
                "type": "object",
                "required": ["id", "type", "title"],
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Unique numeric identifier for the panel within the dashboard"
                    },
                    "type": {
                        "type": "string",
                        "description": "Panel visualization type (e.g., 'graph', 'stat', 'gauge', 'table', 'timeseries', 'heatmap', 'logs', 'bar', 'piechart')",
                        "enum": [
                            "graph", "stat", "gauge", "table", "timeseries", 
                            "heatmap", "logs", "bar", "piechart", "text",
                            "singlestat", "dashlist", "alertlist", "row",
                            "bargauge", "barchart", "histogram", "news", "pie",
                            "canvas", "geomap", "xychart", "candlestick"
                        ]
                    },
                    "title": {
                        "type": "string",
                        "description": "Title displayed at the top of the panel"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the panel content and purpose"
                    },
                    "gridPos": {
                        "type": "object",
                        "description": "Panel position and size in the dashboard grid",
                        "properties": {
                            "h": {
                                "type": "integer",
                                "description": "Panel height in grid units"
                            },
                            "w": {
                                "type": "integer",
                                "description": "Panel width in grid units (max 24)"
                            },
                            "x": {
                                "type": "integer",
                                "description": "X position from the left in grid units"
                            },
                            "y": {
                                "type": "integer",
                                "description": "Y position from the top in grid units"
                            }
                        },
                        "required": ["h", "w", "x", "y"]
                    },
                    "datasource": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "object",
                                "required": ["type", "uid"],
                                "description": "Data source configuration for the panel",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "description": "Type of data source (e.g., 'prometheus', 'mysql', 'postgres')"
                                    },
                                    "uid": {
                                        "type": "string",
                                        "description": "Unique identifier for the data source"
                                    }
                                }
                            },
                            {"type": "null"}
                        ]
                    },
                    "targets": {
                        "type": "array",
                        "description": "Query targets to fetch data for the panel",
                        "items": {
                            "type": "object",
                            "properties": {
                                "refId": {
                                    "type": "string",
                                    "description": "Reference ID for the target (e.g., 'A', 'B')"
                                },
                                "expr": {
                                    "type": "string",
                                    "description": "Query expression (e.g., Prometheus query, SQL query)"
                                },
                                "format": {
                                    "type": "string",
                                    "description": "Output format (e.g., 'time_series', 'table')",
                                    "enum": ["time_series", "table", "heatmap", "logs"]
                                },
                                "intervalMs": {
                                    "type": "integer",
                                    "description": "Query resolution in milliseconds"
                                },
                                "legendFormat": {
                                    "type": "string",
                                    "description": "Format for legend labels"
                                },
                                "datasource": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {
                                            "type": "object",
                                            "required": ["type", "uid"],
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "description": "Type of data source for this specific target"
                                                },
                                                "uid": {
                                                    "type": "string",
                                                    "description": "Unique identifier for this target's data source"
                                                }
                                            }
                                        },
                                        {"type": "null"}
                                    ]
                                },
                                "rawSql": {
                                    "type": "string",
                                    "description": "Raw SQL query for SQL data sources"
                                },
                                "rawQuery": {
                                    "type": "boolean",
                                    "description": "Whether to use raw query mode"
                                }
                            }
                        }
                    },
                    "options": {
                        "type": "object",
                        "description": "Visualization options specific to the panel type"
                    },
                    "fieldConfig": {
                        "type": "object",
                        "description": "Field configuration options for the panel",
                        "properties": {
                            "defaults": {
                                "type": "object",
                                "description": "Default field options",
                                "properties": {
                                    "unit": {
                                        "type": "string",
                                        "description": "Unit for values (e.g., 'bytes', 'percent', 's')"
                                    },
                                    "min": {
                                        "type": ["number", "null"],
                                        "description": "Minimum value for the scale"
                                    },
                                    "max": {
                                        "type": ["number", "null"],
                                        "description": "Maximum value for the scale"
                                    },
                                    "decimals": {
                                        "type": ["integer", "null"],
                                        "description": "Number of decimal places to display"
                                    },
                                    "thresholds": {
                                        "type": "object",
                                        "description": "Threshold configuration for color changes",
                                        "properties": {
                                            "mode": {
                                                "type": "string",
                                                "description": "Threshold mode (absolute or percentage)",
                                                "enum": ["absolute", "percentage"]
                                            },
                                            "steps": {
                                                "type": "array",
                                                "description": "Threshold steps with color changes",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "color": {
                                                            "type": "string",
                                                            "description": "Color for this threshold range"
                                                        },
                                                        "value": {
                                                            "type": ["number", "null"],
                                                            "description": "Threshold value"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "color": {
                                        "type": "object",
                                        "description": "Color configuration",
                                        "properties": {
                                            "mode": {
                                                "type": "string",
                                                "description": "Color mode (e.g., 'palette-classic', 'continuous-BlYlRd')",
                                                "enum": ["value", "palette-classic", "fixed", "continuous-GrYlRd", "continuous-RdYlGr", "continuous-BlYlRd"]
                                            }
                                        }
                                    }
                                }
                            },
                            "overrides": {
                                "type": "array",
                                "description": "Field option overrides for specific fields",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "matcher": {
                                            "type": "object",
                                            "description": "Matcher for selecting which fields to override",
                                            "properties": {
                                                "id": {
                                                    "type": "string",
                                                    "description": "Matcher ID (e.g., 'byName', 'byRegexp')"
                                                },
                                                "options": {
                                                    "type": ["string", "object"],
                                                    "description": "Matcher options"
                                                }
                                            }
                                        },
                                        "properties": {
                                            "type": "array",
                                            "description": "Properties to override",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string",
                                                        "description": "Property ID to override (e.g., 'unit', 'color')"
                                                    },
                                                    "value": {
                                                        "type": ["string", "number", "boolean", "object", "null"],
                                                        "description": "Override value"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "links": {
                        "type": "array",
                        "description": "Panel links for navigation",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Link title"
                                },
                                "url": {
                                    "type": "string",
                                    "description": "URL for the link"
                                },
                                "targetBlank": {
                                    "type": "boolean",
                                    "description": "Whether to open in a new tab"
                                }
                            }
                        }
                    }
                }
            }
        },
        "templating": {
            "type": "object",
            "description": "Dashboard template variables configuration",
            "properties": {
                "list": {
                    "type": "array",
                    "description": "List of template variables",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Variable name (used in queries with $varname format)"
                            },
                            "type": {
                                "type": "string",
                                "description": "Variable type (e.g., 'query', 'custom', 'interval')",
                                "enum": ["query", "custom", "interval", "datasource", "textbox", "constant", "adhoc"]
                            },
                            "query": {
                                "type": ["string", "object"],
                                "description": "Query used to populate variable options"
                            },
                            "current": {
                                "type": "object",
                                "description": "Currently selected value",
                                "properties": {
                                    "value": {
                                        "type": ["string", "array", "null"],
                                        "description": "Current selected value(s)"
                                    },
                                    "text": {
                                        "type": ["string", "array", "null"],
                                        "description": "Display text for the current value(s)"
                                    },
                                    "selected": {
                                        "type": "boolean",
                                        "description": "Whether this value is selected"
                                    }
                                }
                            },
                            "hide": {
                                "type": "integer",
                                "description": "Hide variable: 0=don't hide, 1=hide label, 2=hide variable",
                                "enum": [0, 1, 2]
                            },
                            "label": {
                                "type": ["string", "null"],
                                "description": "Display label for the variable"
                            },
                            "multi": {
                                "type": "boolean",
                                "description": "Whether multiple values can be selected"
                            },
                            "includeAll": {
                                "type": "boolean",
                                "description": "Include 'All' option"
                            },
                            "options": {
                                "type": "array",
                                "description": "Available options for custom variables",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "Display text"
                                        },
                                        "value": {
                                            "type": ["string", "number"],
                                            "description": "Actual value"
                                        },
                                        "selected": {
                                            "type": "boolean",
                                            "description": "Whether this option is selected"
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["name", "type"]
                    }
                }
            }
        },
        "annotations": {
            "type": "object",
            "description": "Event annotations configuration",
            "properties": {
                "list": {
                    "type": "array",
                    "description": "List of annotation queries",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Annotation name"
                            },
                            "datasource": {
                                "type": ["object", "string"],
                                "description": "Datasource for annotations"
                            },
                            "enable": {
                                "type": "boolean",
                                "description": "Whether annotation is enabled"
                            },
                            "iconColor": {
                                "type": "string",
                                "description": "Color of annotation icon"
                            }
                        }
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


def get_panel_type_documentation() -> Dict[str, str]:
    """
    Get documentation for Grafana panel types.
    
    Returns:
        Dictionary of panel type documentations
    """
    return {
        "graph": "Traditional graph panel for time series data with multiple visualization options",
        "timeseries": "Modern replacement for the graph panel with improved performance and features",
        "stat": "Show a single big stat value with optional sparkline and thresholds",
        "gauge": "Radial gauge visualization for displaying a value within a range",
        "table": "Shows data in a table format with column formatting options",
        "heatmap": "Visualize data as a heatmap with color-coded cells",
        "logs": "Display and search through log lines from logs datasources",
        "bar": "Horizontal bar chart for comparing values across categories",
        "piechart": "Display data as a pie chart to show proportions of a whole",
        "text": "Panel for displaying text or markdown content",
        "singlestat": "Legacy single stat panel (deprecated in favor of 'stat')",
        "dashlist": "Display a list of dashboards with links",
        "alertlist": "Display a list of alerts with their status",
        "row": "Group panels together in a collapsible container",
        "bargauge": "Horizontal or vertical gauge for displaying values with thresholds",
        "barchart": "Modern bar chart for comparing values across categories",
        "histogram": "Show data distribution using histograms",
        "news": "Display RSS feeds",
        "geomap": "Display geographical data on interactive maps",
        "xychart": "Plot data on a Cartesian (X/Y) coordinate system",
        "candlestick": "Financial chart for displaying price movements of securities"
    } 