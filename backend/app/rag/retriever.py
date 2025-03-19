"""
RAG retrieval module for enhancing dashboard generation with contextual information.
"""

import json
from typing import Any, Dict, List, Optional

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
    
    # If no specific matches, provide general dashboard structure
    if not context:
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
    
    for key, value in context.items():
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