from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.db import log
from backend.routers.analytics import router as analytics_router
from backend.routers.auth import router as auth_router
from backend.routers.categories import router as categories_router
from backend.routers.health import router as health_router
from backend.routers.inventory import router as inventory_router
from backend.routers.users import router as users_router
from backend.routers.waste import router as waste_router

app = FastAPI(title="Kitchen Waste Tracker API", version="1.0.0")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(waste_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(analytics_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    log(f"VALIDATION ERROR {request.method} {request.url.path}", exc.errors())
    return JSONResponse(status_code=422, content={"error": "Validation failed", "details": exc.errors()})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
