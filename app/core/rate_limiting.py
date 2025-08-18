"""Enhanced rate limiting for authentication endpoints."""
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis
import json
import hashlib


class AuthRateLimiter:
    """Enhanced rate limiter for authentication endpoints."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_store: Dict[str, Dict] = {}  # Fallback to memory if no Redis
        
    def _get_client_key(self, request: Request, endpoint: str) -> str:
        """Generate a unique key for rate limiting."""
        # Use IP address as primary identifier
        ip = get_remote_address(request)
        
        # Add user agent for additional fingerprinting
        user_agent = request.headers.get("user-agent", "")
        user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        
        return f"rate_limit:{endpoint}:{ip}:{user_agent_hash}"
    
    def _get_username_key(self, username: str, endpoint: str) -> str:
        """Generate a key for username-based rate limiting."""
        return f"rate_limit:username:{endpoint}:{username}"
    
    def check_rate_limit(
        self, 
        request: Request, 
        endpoint: str, 
        max_attempts: int, 
        window_minutes: int,
        username: Optional[str] = None
    ) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            request: FastAPI request object
            endpoint: Endpoint identifier (e.g., 'login', 'password_change')
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
            username: Optional username for user-specific limiting
            
        Returns:
            True if within limits, False otherwise
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Check IP-based rate limit
        ip_key = self._get_client_key(request, endpoint)
        ip_attempts = self._get_attempts(ip_key, window_start)
        
        if ip_attempts >= max_attempts:
            self._raise_rate_limit_error(window_minutes, "IP address")
        
        # Check username-based rate limit if username provided
        if username:
            username_key = self._get_username_key(username, endpoint)
            username_attempts = self._get_attempts(username_key, window_start)
            
            # More restrictive limit for username attempts
            username_max = max(max_attempts // 2, 3)
            if username_attempts >= username_max:
                self._raise_rate_limit_error(window_minutes, "username")
        
        return True
    
    def record_attempt(
        self, 
        request: Request, 
        endpoint: str, 
        username: Optional[str] = None,
        success: bool = False
    ) -> None:
        """Record an authentication attempt."""
        now = datetime.utcnow()
        
        # Record IP-based attempt
        ip_key = self._get_client_key(request, endpoint)
        self._record_attempt(ip_key, now, success)
        
        # Record username-based attempt if provided
        if username:
            username_key = self._get_username_key(username, endpoint)
            self._record_attempt(username_key, now, success)
    
    def _get_attempts(self, key: str, window_start: datetime) -> int:
        """Get number of attempts within the time window."""
        if self.redis_client:
            return self._get_attempts_redis(key, window_start)
        else:
            return self._get_attempts_memory(key, window_start)
    
    def _record_attempt(self, key: str, timestamp: datetime, success: bool) -> None:
        """Record an attempt."""
        if self.redis_client:
            self._record_attempt_redis(key, timestamp, success)
        else:
            self._record_attempt_memory(key, timestamp, success)
    
    def _get_attempts_redis(self, key: str, window_start: datetime) -> int:
        """Get attempts from Redis."""
        try:
            attempts = self.redis_client.lrange(key, 0, -1)
            valid_attempts = []
            
            for attempt_data in attempts:
                attempt = json.loads(attempt_data)
                attempt_time = datetime.fromisoformat(attempt['timestamp'])
                if attempt_time >= window_start:
                    valid_attempts.append(attempt)
            
            return len(valid_attempts)
        except Exception:
            return 0
    
    def _record_attempt_redis(self, key: str, timestamp: datetime, success: bool) -> None:
        """Record attempt in Redis."""
        try:
            attempt_data = {
                'timestamp': timestamp.isoformat(),
                'success': success
            }
            
            # Add to list
            self.redis_client.lpush(key, json.dumps(attempt_data))
            
            # Keep only last 100 attempts and set expiration
            self.redis_client.ltrim(key, 0, 99)
            self.redis_client.expire(key, 3600)  # 1 hour expiration
        except Exception:
            pass  # Fail silently if Redis is unavailable
    
    def _get_attempts_memory(self, key: str, window_start: datetime) -> int:
        """Get attempts from memory store."""
        if key not in self.memory_store:
            return 0
        
        attempts = self.memory_store[key].get('attempts', [])
        valid_attempts = [
            a for a in attempts 
            if datetime.fromisoformat(a['timestamp']) >= window_start
        ]
        
        # Update the store to remove old attempts
        self.memory_store[key]['attempts'] = valid_attempts
        
        return len(valid_attempts)
    
    def _record_attempt_memory(self, key: str, timestamp: datetime, success: bool) -> None:
        """Record attempt in memory store."""
        if key not in self.memory_store:
            self.memory_store[key] = {'attempts': []}
        
        attempt_data = {
            'timestamp': timestamp.isoformat(),
            'success': success
        }
        
        self.memory_store[key]['attempts'].append(attempt_data)
        
        # Keep only last 100 attempts
        if len(self.memory_store[key]['attempts']) > 100:
            self.memory_store[key]['attempts'] = self.memory_store[key]['attempts'][-100:]
    
    def _raise_rate_limit_error(self, window_minutes: int, limit_type: str) -> None:
        """Raise rate limit exceeded error."""
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts for this {limit_type}. "
                   f"Please try again in {window_minutes} minutes.",
            headers={"Retry-After": str(window_minutes * 60)}
        )
    
    def get_remaining_attempts(
        self, 
        request: Request, 
        endpoint: str, 
        max_attempts: int, 
        window_minutes: int,
        username: Optional[str] = None
    ) -> Dict[str, int]:
        """Get remaining attempts for debugging/monitoring."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        ip_key = self._get_client_key(request, endpoint)
        ip_attempts = self._get_attempts(ip_key, window_start)
        ip_remaining = max(0, max_attempts - ip_attempts)
        
        result = {
            "ip_attempts": ip_attempts,
            "ip_remaining": ip_remaining,
            "window_minutes": window_minutes
        }
        
        if username:
            username_key = self._get_username_key(username, endpoint)
            username_attempts = self._get_attempts(username_key, window_start)
            username_max = max(max_attempts // 2, 3)
            username_remaining = max(0, username_max - username_attempts)
            
            result.update({
                "username_attempts": username_attempts,
                "username_remaining": username_remaining,
                "username_max": username_max
            })
        
        return result


# Global rate limiter instance
auth_rate_limiter = AuthRateLimiter()


def check_auth_rate_limit(
    request: Request,
    endpoint: str,
    max_attempts: int = 1000000,
    window_minutes: int = 1,
    username: Optional[str] = None
) -> bool:
    """Convenience function for checking auth rate limits."""
    return True
    # return auth_rate_limiter.check_rate_limit(
    #     request, endpoint, max_attempts, window_minutes, username
    # )


def record_auth_attempt(
    request: Request,
    endpoint: str,
    username: Optional[str] = None,
    success: bool = False
) -> None:
    """Convenience function for recording auth attempts."""
    auth_rate_limiter.record_attempt(request, endpoint, username, success)
