"""
RAG retrieval module for enhancing dashboard generation with contextual information.
"""

import json
from typing import Any, Dict, List, Optional

from app.schemas.grafana_schema import GRAFANA_DASHBOARD_SCHEMA, get_panel_type_documentation

# Sample contexts that would be stored in a vector DB in a real application
SAMPLE_CONTEXTS = {
    "sql_queries": {
        "prometheus": {
            "cpu_usage": 'rate(node_cpu_seconds_total{mode="idle"}[5m])',
            "memory_usage": 'node_memory_MemTotal_bytes - node_memory_MemFree_bytes',
            "disk_usage": 'node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100',
        },
        "mysql": {
            "query_rate": "SELECT COUNT(*) as query_count, DATE_FORMAT(event_time, '%Y-%m-%d %H:%i:%s') as time FROM mysql_query_log GROUP BY time",
            "slow_queries": "SELECT query_text, execution_time FROM mysql_slow_log WHERE execution_time > 1.0 ORDER BY execution_time DESC",
            "connection_count": "SELECT COUNT(*) as connections FROM information_schema.processlist",
        },
        "postgres": {
            "active_connections": "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'",
            "database_size": "SELECT pg_database_size(current_database())",
            "index_usage": "SELECT relname, idx_scan, seq_scan FROM pg_stat_user_tables ORDER BY idx_scan DESC",
        }
    },
    "log_formats": {
        "nginx": {
            "access_log": "{'timestamp': 'datetime', 'remote_addr': 'ip', 'request': 'string', 'status': 'integer', 'bytes_sent': 'integer', 'http_referer': 'string', 'http_user_agent': 'string'}",
            "error_log": "{'timestamp': 'datetime', 'level': 'string', 'pid': 'integer', 'message': 'string'}"
        },
        "application": {
            "json_logs": "{'timestamp': 'datetime', 'level': 'string', 'service': 'string', 'trace_id': 'string', 'message': 'string', 'context': 'object'}",
        }
    },
    "dashboard_examples": {
        "system_monitoring": {
            "description": "Dashboard with CPU, memory, disk, and network metrics for system monitoring",
            "panels": ["CPU Usage", "Memory Usage", "Disk I/O", "Network Traffic"]
        },
        "application_performance": {
            "description": "Dashboard for tracking API performance including request rate, latency, and error rate",
            "panels": ["Request Rate", "P95 Latency", "Error Rate", "Dependency Health"]
        },
        "database_monitoring": {
            "description": "Dashboard for monitoring database performance and health",
            "panels": ["Query Rate", "Slow Queries", "Connection Count", "Cache Hit Ratio"]
        }
    }
}


def extract_schema_documentation() -> Dict[str, Any]:
    """
    Extract and format documentation from the Grafana dashboard schema.
    
    Returns:
        Dictionary with documentation from the schema
    """
    schema_docs = {
        "dashboard_structure": {},
        "panel_types": get_panel_type_documentation(),
        "required_fields": {}
    }
    
    # Extract dashboard level documentation
    for prop, details in GRAFANA_DASHBOARD_SCHEMA["properties"].items():
        if isinstance(details, dict) and "description" in details:
            schema_docs["dashboard_structure"][prop] = details["description"]
    
    # Extract panel properties documentation
    panel_props = GRAFANA_DASHBOARD_SCHEMA["properties"]["panels"]["items"]["properties"]
    schema_docs["panel_properties"] = {}
    for prop, details in panel_props.items():
        if isinstance(details, dict) and "description" in details:
            schema_docs["panel_properties"][prop] = details["description"]
    
    # Extract required fields
    schema_docs["required_fields"]["dashboard"] = GRAFANA_DASHBOARD_SCHEMA["required"]
    schema_docs["required_fields"]["panel"] = panel_props["gridPos"]["required"]
    
    return schema_docs


def get_rag_context(prompt: str) -> Dict[str, Any]:
    """
    Retrieve relevant context based on the user prompt.
    
    In a production system, this would use a vector DB or other retrieval system.
    This simplified version uses keyword matching to find relevant contexts.
    
    Args:
        prompt: The user's dashboard generation prompt
        
    Returns:
        Dictionary with relevant context information
    """
    prompt_lower = prompt.lower()
    context = {}
    
    # Always include schema documentation for enhanced generation
    context["grafana_schema"] = extract_schema_documentation()
    
    # Check for database-related terms
    if any(db in prompt_lower for db in ["mysql", "sql", "database", "query"]):
        context["sql_examples"] = SAMPLE_CONTEXTS["sql_queries"]["mysql"]
        if "mysql" in prompt_lower:
            context["sql_examples"] = SAMPLE_CONTEXTS["sql_queries"]["mysql"]
        elif "postgres" in prompt_lower:
            context["sql_examples"] = SAMPLE_CONTEXTS["sql_queries"]["postgres"]
    
    # Check for metrics and monitoring
    if any(term in prompt_lower for term in ["prometheus", "metrics", "monitoring", "cpu", "memory"]):
        context["metrics_examples"] = SAMPLE_CONTEXTS["sql_queries"]["prometheus"]
        context["system_dashboard_example"] = SAMPLE_CONTEXTS["dashboard_examples"]["system_monitoring"]
    
    # Check for logs
    if any(term in prompt_lower for term in ["logs", "logging", "nginx", "error log"]):
        context["log_formats"] = SAMPLE_CONTEXTS["log_formats"]["nginx"]
        if "nginx" in prompt_lower:
            context["log_formats"] = SAMPLE_CONTEXTS["log_formats"]["nginx"]
        elif "application" in prompt_lower or "json" in prompt_lower:
            context["log_formats"] = SAMPLE_CONTEXTS["log_formats"]["application"]
    
    # Check for application performance
    if any(term in prompt_lower for term in ["api", "latency", "performance", "error rate"]):
        context["application_dashboard_example"] = SAMPLE_CONTEXTS["dashboard_examples"]["application_performance"]
    
    # Check for specific visualization types
    visualization_keywords = {
        "graph": ["line graph", "time series", "trend"],
        "gauge": ["gauge", "meter", "dial"],
        "stat": ["single stat", "big number", "kpi"],
        "table": ["table", "tabular", "grid"],
        "heatmap": ["heatmap", "heat map", "density"],
        "pie": ["pie chart", "donut", "proportion"]
    }
    
    for viz_type, keywords in visualization_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            if "recommended_visualizations" not in context:
                context["recommended_visualizations"] = {}
            context["recommended_visualizations"][viz_type] = context["grafana_schema"]["panel_types"].get(viz_type, "")
    
    # If no specific matches except schema, provide general dashboard structure
    if len(context) <= 1:
        context["general_dashboard_examples"] = SAMPLE_CONTEXTS["dashboard_examples"]
    
    return context


def format_rag_context_as_text(context: Dict[str, Any]) -> str:
    """
    Format the RAG context as plain text for inclusion in prompts.
    
    Args:
        context: The RAG context dictionary
        
    Returns:
        Formatted text representation of the context
    """
    if not context:
        return "No additional context available."
    
    result = []
    
    # Process schema information first if available
    if "grafana_schema" in context:
        schema = context["grafana_schema"]
        
        result.append("## Grafana Dashboard Schema")
        
        if "panel_types" in schema:
            result.append("\n### Available Panel Types")
            for panel_type, description in schema["panel_types"].items():
                result.append(f"- **{panel_type}**: {description}")
            result.append("")
        
        if "dashboard_structure" in schema:
            result.append("\n### Dashboard Structure")
            for field, description in schema["dashboard_structure"].items():
                result.append(f"- **{field}**: {description}")
            result.append("")
        
        if "panel_properties" in schema:
            result.append("\n### Panel Properties")
            for field, description in schema["panel_properties"].items():
                result.append(f"- **{field}**: {description}")
            result.append("")
        
        if "required_fields" in schema:
            result.append("\n### Required Fields")
            result.append("For dashboard: " + ", ".join(schema["required_fields"].get("dashboard", [])))
            result.append("For panels: " + ", ".join(schema["required_fields"].get("panel", [])))
            result.append("")
    
    # Process other context items
    for key, value in context.items():
        if key == "grafana_schema":
            continue  # Already processed
            
        result.append(f"## {key.replace('_', ' ').title()}")
        
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                if isinstance(subvalue, dict):
                    result.append(f"\n### {subkey.replace('_', ' ').title()}")
                    for k, v in subvalue.items():
                        result.append(f"- {k.replace('_', ' ').title()}: {v}")
                else:
                    result.append(f"- {subkey.replace('_', ' ').title()}: {subvalue}")
        else:
            result.append(str(value))
        
        result.append("")  # Add blank line between sections
    
    return "\n".join(result) 