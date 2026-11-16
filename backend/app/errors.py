from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

# il contratto vuole gli errori sempre cosi':
# {"error": {"code": "...", "message": "...", "details": {...}}}


def errore(status, code, message, details=None):
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return JSONResponse(status_code=status, content={"error": error})


# errori http: indirizzo sbagliato, metodo sbagliato, o lanciati da noi
async def errore_http(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return errore(401, "unauthorized", "Missing or invalid bearer token.")
    if exc.status_code == 403:
        return errore(403, "forbidden", "Your role is not allowed to perform this action.")
    if exc.status_code == 404:
        return errore(404, "not_found", "Resource not found.")
    if exc.status_code == 405:
        return errore(405, "method_not_allowed", "Method not allowed.")
    if exc.status_code == 422:
        return errore(422, "validation_error", exc.detail)
    return errore(exc.status_code, "http_error", str(exc.detail))


# parametri sbagliati, es. property_id=3 -> details: {"property_id": "..."}
async def errore_validazione(request: Request, exc: RequestValidationError):
    details = {}
    for e in exc.errors():
        campo = str(e["loc"][-1])
        details[campo] = e["msg"]
    return errore(422, "validation_error", "Request parameters or body failed validation.", details)


# bug nel nostro codice: fuori non mostro niente, il dettaglio si vede nel terminale
async def errore_imprevisto(request: Request, exc: Exception):
    return errore(500, "internal_error", "Internal server error.")
