"""Safe API errors and correlation IDs; never log request bodies or credentials."""
import logging
import time
import traceback
import uuid
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
logger=logging.getLogger("sci.api")
CODES={400:"invalid_request",401:"authentication_required",403:"forbidden",404:"not_found",405:"method_not_allowed",409:"conflict",413:"file_too_large",422:"validation_error",429:"rate_limited",500:"internal_error",502:"upstream_error",503:"unavailable",504:"timeout"}
def error_response(request,status,detail,headers=None):
    return JSONResponse({"detail":detail,"code":CODES.get(status,"request_failed"),"request_id":getattr(request.state,"request_id","")},status_code=status,headers=headers)
def install_error_handling(app):
    @app.exception_handler(HTTPException)
    async def http_error(request,exc):
        detail=exc.detail if isinstance(exc.detail,str) and exc.status_code<500 else "ระบบขัดข้องชั่วคราว กรุณาลองภายหลัง"
        return error_response(request,exc.status_code,detail,exc.headers)
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        # Pydantic error input/context can include passwords; never serialize them.
        message="ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบช่องที่จำเป็นและรูปแบบข้อมูล"
        if request.url.path.endswith("/messages"): message+=" (คำถามต้องมี 1–1,500 ตัวอักษร)"
        return error_response(request,422,message)
    @app.middleware("http")
    async def request_errors(request,call_next):
        request.state.request_id=uuid.uuid4().hex[:12]
        started=time.monotonic()
        try:
            response=await call_next(request)
        except Exception as exc:
            frames=traceback.extract_tb(exc.__traceback__)[-4:]
            # Frame names/line numbers only: exception messages may contain SQL values.
            logger.error("api_exception request_id=%s type=%s frames=%s",request.state.request_id,type(exc).__name__,[(f.name,f.lineno) for f in frames])
            response=error_response(request,500,"ระบบขัดข้องชั่วคราว กรุณาลองภายหลัง")
        response.headers["X-Request-ID"]=request.state.request_id
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
        response.headers["Cache-Control"]="no-store"
        if response.status_code>=400:
            route=getattr(request.scope.get("route"),"path","unmatched")
            logger.warning("api_request_failed request_id=%s method=%s route=%s status=%s elapsed_ms=%s",request.state.request_id,request.method,route,response.status_code,round((time.monotonic()-started)*1000))
        return response
