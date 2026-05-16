"""
middleware.py — Custom middlewares and metrics tracking
"""

import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .utils import logger

class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # We can't safely access app.state here because 'app' might be another middleware.
        # We will initialize metrics in the first dispatch call if they don't exist.

    async def dispatch(self, request: Request, call_next) -> Response:
        # Safely ensure metrics exist on the main app state
        if not hasattr(request.app.state, "metrics"):
            request.app.state.metrics = {
                "total_requests": 0,
                "failed_requests": 0,
                "total_latency_ms": 0.0,
                "moderation_hits": 0
            }
            
        metrics = request.app.state.metrics
        metrics["total_requests"] += 1

        start_time = time.perf_counter()
        
        request.state.metrics = metrics

        try:
            response = await call_next(request)
            
            # Check for moderation hits (passed via headers in our setup)
            if response.headers.get("X-Is-Safe") == "false":
                metrics["moderation_hits"] += 1
                
            if response.status_code >= 400:
                metrics["failed_requests"] += 1
                
        except Exception as e:
            metrics["failed_requests"] += 1
            logger.error(f"Request failed: {str(e)}")
            raise e
        finally:
            latency = (time.perf_counter() - start_time) * 1000
            metrics["total_latency_ms"] += latency
            
            # Request logging
            logger.info(json.dumps({
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
                "latency_ms": round(latency, 2),
                "status": response.status_code if 'response' in locals() else 500
            }))

        return response
