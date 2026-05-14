import os

# Read directly from environment — no dotenv needed
SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def get_client():
    from supabase import create_client
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_authed_client(access_token: str):
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client


# ══════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════
def sign_up(email: str, password: str) -> dict:
    try:
        client   = get_client()
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user:
            return {
                "success":      True,
                "user_id":      response.user.id,
                "access_token": response.session.access_token if response.session else None,
                "message":      "Account created successfully!",
            }
        return {"success": False, "message": "Sign up failed — please try again"}
    except Exception as e:
        err = str(e)
        if "already registered" in err.lower():
            return {"success": False, "message": "Email already registered. Please login instead."}
        return {"success": False, "message": err}


def sign_in(email: str, password: str) -> dict:
    try:
        client   = get_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            return {
                "success":      True,
                "user_id":      response.user.id,
                "access_token": response.session.access_token,
                "message":      "Logged in successfully!",
            }
        return {"success": False, "message": "Login failed"}
    except Exception as e:
        err = str(e)
        if "invalid" in err.lower() or "credentials" in err.lower():
            return {"success": False, "message": "Wrong email or password"}
        return {"success": False, "message": err}


def sign_out(access_token: str) -> dict:
    try:
        client = get_client()
        client.auth.sign_out()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ══════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════
def save_profile(user_id: str, access_token: str, profile: dict) -> dict:
    try:
        client = get_authed_client(access_token)
        data   = {
            "id":           user_id,
            "name":         profile.get("name", ""),
            "age":          profile.get("age", 0),
            "income":       profile.get("income", 0),
            "savings":      profile.get("savings", 0),
            "owns_home":    profile.get("owns_home", False),
            "goals":        profile.get("goals", ""),
            "health_score": profile.get("health_score", 0),
        }
        response = client.table("profiles").upsert(data).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "message": str(e)}


def load_profile(user_id: str, access_token: str) -> dict:
    try:
        client   = get_authed_client(access_token)
        response = client.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return {"success": True, "data": response.data[0]}
        return {"success": False, "message": "Profile not found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ══════════════════════════════════════════════════════════════════
# EXPENSES
# ══════════════════════════════════════════════════════════════════
def save_expenses(user_id: str, access_token: str, expenses: dict) -> dict:
    try:
        client   = get_authed_client(access_token)
        clean    = {k: v for k, v in expenses.items()
                    if k not in ["id", "user_id", "updated_at"]}
        data     = {"user_id": user_id, **clean}
        existing = client.table("expenses").select("id").eq("user_id", user_id).execute()
        if existing.data:
            response = client.table("expenses").update(clean).eq("user_id", user_id).execute()
        else:
            response = client.table("expenses").insert(data).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


def load_expenses(user_id: str, access_token: str) -> dict:
    try:
        client   = get_authed_client(access_token)
        response = client.table("expenses").select("*").eq("user_id", user_id).execute()
        if response.data:
            data = {k: v for k, v in response.data[0].items()
                    if k not in ["id", "user_id", "updated_at"]}
            return {"success": True, "data": data}
        return {"success": False, "message": "No expenses found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ══════════════════════════════════════════════════════════════════
# INVESTMENTS
# ══════════════════════════════════════════════════════════════════
def save_investments(user_id: str, access_token: str, investments: dict) -> dict:
    try:
        client   = get_authed_client(access_token)
        clean    = {k: v for k, v in investments.items()
                    if k not in ["id", "user_id", "updated_at"]}
        data     = {"user_id": user_id, **clean}
        existing = client.table("investments").select("id").eq("user_id", user_id).execute()
        if existing.data:
            response = client.table("investments").update(clean).eq("user_id", user_id).execute()
        else:
            response = client.table("investments").insert(data).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


def load_investments(user_id: str, access_token: str) -> dict:
    try:
        client   = get_authed_client(access_token)
        response = client.table("investments").select("*").eq("user_id", user_id).execute()
        if response.data:
            data = {k: v for k, v in response.data[0].items()
                    if k not in ["id", "user_id", "updated_at"]}
            return {"success": True, "data": data}
        return {"success": False, "message": "No investments found"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ══════════════════════════════════════════════════════════════════
# CHAT HISTORY
# ══════════════════════════════════════════════════════════════════
def save_message(user_id: str, access_token: str, role: str, content: str) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("chat_messages").insert({
            "user_id": user_id,
            "role":    role,
            "content": content,
        }).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


def load_chat_history(user_id: str, access_token: str, limit: int = 50) -> dict:
    try:
        client   = get_authed_client(access_token)
        response = (client.table("chat_messages")
                    .select("role, content, created_at")
                    .eq("user_id", user_id)
                    .order("created_at", desc=False)
                    .limit(limit)
                    .execute())
        return {"success": True, "data": response.data or []}
    except Exception as e:
        return {"success": False, "message": str(e), "data": []}


def clear_chat_history(user_id: str, access_token: str) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("chat_messages").delete().eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ══════════════════════════════════════════════════════════════════
# HEALTH SCORE HISTORY
# ══════════════════════════════════════════════════════════════════
def save_health_score(user_id: str, access_token: str, score: int) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("health_score_history").insert({
            "user_id": user_id,
            "score":   score,
        }).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}


def load_score_history(user_id: str, access_token: str, limit: int = 30) -> dict:
    try:
        client   = get_authed_client(access_token)
        response = (client.table("health_score_history")
                    .select("score, recorded_at")
                    .eq("user_id", user_id)
                    .order("recorded_at", desc=False)
                    .limit(limit)
                    .execute())
        return {"success": True, "data": response.data or []}
    except Exception as e:
        return {"success": False, "message": str(e), "data": []}


# ══════════════════════════════════════════════════════════════════
# COMBINED — save and load everything at once
# ══════════════════════════════════════════════════════════════════
def save_full_profile(user_id: str, access_token: str, profile: dict) -> dict:
    r1 = save_profile(user_id, access_token, profile)
    r2 = save_expenses(user_id, access_token, profile.get("expenses", {}))
    r3 = save_investments(user_id, access_token, profile.get("investments", {}))
    score = profile.get("health_score", 0)
    if score > 0:
        save_health_score(user_id, access_token, score)
    all_ok = r1["success"] and r2["success"] and r3["success"]
    return {
        "success": all_ok,
        "message": "Profile saved!" if all_ok else f"Save error: {r1.get('message','')} {r2.get('message','')} {r3.get('message','')}",
    }


def load_full_profile(user_id: str, access_token: str) -> dict:
    profile_r = load_profile(user_id, access_token)
    if not profile_r["success"]:
        return {"success": False, "message": "No profile found — please complete onboarding"}

    expenses_r    = load_expenses(user_id, access_token)
    investments_r = load_investments(user_id, access_token)

    profile = profile_r["data"]
    profile["expenses"]       = expenses_r["data"]    if expenses_r["success"]    else {}
    profile["investments"]    = investments_r["data"] if investments_r["success"] else {}
    profile["total_expenses"] = sum(profile["expenses"].values()) if profile["expenses"] else 0

    return {"success": True, "data": profile}