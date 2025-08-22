"""
Logging service for the LangChain playground.
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from .models import LoggingService


class SessionLogger:
    """Logger for a specific session."""
    
    def __init__(self, session_id: str, log_dir: str = "../session-data/logs"):
        self.session_id = session_id
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, f"session-{session_id}.log")
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """Ensure the log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _write_log(self, level: str, message: str, data: Dict[str, Any] = None):
        """Write a log entry."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "session_id": self.session_id,
            "message": message
        }
        
        if data:
            log_entry["data"] = data
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def log_info(self, message: str):
        """Log an info message."""
        self._write_log("INFO", message)
    
    def log_error(self, message: str):
        """Log an error message."""
        self._write_log("ERROR", message)
    
    def log_debug(self, message: str):
        """Log a debug message."""
        self._write_log("DEBUG", message)
    
    def log_api_call(self, endpoint: str, method: str, data: Dict[str, Any]):
        """Log an API call."""
        self._write_log("API_CALL", f"{method} {endpoint}", {
            "endpoint": endpoint,
            "method": method,
            "data": data
        })
    
    def log_api_response(self, endpoint: str, response_data: Dict[str, Any]):
        """Log an API response."""
        self._write_log("API_RESPONSE", f"Response for {endpoint}", {
            "endpoint": endpoint,
            "response": response_data
        })
    
    def log_llm_request(self, provider: str, model: str, prompt: str, 
                       system: Optional[str] = None, temperature: Optional[float] = None, 
                       max_tokens: Optional[int] = None):
        """Log an LLM request."""
        self._write_log("LLM_REQUEST", f"LLM request to {provider}/{model}", {
            "provider": provider,
            "model": model,
            "prompt_length": len(prompt),
            "system_length": len(system) if system else 0,
            "temperature": temperature,
            "max_tokens": max_tokens
        })
    
    def log_llm_response(self, provider: str, response: str, tokens_used: Optional[int] = None):
        """Log an LLM response."""
        self._write_log("LLM_RESPONSE", f"LLM response from {provider}", {
            "provider": provider,
            "response_length": len(response),
            "tokens_used": tokens_used
        })
    
    def log_llm_error(self, provider: str, error: str):
        """Log an LLM error."""
        self._write_log("LLM_ERROR", f"LLM error from {provider}", {
            "provider": provider,
            "error": error
        })
    
    def log_mcp_connection(self, connector: str, config: Dict[str, Any]):
        """Log an MCP connection attempt."""
        self._write_log("MCP_CONNECTION", f"MCP connection to {connector}", {
            "connector": connector,
            "config": config
        })
    
    def log_mcp_success(self, connector: str, result: Dict[str, Any]):
        """Log a successful MCP operation."""
        self._write_log("MCP_SUCCESS", f"MCP success for {connector}", {
            "connector": connector,
            "result": result
        })
    
    def log_mcp_error(self, connector: str, error: str):
        """Log an MCP error."""
        self._write_log("MCP_ERROR", f"MCP error for {connector}", {
            "connector": connector,
            "error": error
        })
    
    def log_optimization(self, original_prompt: str, optimized_prompt: str, debug: Dict[str, Any]):
        """Log a prompt optimization."""
        self._write_log("OPTIMIZATION", "Prompt optimization completed", {
            "original_length": len(original_prompt),
            "optimized_length": len(optimized_prompt),
            "debug": debug
        })


class LoggingServiceManager(LoggingService):
    """Main logging service manager."""
    
    def __init__(self, log_dir: str = "../session-data/logs"):
        self.log_dir = log_dir
        self._loggers: Dict[str, SessionLogger] = {}
    
    def get_logger(self, session_id: str) -> SessionLogger:
        """Get a logger for a specific session."""
        if session_id not in self._loggers:
            self._loggers[session_id] = SessionLogger(session_id, self.log_dir)
        return self._loggers[session_id]
    
    def log_info(self, message: str):
        """Log an info message to the default logger."""
        default_logger = self.get_logger("default")
        default_logger.log_info(message)
    
    def log_error(self, message: str):
        """Log an error message to the default logger."""
        default_logger = self.get_logger("default")
        default_logger.log_error(message)
    
    def log_api_call(self, endpoint: str, method: str, data: Dict[str, Any]):
        """Log an API call to the default logger."""
        default_logger = self.get_logger("default")
        default_logger.log_api_call(endpoint, method, data)
    
    def log_llm_request(self, provider: str, model: str, prompt: str, 
                       system: Optional[str] = None, temperature: Optional[float] = None, 
                       max_tokens: Optional[int] = None):
        """Log an LLM request to the default logger."""
        default_logger = self.get_logger("default")
        default_logger.log_llm_request(provider, model, prompt, system, temperature, max_tokens)
    
    def log_llm_response(self, provider: str, response: str, tokens_used: Optional[int] = None):
        """Log an LLM response to the default logger."""
        default_logger = self.get_logger("default")
        default_logger.log_llm_response(provider, response, tokens_used)
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get logs for a specific session."""
        log_file = os.path.join(self.log_dir, f"session-{session_id}.log")
        logs = []
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                log_entry = json.loads(line)
                                logs.append(log_entry)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        return logs
    
    def get_recent_logs(self, session_id: str, lines: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs for a specific session."""
        logs = self.get_session_logs(session_id)
        return logs[-lines:] if logs else []
    
    def clear_session_logs(self, session_id: str) -> bool:
        """Clear logs for a specific session."""
        log_file = os.path.join(self.log_dir, f"session-{session_id}.log")
        try:
            if os.path.exists(log_file):
                os.remove(log_file)
            return True
        except Exception as e:
            print(f"Error clearing log file: {e}")
            return False
    
    def get_all_session_ids(self) -> List[str]:
        """Get all available session IDs from log files."""
        session_ids = []
        
        if os.path.exists(self.log_dir):
            for filename in os.listdir(self.log_dir):
                if filename.startswith("session-") and filename.endswith(".log"):
                    session_id = filename[8:-4]  # Remove "session-" prefix and ".log" suffix
                    session_ids.append(session_id)
        
        return session_ids


# Global logging service instance
logging_service = LoggingServiceManager()
