"""FastAPI router for user authentication and session management."""

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session
from src.app.errors import UnauthorizedError
from src.app.modules.identity.controller import IdentityController
from src.app.modules.identity.schemas import DemoLoginIn, LoginIn, UserOut
from src.core.security import decode_access_token
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Identity & Authentication"])
controller = IdentityController()


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> UserOut:
    user_out = controller.login(payload, db)
    if user_out.access_token:
        response.set_cookie(
            key="routedesk_token",
            value=user_out.access_token,
            httponly=True,
            samesite="lax",
        )
    return user_out


@router.post("/demo-login", response_model=UserOut)
def demo_login(payload: DemoLoginIn, response: Response, db: Session = Depends(get_db)) -> UserOut:
    user_out = controller.demo_login(payload, db)
    if user_out.access_token:
        response.set_cookie(
            key="routedesk_token",
            value=user_out.access_token,
            httponly=True,
            samesite="lax",
        )
    return user_out


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response) -> dict:
    response.delete_cookie("routedesk_token")
    return {"status": "logged_out"}


@router.get("/me", response_model=UserOut)
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> UserOut:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid authorization token")
    token = authorization.split(" ")[1]
    try:
        claims = decode_access_token(token)
        user_id = claims.get("sub")
        return controller.get_user_by_id(user_id, db)
    except Exception:
        raise UnauthorizedError("Invalid or expired session token")
