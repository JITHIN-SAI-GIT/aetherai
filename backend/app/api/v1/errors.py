from fastapi import HTTPException
from fastapi.responses import JSONResponse
from .schemas.error_schema import OpenAIErrorResponse, OpenAIErrorDetail

def raise_invalid_request(message: str, param: str = None, code: str = "invalid_request_error"):
    raise HTTPException(
        status_code=400,
        detail=OpenAIErrorResponse(
            error=OpenAIErrorDetail(
                message=message,
                type="invalid_request_error",
                param=param,
                code=code
            )
        ).model_dump()
    )
    
def raise_api_error(message: str, code: str = "api_error"):
    raise HTTPException(
        status_code=500,
        detail=OpenAIErrorResponse(
            error=OpenAIErrorDetail(
                message=message,
                type="api_error",
                code=code
            )
        ).model_dump()
    )

def open_ai_exception_handler(request, exc):
    if hasattr(exc, "detail") and isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    
    status_code = getattr(exc, "status_code", 500)
    message = getattr(exc, "detail", str(exc))
    
    return JSONResponse(
        status_code=status_code,
        content=OpenAIErrorResponse(
            error=OpenAIErrorDetail(
                message=str(message),
                type="invalid_request_error" if status_code < 500 else "api_error"
            )
        ).model_dump()
    )
