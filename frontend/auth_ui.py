"""
Auth UI — paste this into frontend/app.py

1. Add to session state init:
   "user_id": None, "access_token": None, "user_email": None, "authenticated": False

2. Add this function before onboarding()

3. Update the ROUTER at the bottom of app.py to:
   if not st.session_state.authenticated:
       auth_page()
   elif st.session_state.step < 4:
       ...onboarding...
   else:
       main_app()
"""

import streamlit as st

AUTH_STYLES = """
<style>
.auth-wrap {
    max-width: 440px;
    margin: 60px auto 0;
}
.auth-card {
    background: #FFFFFF;
    border: 1px solid #E8EDE0;
    border-radius: 24px;
    padding: 36px 40px;
    box-shadow: 0 4px 24px rgba(0,0,0,.06);
    animation: fadeUp .4s ease both;
}
.auth-logo {
    font-size: 36px;
    font-weight: 700;
    color: #1A2B1A;
    text-align: center;
    margin-bottom: 6px;
}
.auth-tagline {
    font-size: 14px;
    color: #9CAE9C;
    text-align: center;
    margin-bottom: 28px;
}
.auth-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 16px 0;
    color: #9CAE9C;
    font-size: 13px;
}
.auth-divider::before, .auth-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E8EDE0;
}
</style>
"""

def auth_page():
    st.markdown(AUTH_STYLES, unsafe_allow_html=True)

    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="auth-card">
      <div class="auth-logo">💚 FinanceGPT</div>
      <div class="auth-tagline">Your personal finance coach — built for Indian professionals 24–32</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Tab: Login / Sign up
    tab_login, tab_signup = st.tabs(["🔑  Login", "✨  Create account"])

    # ── LOGIN ─────────────────────────────────────────────────────
    with tab_login:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        email    = st.text_input("Email", key="login_email",    placeholder="you@example.com")
        password = st.text_input("Password", key="login_pass",  type="password", placeholder="Your password")

        if st.button("Login →", key="login_btn", use_container_width=True):
            if not email or not password:
                st.error("Please enter email and password")
            else:
                with st.spinner("Logging in..."):
                    result = api_post("/api/auth/signin", {
                        "email":    email,
                        "password": password,
                    })
                if result and result.get("success"):
                    st.session_state.user_id      = result["user_id"]
                    st.session_state.access_token = result["access_token"]
                    st.session_state.user_email   = email
                    st.session_state.authenticated= True

                    # Try to load existing profile
                    with st.spinner("Loading your profile..."):
                        profile_result = api_post("/api/auth/profile/load", {
                            "user_id":      result["user_id"],
                            "access_token": result["access_token"],
                        })

                    if profile_result and profile_result.get("success"):
                        # Restore full profile from database
                        saved = profile_result["data"]
                        st.session_state.profile = {
                            "name":           saved.get("name", ""),
                            "age":            saved.get("age", 26),
                            "income":         saved.get("income", 0),
                            "savings":        saved.get("savings", 0),
                            "owns_home":      saved.get("owns_home", False),
                            "goals":          saved.get("goals", ""),
                            "health_score":   saved.get("health_score", 0),
                            "expenses":       saved.get("expenses", {}),
                            "investments":    saved.get("investments", {}),
                            "total_expenses": saved.get("total_expenses", 0),
                        }
                        # Load chat history
                        chat_result = api_post("/api/auth/chat/history", {
                            "user_id":      result["user_id"],
                            "access_token": result["access_token"],
                        })
                        if chat_result and chat_result.get("success"):
                            st.session_state.messages = chat_result.get("data", [])

                        st.session_state.step = 4   # skip onboarding
                        st.success(f"Welcome back, {saved.get('name', '')}! 👋")
                    else:
                        # No profile yet — go through onboarding
                        st.session_state.step = 0
                        st.info("Welcome! Let's set up your profile.")

                    st.rerun()
                else:
                    err = result.get("message", "Login failed") if result else "Could not connect to backend"
                    st.error(err)

    # ── SIGN UP ───────────────────────────────────────────────────
    with tab_signup:
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        new_email = st.text_input("Email", key="signup_email",    placeholder="you@example.com")
        new_pass  = st.text_input("Password", key="signup_pass",  type="password", placeholder="Min 6 characters")
        new_pass2 = st.text_input("Confirm password", key="signup_pass2", type="password", placeholder="Same password again")

        st.markdown("""
        <div style="font-size:12px;color:#9CAE9C;margin:8px 0 16px">
          🔒 Your financial data is encrypted and private.
          We never share or sell your information.
        </div>""", unsafe_allow_html=True)

        if st.button("Create account →", key="signup_btn", use_container_width=True):
            if not new_email or not new_pass:
                st.error("Please fill in all fields")
            elif new_pass != new_pass2:
                st.error("Passwords don't match")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters")
            else:
                with st.spinner("Creating your account..."):
                    result = api_post("/api/auth/signup", {
                        "email":    new_email,
                        "password": new_pass,
                    })
                if result and result.get("success"):
                    st.session_state.user_id      = result["user_id"]
                    st.session_state.access_token = result.get("access_token")
                    st.session_state.user_email   = new_email
                    st.session_state.authenticated= True
                    st.session_state.step         = 0   # start onboarding
                    st.success("Account created! Let's set up your financial profile.")
                    st.rerun()
                else:
                    err = result.get("message", "Sign up failed") if result else "Could not connect to backend"
                    st.error(err)

    # ── Guest mode ────────────────────────────────────────────────
    st.markdown('<div class="auth-divider">or</div>', unsafe_allow_html=True)
    if st.button("Continue as guest (data won't be saved)", use_container_width=True, key="guest_btn"):
        st.session_state.authenticated = True
        st.session_state.user_id       = None
        st.session_state.access_token  = None
        st.session_state.step          = 0
        st.rerun()