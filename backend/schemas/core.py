from typing import Optional

from pydantic import BaseModel


class InventoryItem(BaseModel):
    item_name: str
    category: str
    quantity: float
    unit: str
    storage: str
    expiry_date: str


class WasteLog(BaseModel):
    item_id: int
    qty_wasted: float
    unit: str
    reason: str
    waste_date: str
    notes: Optional[str] = None
    cost_estimate: Optional[float] = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "chef"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryCreate(BaseModel):
    category_name: str
    description: Optional[str] = ""
    shelf_life_days: int = 7


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None
    shelf_life_days: Optional[int] = None
