"""
IT Delivery Manager Analytics Router.
Computes executive business impact metrics, hours saved, and department distributions.
"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth.dependencies import AuthenticatedUser, require_role
from src.database.db import get_db
from src.database.models import UserRole
from src.repositories.ticket_repository import TicketRepository

router = APIRouter(prefix="/api/v1/analytics", tags=["IT Delivery Manager"])


@router.get("/kpis")
def get_executive_kpis(
    tickets_per_month: int = 5000,
    triage_min_saved: float = 3.0,
    misroute_penalty_min: float = 15.0,
    hourly_rate_usd: float = 10.0,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.MANAGER, UserRole.MLOPS_ADMIN])),
) -> dict[str, Any]:
    """Calculates executive ROI & operational KPIs using PRD formula."""
    return TicketRepository.get_analytics(
        db=db,
        N=tickets_per_month,
        t=triage_min_saved,
        c=misroute_penalty_min,
        r=hourly_rate_usd,
    )


@router.get("/roi-model")
def get_roi_sensitivity(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.MANAGER, UserRole.MLOPS_ADMIN])),
) -> dict[str, Any]:
    """Provides sensitivity curve across ticket volumes (2k to 10k)."""
    analytics = TicketRepository.get_analytics(db=db)
    a = analytics["auto_route_rate"] or 0.70
    p = analytics["routed_accuracy"] or 0.92
    t = 3.0
    c = 15.0
    r = 10.0

    volumes = [2000, 3500, 5000, 7500, 10000]
    sensitivity = []
    for vol in volumes:
        net_min = vol * a * (t - (1.0 - p) * c)
        net_hr = net_min / 60.0
        sensitivity.append(
            {
                "monthly_ticket_volume": vol,
                "net_hours_saved": round(net_hr, 1),
                "cost_saved_usd": round(net_hr * r, 2),
            }
        )

    return {
        "current_parameters": {
            "auto_route_rate": a,
            "accuracy": p,
            "triage_saved_min": t,
            "misroute_penalty_min": c,
            "hourly_cost_usd": r,
        },
        "volume_curve": sensitivity,
    }


class RoiModelRequest(BaseModel):
    monthly_volume: int = Field(10000, ge=100)
    labor_rate_usd: float = Field(45.0, ge=1.0)
    triage_min_saved: float = Field(4.0, ge=0.5)
    misroute_penalty_min: float = Field(15.0, ge=1.0)
    infra_monthly_usd: float = Field(150.0, ge=0.0)


@router.post("/roi-model")
def calculate_custom_roi(
    req: RoiModelRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.MANAGER, UserRole.MLOPS_ADMIN])),
) -> dict[str, Any]:
    """Calculates customized ROI sensitivity using PRD formula."""
    analytics = TicketRepository.get_analytics(db=db)
    a = analytics["auto_route_rate"] or 0.714
    p = analytics["routed_accuracy"] or 0.925
    t = req.triage_min_saved
    c = req.misroute_penalty_min
    r = req.labor_rate_usd
    vol = req.monthly_volume

    net_min = vol * a * (t - (1.0 - p) * c)
    net_hr = net_min / 60.0
    gross_monthly = net_hr * r
    net_monthly = max(0.0, gross_monthly - req.infra_monthly_usd)
    annual_savings = net_monthly * 12.0
    roi_multiplier = (gross_monthly / req.infra_monthly_usd) if req.infra_monthly_usd > 0 else 0.0

    return {
        "monthly_volume": vol,
        "auto_route_rate": round(a, 4),
        "routed_accuracy": round(p, 4),
        "net_hours_saved_monthly": round(net_hr, 1),
        "gross_monthly_savings_usd": round(gross_monthly, 2),
        "net_monthly_savings_usd": round(net_monthly, 2),
        "annual_net_savings_usd": round(annual_savings, 2),
        "roi_multiplier": round(roi_multiplier, 1),
    }

