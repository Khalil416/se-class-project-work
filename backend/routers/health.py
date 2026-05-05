from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/")
def read_root():
    return {
        "message": "Welcome to Kitchen Waste Tracker API",
        "version": "1.0.0",
    }


@router.get("/health")
def health():
    return {"status": "ok"}
