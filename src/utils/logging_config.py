"""
Advanced logging and debugging utilities for the AICTE workflow system.
Provides structured logging, performance monitoring, and debugging capabilities.
"""
import logging
import logging.handlers
import os
import sys
import time
import functools
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager

from .config import config


class WorkflowLogger:
    """Enhanced logger with workflow-specific features."""
    
    def __init__(self, name: str = "workflow"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.performance_data = {}
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger with configuration from config file."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Get logging configuration
        log_level = config.get('logging.level', 'INFO').upper()
        log_file = config.get('logging.file', 'logs/workflow.log')
        max_file_size = config.get('logging.max_file_size_mb', 10) * 1024 * 1024
        backup_count = config.get('logging.backup_count', 5)
        log_format = config.get('logging.format', 
                               '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_output = config.get('logging.console_output', True)
        
        # Set log level
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # File handler with rotation
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=max_file_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Error file handler
        error_log_path = log_path.parent / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path, maxBytes=max_file_size, backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message with optional extra data."""
        self._log_with_context(logging.INFO, message, extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message with optional extra data."""
        self._log_with_context(logging.DEBUG, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message with optional extra data."""
        self._log_with_context(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
              exc_info: bool = False) -> None:
        """Log error message with optional extra data and exception info."""
        self._log_with_context(logging.ERROR, message, extra, exc_info=exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, 
                 exc_info: bool = False) -> None:
        """Log critical message with optional extra data and exception info."""
        self._log_with_context(logging.CRITICAL, message, extra, exc_info=exc_info)
    
    def _log_with_context(self, level: int, message: str, 
                         extra: Optional[Dict[str, Any]] = None,
                         exc_info: bool = False) -> None:
        """Log message with additional context information."""
        # Add context information
        context = {
            'timestamp': datetime.now().isoformat(),
            'logger_name': self.name
        }
        
        if extra:
            context.update(extra)
        
        # Format message with context
        if context:
            context_str = json.dumps(context, default=str)
            formatted_message = f"{message} | Context: {context_str}"
        else:
            formatted_message = message
        
        self.logger.log(level, formatted_message, exc_info=exc_info)
    
    def log_step_start(self, step_id: int, step_name: str, 
                      project_name: str) -> None:
        """Log the start of a workflow step."""
        self.info(f"Step {step_id} started: {step_name}", {
            'step_id': step_id,
            'step_name': step_name,
            'project_name': project_name,
            'event_type': 'step_start'
        })
    
    def log_step_complete(self, step_id: int, step_name: str, 
                         project_name: str, duration: float) -> None:
        """Log the completion of a workflow step."""
        self.info(f"Step {step_id} completed: {step_name} (took {duration:.2f}s)", {
            'step_id': step_id,
            'step_name': step_name,
            'project_name': project_name,
            'duration_seconds': duration,
            'event_type': 'step_complete'
        })
    
    def log_step_error(self, step_id: int, step_name: str, 
                      project_name: str, error: Exception) -> None:
        """Log an error in a workflow step."""
        self.error(f"Step {step_id} failed: {step_name} - {str(error)}", {
            'step_id': step_id,
            'step_name': step_name,
            'project_name': project_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'event_type': 'step_error'
        }, exc_info=True)
    
    def log_api_call(self, service: str, method: str, url: str, 
                    status_code: Optional[int] = None, 
                    duration: Optional[float] = None) -> None:
        """Log API call information."""
        message = f"API call: {service}.{method} -> {url}"
        extra = {
            'service': service,
            'method': method,
            'url': url,
            'event_type': 'api_call'
        }
        
        if status_code is not None:
            message += f" (status: {status_code})"
            extra['status_code'] = status_code
        
        if duration is not None:
            message += f" (took {duration:.2f}s)"
            extra['duration_seconds'] = duration
        
        self.debug(message, extra)
    
    def log_performance_metric(self, metric_name: str, value: float, 
                              unit: str = "seconds") -> None:
        """Log performance metric."""
        self.info(f"Performance metric: {metric_name} = {value} {unit}", {
            'metric_name': metric_name,
            'metric_value': value,
            'metric_unit': unit,
            'event_type': 'performance_metric'
        })
    
    @contextmanager
    def performance_timer(self, operation_name: str):
        """Context manager for timing operations."""
        start_time = time.time()
        self.debug(f"Starting operation: {operation_name}")
        
        try:
            yield
            duration = time.time() - start_time
            self.debug(f"Completed operation: {operation_name} (took {duration:.2f}s)")
            self.log_performance_metric(f"{operation_name}_duration", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"Failed operation: {operation_name} after {duration:.2f}s - {str(e)}", 
                      exc_info=True)
            raise


class DebugManager:
    """Manages debugging features and utilities."""
    
    def __init__(self):
        self.debug_enabled = config.get('debug.verbose_output', False)
        self.save_api_responses = config.get('debug.save_api_responses', False)
        self.simulate_failures = config.get('debug.simulate_failures', False)
        self.debug_dir = Path("debug_output")
        
        if self.save_api_responses:
            self.debug_dir.mkdir(exist_ok=True)
    
    def save_api_response(self, service: str, method: str, 
                         response_data: Dict[str, Any]) -> None:
        """Save API response for debugging."""
        if not self.save_api_responses:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{service}_{method}_{timestamp}.json"
        filepath = self.debug_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(response_data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save API response: {e}")
    
    def should_simulate_failure(self, operation: str) -> bool:
        """Check if failure should be simulated for testing."""
        if not self.simulate_failures:
            return False
        
        # Simple probability-based failure simulation
        import random
        failure_rate = config.get('debug.failure_rate', 0.1)
        return random.random() < failure_rate
    
    def log_debug_info(self, info: Dict[str, Any]) -> None:
        """Log debug information if debug mode is enabled."""
        if self.debug_enabled:
            logger.debug("Debug info", extra=info)


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.log_performance_metric(f"{func_name}_execution_time", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Function {func_name} failed after {duration:.2f}s", 
                        {'function': func_name, 'duration': duration}, exc_info=True)
            raise
    
    return wrapper


def log_exceptions(func: Callable) -> Callable:
    """Decorator to automatically log exceptions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            func_name = f"{func.__module__}.{func.__name__}"
            logger.error(f"Exception in {func_name}: {str(e)}", 
                        {'function': func_name, 'exception_type': type(e).__name__}, 
                        exc_info=True)
            raise
    
    return wrapper


def setup_logging() -> WorkflowLogger:
    """Setup and return the main workflow logger."""
    return WorkflowLogger("workflow")


# Global logger instance
logger = setup_logging()
debug_manager = DebugManager()


class LogAnalyzer:
    """Analyzes log files for insights and troubleshooting."""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or config.get('logging.file', 'logs/workflow.log')
        self.log_path = Path(self.log_file)
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics from logs."""
        if not self.log_path.exists():
            return {"error": "Log file not found"}
        
        performance_data = {
            "step_durations": {},
            "api_call_durations": {},
            "error_count": 0,
            "total_operations": 0
        }
        
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    if "performance_metric" in line:
                        # Parse performance metrics
                        try:
                            if "step_complete" in line and "took" in line:
                                # Extract step duration
                                parts = line.split()
                                for i, part in enumerate(parts):
                                    if part.startswith("(took") and i + 1 < len(parts):
                                        duration_str = parts[i + 1].rstrip("s)")
                                        duration = float(duration_str)
                                        step_match = [p for p in parts if p.startswith("Step")]
                                        if step_match:
                                            step_id = step_match[0].replace("Step", "").replace(":", "")
                                            performance_data["step_durations"][step_id] = duration
                                        break
                        except (ValueError, IndexError):
                            continue
                    
                    if "ERROR" in line:
                        performance_data["error_count"] += 1
                    
                    performance_data["total_operations"] += 1
        
        except Exception as e:
            return {"error": f"Failed to analyze log: {str(e)}"}
        
        return performance_data
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors from the log file."""
        if not self.log_path.exists():
            return []
        
        errors = []
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    if "ERROR" in line or "CRITICAL" in line:
                        try:
                            # Simple timestamp extraction
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                            
                            if timestamp.timestamp() > cutoff_time:
                                errors.append({
                                    "timestamp": timestamp_str,
                                    "message": line.strip(),
                                    "level": "ERROR" if "ERROR" in line else "CRITICAL"
                                })
                        except (ValueError, IndexError):
                            continue
        
        except Exception as e:
            logger.warning(f"Could not analyze recent errors: {e}")
        
        return errors
    
    def generate_report(self) -> str:
        """Generate a comprehensive log analysis report."""
        performance = self.analyze_performance()
        recent_errors = self.get_recent_errors()
        
        report = []
        report.append("AICTE Workflow Log Analysis Report")
        report.append("=" * 40)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Log file: {self.log_file}")
        report.append("")
        
        # Performance summary
        report.append("Performance Summary:")
        report.append(f"  Total operations: {performance.get('total_operations', 0)}")
        report.append(f"  Error count: {performance.get('error_count', 0)}")
        
        if performance.get('step_durations'):
            report.append("  Step durations:")
            for step, duration in performance['step_durations'].items():
                report.append(f"    Step {step}: {duration:.2f}s")
        
        report.append("")
        
        # Recent errors
        if recent_errors:
            report.append(f"Recent Errors (last 24 hours): {len(recent_errors)}")
            for error in recent_errors[-5:]:  # Show last 5 errors
                report.append(f"  [{error['timestamp']}] {error['level']}: {error['message'][:100]}...")
        else:
            report.append("Recent Errors: None")
        
        return "\n".join(report)