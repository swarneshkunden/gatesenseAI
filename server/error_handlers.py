import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("volunteer_copilot")

def register_error_handlers(app):
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Format the validation errors nicely
        errors = []
        for error in exc.errors():
            # Get the field path
            loc = ".".join(str(l) for l in error.get("loc", []))
            # Remove body prefix if present
            loc = loc.replace("body.", "").replace("query.", "").replace("path.", "")
            errors.append({
                "field": loc,
                "message": error.get("msg", "Invalid value")
            })
            
        logger.warning(f"Validation failed on {request.url.path}: {errors}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": "Validation failed",
                "errors": errors
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTP error {exc.status_code} on {request.url.path}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # Log the full stack trace on the server side
        logger.exception(f"Unhandled system exception occurred on {request.url.path}: {str(exc)}")
        
        # Enforce ZERO information leakage in production/development
        # Do not expose internal details like paths, DB schemas, or code line numbers
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "An unexpected error occurred. Please contact stadium operations if this persists."
            }
        )
