import asyncio
import logging
from typing import Any, Callable, Dict
from functools import wraps
import time

logger = logging.getLogger(__name__)

class RetryConfig:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

class AgentError(Exception):
    def __init__(self, message: str, error_code: str = "AGENT_ERROR", details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class MemoryError(AgentError):
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "MEMORY_ERROR", details)

class QueryProcessingError(AgentError):
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "QUERY_ERROR", details)

def with_retry(config: RetryConfig = None):
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        logger.error(f"{func.__name__} failed after {config.max_retries} retries: {e}")
                        break
                    
                    delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                    logger.warning(f"{func.__name__} retry {attempt + 1} in {delay}s: {e}")
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

def with_error_handling(error_type: type = AgentError):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except error_type:
                raise
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise error_type(f"Error in {func.__name__}: {str(e)}", details={'original_error': str(e)})
        
        return wrapper
    return decorator

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    async def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise AgentError("Circuit breaker is OPEN", "CIRCUIT_BREAKER_OPEN")
        
        try:
            result = await func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")
            
            raise e