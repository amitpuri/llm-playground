"""
Logging service for MCP Playground application.
Handles session-based logging of MCP and LLM communications.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class SessionLogger:
    """Session-based logger for MCP and LLM communications."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or self._generate_session_id()
        # Updated to use session-data/logs directory
        self.logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'session-data', 'logs')
        self.log_file = os.path.join(self.logs_dir, f'session_{self.session_id}.log')
        self.debug_log_file = os.path.join(self.logs_dir, f'debug_{self.session_id}.log')
        
        # Ensure logs directory exists
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set up file logger
        self.logger = logging.getLogger(f'session_{self.session_id}')
        self.logger.setLevel(logging.DEBUG)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Initialize session
        self.log_session_start()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return str(uuid.uuid4())[:8]
    
    def log_session_start(self):
        """Log session start."""
        self.logger.info(f"=== SESSION STARTED: {self.session_id} ===")
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info(f"Start Time: {datetime.now().isoformat()}")
        self.logger.info("=" * 50)
    
    def log_session_end(self):
        """Log session end."""
        self.logger.info("=" * 50)
        self.logger.info(f"End Time: {datetime.now().isoformat()}")
        self.logger.info(f"=== SESSION ENDED: {self.session_id} ===")
    
    def log_mcp_connection(self, connector_type: str, config: Dict[str, Any]):
        """Log MCP connection attempt."""
        self.logger.info(f"[MCP] Connecting to {connector_type.upper()}")
        self.logger.info(f"[MCP] Config: {json.dumps(config, indent=2, default=str)}")
    
    def log_mcp_success(self, connector_type: str, result: Dict[str, Any]):
        """Log successful MCP operation."""
        self.logger.info(f"[MCP] {connector_type.upper()} operation successful")
        self.logger.info(f"[MCP] Result summary: {len(result.get('issues', []))} issues, {len(result.get('rows', []))} rows")
        if 'debug' in result:
            self.logger.debug(f"[MCP] Debug info: {json.dumps(result['debug'], indent=2, default=str)}")
    
    def log_mcp_error(self, connector_type: str, error: str):
        """Log MCP error."""
        self.logger.error(f"[MCP] {connector_type.upper()} error: {error}")
    
    def log_llm_request(self, provider: str, model: str, prompt: str, system: str = None, 
                       temperature: float = None, max_tokens: int = None):
        """Log LLM request."""
        self.logger.info(f"[LLM] Request to {provider.upper()}")
        self.logger.info(f"[LLM] Model: {model}")
        self.logger.info(f"[LLM] Temperature: {temperature}")
        self.logger.info(f"[LLM] Max tokens: {max_tokens}")
        self.logger.info(f"[LLM] System prompt: {system[:200] + '...' if system and len(system) > 200 else system}")
        self.logger.info(f"[LLM] User prompt: {prompt[:500] + '...' if len(prompt) > 500 else prompt}")
    
    def log_llm_response(self, provider: str, response: str, tokens_used: int = None):
        """Log LLM response."""
        self.logger.info(f"[LLM] Response from {provider.upper()}")
        if tokens_used:
            self.logger.info(f"[LLM] Tokens used: {tokens_used}")
        self.logger.info(f"[LLM] Response: {response[:1000] + '...' if len(response) > 1000 else response}")
    
    def log_llm_error(self, provider: str, error: str):
        """Log LLM error."""
        self.logger.error(f"[LLM] {provider.upper()} error: {error}")
    
    def log_optimization(self, user_prompt: str, optimized_prompt: str, debug_info: Dict[str, Any]):
        """Log prompt optimization."""
        self.logger.info("[OPTIMIZATION] Prompt optimization completed")
        self.logger.info(f"[OPTIMIZATION] Original prompt length: {len(user_prompt)}")
        self.logger.info(f"[OPTIMIZATION] Optimized prompt length: {len(optimized_prompt)}")
        self.logger.debug(f"[OPTIMIZATION] Debug info: {json.dumps(debug_info, indent=2, default=str)}")
    
    def log_api_call(self, endpoint: str, method: str, data: Dict[str, Any] = None):
        """Log API call."""
        self.logger.info(f"[API] {method} {endpoint}")
        if data:
            self.logger.debug(f"[API] Request data: {json.dumps(data, indent=2, default=str)}")
    
    def log_api_response(self, endpoint: str, response: Dict[str, Any]):
        """Log API response."""
        self.logger.info(f"[API] Response from {endpoint}")
        self.logger.debug(f"[API] Response data: {json.dumps(response, indent=2, default=str)}")
    
    def log_error(self, error: str, context: str = None):
        """Log general error."""
        if context:
            self.logger.error(f"[ERROR] {context}: {error}")
        else:
            self.logger.error(f"[ERROR] {error}")
    
    def log_info(self, message: str, context: str = None):
        """Log general info."""
        if context:
            self.logger.info(f"[INFO] {context}: {message}")
        else:
            self.logger.info(f"[INFO] {message}")
    
    def log_debug(self, message: str, context: str = None):
        """Log debug message."""
        if context:
            self.logger.debug(f"[DEBUG] {context}: {message}")
        else:
            self.logger.debug(f"[DEBUG] {message}")
    
    def log_warning(self, message: str, context: str = None):
        """Log warning message."""
        if context:
            self.logger.warning(f"[WARNING] {context}: {message}")
        else:
            self.logger.warning(f"[WARNING] {message}")
    
    def get_session_logs(self) -> str:
        """Get all logs for the current session."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"No log file found for session {self.session_id}"
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
    def get_recent_logs(self, lines: int = 100) -> str:
        """Get recent logs (last N lines)."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except FileNotFoundError:
            return f"No log file found for session {self.session_id}"
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
    def clear_logs(self):
        """Clear current session logs."""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            if os.path.exists(self.debug_log_file):
                os.remove(self.debug_log_file)
            self.logger.info("Logs cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear logs: {e}")
    
    def get_log_file_path(self) -> str:
        """Get the path to the current log file."""
        return self.log_file
    
    def get_debug_log_file_path(self) -> str:
        """Get the path to the current debug log file."""
        return self.debug_log_file


class LoggingService:
    """Service for managing multiple session loggers."""
    
    def __init__(self):
        self.session_loggers: Dict[str, SessionLogger] = {}
    
    def get_logger(self, session_id: str = None) -> SessionLogger:
        """Get or create a logger for the given session."""
        if session_id not in self.session_loggers:
            self.session_loggers[session_id] = SessionLogger(session_id)
        return self.session_loggers[session_id]
    
    def get_session_logs(self, session_id: str) -> str:
        """Get logs for a specific session."""
        if session_id not in self.session_loggers:
            return f"No logger found for session {session_id}"
        return self.session_loggers[session_id].get_session_logs()
    
    def get_recent_logs(self, session_id: str, lines: int = 100) -> str:
        """Get recent logs for a specific session."""
        if session_id not in self.session_loggers:
            return f"No logger found for session {session_id}"
        return self.session_loggers[session_id].get_recent_logs(lines)
    
    def clear_session_logs(self, session_id: str):
        """Clear logs for a specific session."""
        if session_id in self.session_loggers:
            self.session_loggers[session_id].clear_logs()
    
    def get_all_session_ids(self) -> list:
        """Get all active session IDs."""
        return list(self.session_loggers.keys())
    
    def get_log_file_path(self, session_id: str) -> str:
        """Get the log file path for a specific session."""
        if session_id in self.session_loggers:
            return self.session_loggers[session_id].get_log_file_path()
        return ""
    
    def cleanup_old_sessions(self, max_sessions: int = 10):
        """Clean up old sessions, keeping only the most recent ones."""
        if len(self.session_loggers) <= max_sessions:
            return
        
        # Sort sessions by creation time (this would need to be tracked)
        # For now, just keep the most recent ones based on session ID
        session_ids = sorted(self.session_loggers.keys())
        sessions_to_remove = session_ids[:-max_sessions]
        
        for session_id in sessions_to_remove:
            del self.session_loggers[session_id]


# Global logging service instance
logging_service = LoggingService()
