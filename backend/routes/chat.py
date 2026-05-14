from fastapi import APIRouter
from ..models import ChatRequest, ChatResponse, ChatMessage
from ..services.ai import build_system_prompt, chat
from ..services.finance import calc_health_score

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _enrich(profile_dict: dict) -> dict:
    exp  = profile_dict["expenses"]
    inv  = profile_dict["investments"]
    texp = sum(exp.values())
    invested = sum(inv.values())
    debt = exp.get("loan_emi", 0) + exp.get("credit_card", 0)
    profile_dict["total_expenses"] = texp
    profile_dict["health_score"]   = calc_health_score(
        profile_dict["income"], texp, profile_dict["savings"], invested, debt
    )
    return profile_dict


@router.post("", response_model=ChatResponse)
def send_message(req: ChatRequest):
    """
    Send a user message and get an AI response.
    The client must maintain and send the full message history each time
    (stateless API — no server-side memory needed for now).
    """
    p           = _enrich(req.profile.dict())
    sys_prompt  = build_system_prompt(p)
    history     = [m.dict() for m in req.messages]

    reply = chat(sys_prompt, history, req.user_input)

    # Build updated history to return to client
    updated_history = history + [
        {"role": "user",      "content": req.user_input},
        {"role": "assistant", "content": reply},
    ]

    return ChatResponse(
        reply    = reply,
        messages = [ChatMessage(**m) for m in updated_history],
    )