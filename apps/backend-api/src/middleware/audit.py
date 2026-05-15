import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.db.session import SessionLocal
from src.models.models import AuditLog

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # We only want to log state-mutating requests
        if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
            return await call_next(request)

        # Attempt to read request body
        try:
            # We need to receive the body, but also make it available for the actual route
            body_bytes = await request.body()
            
            # Create a new receive function to return the bytes we just consumed
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
            
            payload = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
        except Exception:
            payload = {}

        # Proceed with the request
        response = await call_next(request)

        # Skip logging for safe/auth endpoints if needed, but for now log all mutative actions
        if "auth" in request.url.path or "login" in request.url.path:
            # Avoid logging credentials
            payload = {"hidden": "true"}

        # Determine user/organization from request state if available
        # (This depends on how Auth middleware attaches user info to request.state)
        user = getattr(request.state, "user", None)
        organization_id = getattr(request.state, "organization_id", None)
        
        # We might not have org_id if it's an unauthenticated request or malformed
        if user and user.organizations and not organization_id:
            organization_id = user.organizations[0].id
            
        # Log to DB
        if organization_id:
            try:
                async with SessionLocal() as db:
                    audit_entry = AuditLog(
                        organization_id=organization_id,
                        user_id=user.id if user else None,
                        action=f"{request.method} {request.url.path}",
                        resource_type="api_request",
                        payload=payload,
                        ip_address=request.client.host if request.client else None
                    )
                    db.add(audit_entry)
                    await db.commit()
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")

        return response
