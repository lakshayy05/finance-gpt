"""
Auth routes — signup, login, logout, profile save/load
"""
from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional
from ..services.database import (
    sign_up, sign_in, sign_out,
    save_full_profile, load_full_profile,
    load_chat_history, save_health_score,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Models ────────────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    email:    str
    password: str

class SignInRequest(BaseModel):
    email:    str
    password: str

class SaveProfileRequest(BaseModel):
    user_id:      str
    access_token: str
    profile:      dict

class LoadProfileRequest(BaseModel):
    user_id:      str
    access_token: str


# ── Routes ────────────────────────────────────────────────────────
@router.post("/signup")
def signup(req: SignUpRequest):
    return sign_up(req.email, req.password)


@router.post("/signin")
def signin(req: SignInRequest):
    return sign_in(req.email, req.password)


@router.post("/signout")
def signout(req: LoadProfileRequest):
    return sign_out(req.access_token)


@router.post("/profile/save")
def save_profile_route(req: SaveProfileRequest):
    """Save complete profile after onboarding."""
    return save_full_profile(req.user_id, req.access_token, req.profile)


@router.post("/profile/load")
def load_profile_route(req: LoadProfileRequest):
    """Load profile on login — restores previous session."""
    result = load_full_profile(req.user_id, req.access_token)
    if result["success"]:
        # Also save a new health score snapshot
        score = result["data"].get("health_score", 0)
        if score > 0:
            save_health_score(req.user_id, req.access_token, score)
    return result


@router.post("/chat/history")
def get_chat_history(req: LoadProfileRequest):
    """Load chat history for user."""
    return load_chat_history(req.user_id, req.access_token, limit=50)