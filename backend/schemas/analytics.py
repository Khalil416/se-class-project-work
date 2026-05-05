from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_items: int
    items_near_expiry: int
    items_expired: int
    weekly_waste_cost: float


class WasteSummaryItem(BaseModel):
    reason: str
    count: int
    cost_total: float


class ReportPoint(BaseModel):
    label: str
    cost: float


class ReportReasonItem(BaseModel):
    reason: str
    count: int
    cost_total: float
