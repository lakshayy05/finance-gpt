"""
FinanceGPT — Complete Streamlit Frontend
=========================================
Includes: Auth (login/signup/guest), onboarding, dashboard,
SIP calc, tax planner, statement parser, budget, alerts,
weekly report, market live, chat — all calling FastAPI backend.
"""
import streamlit as st
import httpx, math, json
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

load_dotenv(override=False)
BACKEND = os.getenv("BACKEND_URL", "https://finance-gpt-7aug.onrender.com").rstrip("/")

st.set_page_config(page_title="FinanceGPT", page_icon="💚", layout="wide")

# ══════════════════════════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif;}
.stApp{background:#F7F8F3;}
section[data-testid="stSidebar"]{background:#FFFFFF;border-right:1px solid #E8EDE0;}
section[data-testid="stSidebar"]>div{padding-top:1.5rem;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes countUp{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:scale(1)}}
@keyframes slideIn{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
@keyframes popIn{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
.prog-wrap{background:#E8EDE0;border-radius:99px;height:5px;margin-bottom:28px;overflow:hidden;}
.prog-fill{height:5px;border-radius:99px;background:linear-gradient(90deg,#22C55E,#16A34A);transition:width .5s ease;}
.step-card{background:#FFFFFF;border:1px solid #E8EDE0;border-radius:20px;padding:24px 28px;margin-bottom:24px;animation:fadeUp .4s ease both;box-shadow:0 1px 4px rgba(0,0,0,.04);}
.step-eyebrow{font-size:11px;font-weight:600;letter-spacing:.08em;color:#16A34A;text-transform:uppercase;margin-bottom:6px;}
.step-title{font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px;}
.step-sub{font-size:14px;color:#6B7C6B;}
.metric-card{background:#FFFFFF;border:1px solid #E8EDE0;border-radius:16px;padding:16px 18px;margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.04);animation:slideIn .4s ease both;}
.metric-eyebrow{font-size:11px;font-weight:600;letter-spacing:.06em;color:#9CAE9C;text-transform:uppercase;margin-bottom:5px;}
.metric-val{font-size:22px;font-weight:700;}
.metric-sub{font-size:12px;color:#9CAE9C;margin-top:3px;}
.score-wrap{background:linear-gradient(135deg,#F0FDF4,#DCFCE7);border:1px solid #BBF7D0;border-radius:20px;padding:22px;text-align:center;margin-bottom:16px;}
.score-num{font-size:56px;font-weight:700;line-height:1;animation:countUp .6s cubic-bezier(.34,1.56,.64,1) both .2s;}
.sec-label{font-size:11px;font-weight:600;letter-spacing:.08em;color:#9CAE9C;text-transform:uppercase;margin:18px 0 9px;padding-bottom:6px;border-bottom:1px solid #E8EDE0;}
.insight-card{border-radius:14px;padding:14px 16px;margin-bottom:8px;border-left:4px solid;}
.insight-card.good{background:#F0FDF4;border-color:#22C55E;}
.insight-card.warn{background:#FFFBEB;border-color:#F59E0B;}
.insight-card.bad{background:#FFF1F2;border-color:#F43F5E;}
.insight-title{font-size:13px;font-weight:600;color:#1A2B1A;margin-bottom:3px;}
.insight-sub{font-size:12px;color:#6B7C6B;}
.result-box{background:linear-gradient(135deg,#F0FDF4,#DCFCE7);border:1px solid #BBF7D0;border-radius:16px;padding:20px 24px;text-align:center;animation:popIn .4s ease both;}
.result-label{font-size:12px;font-weight:600;color:#16A34A;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px;}
.result-val{font-size:36px;font-weight:700;color:#1A2B1A;line-height:1.1;}
.result-sub{font-size:13px;color:#6B7C6B;margin-top:6px;}
.summary-bar{background:linear-gradient(135deg,#F0FDF4,#ECFDF5);border:1px solid #BBF7D0;border-radius:16px;padding:14px 18px;margin-bottom:16px;display:flex;gap:20px;flex-wrap:wrap;}
.sb-item{display:flex;flex-direction:column;}
.sb-label{font-size:10px;font-weight:600;color:#16A34A;letter-spacing:.05em;text-transform:uppercase;}
.sb-val{font-size:17px;font-weight:700;color:#1A2B1A;}
.user-bubble{background:#1A2B1A;border-radius:18px 18px 4px 18px;padding:12px 16px;margin:6px 0 6px 48px;color:#F0FDF4;font-size:15px;line-height:1.6;box-shadow:0 2px 8px rgba(26,43,26,.12);}
.bot-bubble{background:#FFFFFF;border:1px solid #E8EDE0;border-radius:18px 18px 18px 4px;padding:13px 17px;margin:6px 48px 6px 0;color:#1A2B1A;font-size:15px;line-height:1.7;box-shadow:0 2px 6px rgba(0,0,0,.05);}
.msg-who{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:5px;}
.msg-who.you{color:#16A34A;}.msg-who.bot{color:#9CAE9C;}
.goal-card{background:#FFFFFF;border:1px solid #E8EDE0;border-radius:16px;padding:18px 20px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
.goal-name{font-size:15px;font-weight:600;color:#1A2B1A;margin-bottom:6px;}
.goal-bar-bg{background:#E8EDE0;border-radius:99px;height:8px;margin:8px 0 4px;}
.goal-bar-fill{height:8px;border-radius:99px;transition:width .8s ease;}
.goal-meta{font-size:12px;color:#9CAE9C;}
.slab-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #F0F4EB;}
.slab-row:last-child{border-bottom:none;}
.auth-card{background:#FFFFFF;border:1px solid #E8EDE0;border-radius:24px;padding:36px 40px;box-shadow:0 4px 24px rgba(0,0,0,.06);max-width:420px;margin:40px auto;}
.auth-logo{font-size:34px;font-weight:700;color:#1A2B1A;text-align:center;margin-bottom:6px;}
.auth-tagline{font-size:14px;color:#9CAE9C;text-align:center;margin-bottom:24px;}
.stButton button{background:#1A2B1A !important;color:#F0FDF4 !important;border:none !important;border-radius:12px !important;font-weight:600 !important;font-family:'Plus Jakarta Sans',sans-serif !important;padding:10px 22px !important;transition:all .2s !important;}
.stButton button:hover{background:#2D4A2D !important;transform:translateY(-1px) !important;}
div[data-testid="stNumberInput"] input,div[data-testid="stTextInput"] input{background:#FFFFFF !important;border:1.5px solid #E8EDE0 !important;border-radius:10px !important;color:#1A2B1A !important;}
div[data-testid="stTextInput"] input[type="password"]{background:#FFFFFF !important;}
label{color:#4A5C4A !important;font-size:14px !important;font-weight:500 !important;}
.stRadio label{color:#1A2B1A !important;}
.stTabs [data-baseweb="tab-list"]{background:#F0F4EB;border-radius:12px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{border-radius:10px !important;font-weight:600 !important;color:#6B7C6B !important;font-family:'Plus Jakarta Sans',sans-serif !important;}
.stTabs [aria-selected="true"]{background:#FFFFFF !important;color:#1A2B1A !important;box-shadow:0 1px 4px rgba(0,0,0,.08) !important;}
div[data-testid="stChatInput"] textarea{background:#FFFFFF !important;border:1.5px solid #E8EDE0 !important;border-radius:14px !important;color:#1A2B1A !important;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# API HELPERS
# ══════════════════════════════════════════════════════════════════
def api_post(endpoint: str, data: dict) -> dict | None:
    try:
        r = httpx.post(f"{BACKEND}{endpoint}", json=data, timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except httpx.ConnectError:
        st.error(f"Cannot connect to backend at {BACKEND}. Is it running?")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def api_get(endpoint: str) -> dict | None:
    try:
        r = httpx.get(f"{BACKEND}{endpoint}", timeout=15)
        r.raise_for_status()
        return r.json()
    except: return None

def api_upload(endpoint: str, file_bytes: bytes, filename: str) -> dict | None:
    try:
        r = httpx.post(f"{BACKEND}{endpoint}", files={"file":(filename,file_bytes,"application/pdf")}, timeout=60)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error(f"Cannot connect to backend.")
        return None
    except Exception as e:
        st.error(f"Upload error: {e}")
        return None

def fmt(n: float) -> str:
    if n>=10000000: return f"₹{n/10000000:.2f}Cr"
    if n>=100000:   return f"₹{n/100000:.2f}L"
    if n>=1000:     return f"₹{n/1000:.1f}k"
    return f"₹{int(n):,}"

def score_color(s):
    if s>=75: return "#16A34A"
    if s>=50: return "#D97706"
    return "#DC2626"

def score_label(s):
    if s>=75: return "Excellent 🎉"
    if s>=50: return "On Track 👍"
    if s>=30: return "Needs Work ⚠️"
    return "Critical 🚨"


# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
for k, v in {
    "authenticated": False,
    "user_id":       None,
    "access_token":  None,
    "user_email":    None,
    "step":          0,
    "profile":       {},
    "analysis":      {},
    "messages":      [],
    "goals":         [],
    "transactions":  [],
    "pending_msg":   None,
    "budget_limits": {},
    "budget_analysis":{},
    "week_expenses": {},
    "weekly_report": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def build_profile_payload() -> dict:
    p = st.session_state.profile
    return {
        "name":        p.get("name",""),
        "age":         p.get("age",26),
        "income":      p.get("income",0),
        "savings":     p.get("savings",0),
        "owns_home":   p.get("owns_home",False),
        "goals":       p.get("goals","not specified"),
        "expenses":    p.get("expenses",{}),
        "investments": p.get("investments",{}),
    }

def save_to_supabase():
    """Save profile to Supabase if user is logged in (not guest)."""
    if st.session_state.user_id and st.session_state.access_token:
        api_post("/api/auth/profile/save", {
            "user_id":      st.session_state.user_id,
            "access_token": st.session_state.access_token,
            "profile":      st.session_state.profile,
        })

def logout():
    for k, v in {
        "authenticated":False,"user_id":None,"access_token":None,
        "user_email":None,"step":0,"profile":{},"analysis":{},
        "messages":[],"goals":[],"transactions":[],"pending_msg":None,
        "budget_limits":{},"budget_analysis":{},"week_expenses":{},"weekly_report":{},
    }.items():
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════
# CHARTS
# ══════════════════════════════════════════════════════════════════
COLORS=["#22C55E","#F59E0B","#3B82F6","#F43F5E","#8B5CF6","#EC4899","#14B8A6","#F97316","#6366F1","#84CC16","#64748B"]

def pie_chart(exp, owns_home):
    mapping=[("rent","Rent"),("food","Food"),("transport","Transport"),("mobile","Mobile"),("wifi","WiFi"),("electricity","Electricity"),("subscriptions","Subs"),("loan_emi","Loan EMI"),("credit_card","CC"),("entertainment","Entertainment"),("other_expenses","Other")]
    labels,values,colors=[],[],[]
    for i,(k,label) in enumerate(mapping):
        if k=="rent" and owns_home: continue
        v=exp.get(k,0)
        if v>0: labels.append(label);values.append(v);colors.append(COLORS[i%len(COLORS)])
    fig=go.Figure(go.Pie(labels=labels,values=values,hole=0.6,marker=dict(colors=colors,line=dict(color="#F7F8F3",width=2)),textinfo="percent",textfont=dict(size=12),hovertemplate="<b>%{label}</b><br>₹%{value:,}<br>%{percent}<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=True,legend=dict(font=dict(color="#4A5C4A",size=12),bgcolor="rgba(0,0,0,0)"),margin=dict(t=0,b=0,l=0,r=0),height=260)
    return fig

def cashflow_chart(income,texp,invested):
    surplus=income-texp;free=max(0,surplus-invested)
    fig=go.Figure(go.Bar(x=["Income","Expenses","Invested","Free Cash"],y=[income,texp,invested,free],marker=dict(color=["#22C55E","#F43F5E","#3B82F6","#F59E0B"],line=dict(color="#F7F8F3",width=1)),text=[fmt(v) for v in [income,texp,invested,free]],textposition="outside",textfont=dict(color="#4A5C4A",size=12),hovertemplate="<b>%{x}</b><br>₹%{y:,}<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",xaxis=dict(tickfont=dict(color="#4A5C4A",size=13)),yaxis=dict(showgrid=False,showticklabels=False,zeroline=False),margin=dict(t=28,b=0,l=0,r=0),height=220)
    return fig

def sip_growth_chart(yearly_data):
    yrs=[d["year"] for d in yearly_data];vals=[d["value"] for d in yearly_data];inv=[d["invested"] for d in yearly_data]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=yrs,y=vals,name="Portfolio",line=dict(color="#22C55E",width=3),fill="tozeroy",fillcolor="rgba(34,197,94,.08)"))
    fig.add_trace(go.Scatter(x=yrs,y=inv,name="Invested",line=dict(color="#3B82F6",width=2,dash="dot")))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",legend=dict(font=dict(color="#4A5C4A",size=12),bgcolor="rgba(0,0,0,0)"),xaxis=dict(title="Year",tickfont=dict(color="#4A5C4A")),yaxis=dict(tickfont=dict(color="#4A5C4A"),gridcolor="#F0F4EB"),margin=dict(t=10,b=0,l=0,r=0),height=280)
    return fig

def market_sparkline(history_data):
    if not history_data: return None
    dates=[d["date"] for d in history_data];prices=[d["price"] for d in history_data]
    up=prices[-1]>=prices[0]
    fig=go.Figure(go.Scatter(x=dates,y=prices,line=dict(color="#22C55E" if up else "#F43F5E",width=2),fill="tozeroy",fillcolor=f"rgba({'34,197,94' if up else '244,63,94'},.08)",hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",xaxis=dict(showgrid=False,showticklabels=False),yaxis=dict(showgrid=True,gridcolor="#F0F4EB",tickfont=dict(color="#9CAE9C",size=10)),margin=dict(t=4,b=4,l=0,r=0),height=120)
    return fig


# ══════════════════════════════════════════════════════════════════
# AUTH PAGE
# ══════════════════════════════════════════════════════════════════
def auth_page():
    st.markdown("""
    <div class="auth-card">
      <div class="auth-logo">💚 FinanceGPT</div>
      <div class="auth-tagline">Your personal finance coach — built for Indian professionals 24–32</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["🔑  Login", "✨  Create account"])

    with tab_login:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        email    = st.text_input("Email", key="login_email", placeholder="you@example.com")
        password = st.text_input("Password", key="login_pass", type="password", placeholder="Your password")

        if st.button("Login →", key="login_btn", use_container_width=True):
            if not email or not password:
                st.error("Please enter email and password")
            else:
                with st.spinner("Logging in..."):
                    result = api_post("/api/auth/signin", {"email":email,"password":password})
                if result and result.get("success"):
                    st.session_state.user_id      = result["user_id"]
                    st.session_state.access_token = result["access_token"]
                    st.session_state.user_email   = email
                    st.session_state.authenticated= True

                    # Load saved profile
                    with st.spinner("Loading your profile..."):
                        pr = api_post("/api/auth/profile/load", {
                            "user_id":      result["user_id"],
                            "access_token": result["access_token"],
                        })
                    if pr and pr.get("success"):
                        saved = pr["data"]
                        st.session_state.profile = {
                            "name":           saved.get("name",""),
                            "age":            saved.get("age",26),
                            "income":         saved.get("income",0),
                            "savings":        saved.get("savings",0),
                            "owns_home":      saved.get("owns_home",False),
                            "goals":          saved.get("goals",""),
                            "health_score":   saved.get("health_score",0),
                            "expenses":       saved.get("expenses",{}),
                            "investments":    saved.get("investments",{}),
                            "total_expenses": saved.get("total_expenses",0),
                        }
                        # Load chat history
                        ch = api_post("/api/auth/chat/history", {
                            "user_id":result["user_id"],"access_token":result["access_token"]
                        })
                        if ch and ch.get("success"):
                            st.session_state.messages = ch.get("data",[])
                        st.session_state.step = 4
                        st.success(f"Welcome back, {saved.get('name','')}! 👋")
                    else:
                        st.session_state.step = 0
                        st.info("Welcome! Let's set up your profile.")
                    st.rerun()
                else:
                    st.error(result.get("message","Login failed") if result else "Cannot connect to backend")

    with tab_signup:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        new_email = st.text_input("Email", key="signup_email", placeholder="you@example.com")
        new_pass  = st.text_input("Password", key="signup_pass", type="password", placeholder="Min 6 characters")
        new_pass2 = st.text_input("Confirm password", key="signup_pass2", type="password", placeholder="Same password again")
        st.markdown('<div style="font-size:12px;color:#9CAE9C;margin:8px 0 14px">🔒 Your financial data is encrypted and private.</div>', unsafe_allow_html=True)

        if st.button("Create account →", key="signup_btn", use_container_width=True):
            if not new_email or not new_pass:
                st.error("Please fill all fields")
            elif new_pass != new_pass2:
                st.error("Passwords don't match")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters")
            else:
                with st.spinner("Creating account..."):
                    result = api_post("/api/auth/signup", {"email":new_email,"password":new_pass})
                if result and result.get("success"):
                    st.session_state.user_id      = result["user_id"]
                    st.session_state.access_token = result.get("access_token")
                    st.session_state.user_email   = new_email
                    st.session_state.authenticated= True
                    st.session_state.step         = 0
                    st.success("Account created! Let's set up your profile.")
                    st.rerun()
                else:
                    st.error(result.get("message","Sign up failed") if result else "Cannot connect to backend")

    st.markdown('<div style="text-align:center;margin:16px 0;color:#9CAE9C;font-size:13px">— or —</div>', unsafe_allow_html=True)
    if st.button("Continue as guest (data won't be saved)", use_container_width=True, key="guest_btn"):
        st.session_state.authenticated = True
        st.session_state.user_id       = None
        st.session_state.access_token  = None
        st.session_state.step          = 0
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# ONBOARDING
# ══════════════════════════════════════════════════════════════════
def onboarding():
    step = st.session_state.step
    st.markdown(f'<div class="prog-wrap"><div class="prog-fill" style="width:{step/4*100:.0f}%"></div></div>', unsafe_allow_html=True)

    if step == 0:
        st.markdown('<div class="step-card"><div class="step-eyebrow">Step 1 of 4</div><div class="step-title">Let\'s get to know you 👋</div><div class="step-sub">2 minutes to your complete financial picture.</div></div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1: name=st.text_input("Your name",placeholder="e.g. Arjun"); age=st.number_input("Age",18,60,26)
        with c2: income=st.number_input("Monthly take-home income (₹)",0,10000000,55000,1000); savings=st.number_input("Total liquid savings (₹)",0,100000000,0,1000)
        if st.button("Next →",key="s0"):
            if not name: st.error("Please enter your name")
            elif income==0: st.warning("Income can't be zero!")
            else: st.session_state.profile.update({"name":name,"age":age,"income":income,"savings":savings}); st.session_state.step=1; st.rerun()

    elif step == 1:
        nm = st.session_state.profile["name"]
        st.markdown(f'<div class="step-card"><div class="step-eyebrow">Step 2 of 4</div><div class="step-title">Fixed expenses, {nm} 🏠</div><div class="step-sub">Bills you pay every month.</div></div>', unsafe_allow_html=True)
        owns = st.radio("Housing",["I pay rent","I own / staying with family"],horizontal=True)=="I own / staying with family"
        c1,c2 = st.columns(2)
        with c1: rent=st.number_input("Rent/EMI (₹)",0,500000,0 if owns else 12000,500); elec=st.number_input("Electricity (₹)",0,50000,1500,100); wifi=st.number_input("WiFi (₹)",0,10000,700,100)
        with c2: mob=st.number_input("Mobile (₹)",0,10000,299,50); loan=st.number_input("Loan EMI (₹)",0,500000,0,500); cc=st.number_input("Credit card (₹)",0,500000,0,500)
        b1,b2=st.columns([1,5])
        with b1:
            if st.button("← Back",key="s1b"): st.session_state.step=0; st.rerun()
        with b2:
            if st.button("Next →",key="s1"):
                st.session_state.profile.update({"owns_home":owns,"expenses":{"rent":rent,"electricity":elec,"wifi":wifi,"mobile":mob,"loan_emi":loan,"credit_card":cc}})
                st.session_state.step=2; st.rerun()

    elif step == 2:
        st.markdown('<div class="step-card"><div class="step-eyebrow">Step 3 of 4</div><div class="step-title">Lifestyle expenses 🍕</div><div class="step-sub">Be honest — no judgement. This is where insights come from.</div></div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1: food=st.number_input("Food & Swiggy/Zomato (₹)",0,200000,8000,500); trans=st.number_input("Transport (₹)",0,100000,3000,500); entmt=st.number_input("Entertainment (₹)",0,100000,3000,500)
        with c2: subs=st.number_input("OTT & subscriptions (₹)",0,50000,800,100); other=st.number_input("Everything else (₹)",0,200000,3000,500)
        b1,b2=st.columns([1,5])
        with b1:
            if st.button("← Back",key="s2b"): st.session_state.step=1; st.rerun()
        with b2:
            if st.button("Next →",key="s2"):
                st.session_state.profile["expenses"].update({"food":food,"transport":trans,"entertainment":entmt,"subscriptions":subs,"other_expenses":other})
                st.session_state.step=3; st.rerun()

    elif step == 3:
        st.markdown('<div class="step-card"><div class="step-eyebrow">Step 4 of 4</div><div class="step-title">Investments & goals 📈</div><div class="step-sub">Enter 0 if you haven\'t started — we\'ll fix that.</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Monthly investments</div>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: mf=st.number_input("Mutual funds/SIP (₹)",0,1000000,0,500); stk=st.number_input("Stocks (₹)",0,1000000,0,500); cryp=st.number_input("Crypto (₹)",0,1000000,0,500)
        with c2: ppf=st.number_input("PPF (₹)",0,150000,0,500); nps=st.number_input("NPS (₹)",0,200000,0,500); fd=st.number_input("FD (₹)",0,1000000,0,500)
        with c3: gold=st.number_input("Gold/Silver (₹)",0,1000000,0,500); re=st.number_input("Real estate (₹)",0,1000000,0,500); oth=st.number_input("Other (₹)",0,1000000,0,500)
        st.markdown('<div class="sec-label">Goals</div>', unsafe_allow_html=True)
        goals = st.text_area("What are you saving for?", placeholder="e.g. emergency fund, bike, Europe trip, home loan", height=80)
        b1,b2 = st.columns([1,5])
        with b1:
            if st.button("← Back",key="s3b"): st.session_state.step=2; st.rerun()
        with b2:
            if st.button("Build my dashboard 🚀",key="s3"):
                inv={"mutual_funds":mf,"stocks":stk,"crypto":cryp,"ppf":ppf,"nps":nps,"fixed_deposits":fd,"gold_silver":gold,"real_estate":re,"other":oth}
                exp=st.session_state.profile["expenses"]; texp=sum(exp.values())
                st.session_state.profile.update({"investments":inv,"goals":goals or "not specified","total_expenses":texp})

                with st.spinner("Analysing your profile..."):
                    payload = build_profile_payload()
                    result  = api_post("/api/profile/analyse",{"profile":payload})

                if result:
                    st.session_state.analysis = result
                    st.session_state.messages = [{"role":"assistant","content":result["opening_message"]}]
                    st.session_state.profile["health_score"] = result["health_score"]
                    st.session_state.step = 4

                    # Save to Supabase
                    save_to_supabase()
                    st.rerun()


# ══════════════════════════════════════════════════════════════════
# FEATURE TABS
# ══════════════════════════════════════════════════════════════════
def tab_sip():
    p=st.session_state.profile; inv=p.get("investments",{})
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>📈 SIP Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>See how small monthly investments grow into life-changing wealth.</div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    with c1: monthly=st.number_input("Monthly SIP (₹)",500,500000,max(500,int(inv.get("mutual_funds",500))),500)
    with c2: rate=st.slider("Expected return (%/year)",6.0,18.0,12.0,0.5)
    with c3: years=st.slider("Horizon (years)",1,40,10)
    if st.button("Calculate →",key="sip_calc"):
        with st.spinner("Calculating..."):
            result=api_post("/api/sip/calculate",{"monthly_amount":monthly,"annual_return":rate,"years":years})
        if result:
            r1,r2,r3=st.columns(3)
            with r1: st.markdown(f'<div class="result-box"><div class="result-label">Total invested</div><div class="result-val">{fmt(result["total_invested"])}</div><div class="result-sub">₹{monthly:,} × {years*12} months</div></div>',unsafe_allow_html=True)
            with r2: st.markdown(f'<div class="result-box"><div class="result-label">Portfolio value</div><div class="result-val" style="color:#16A34A">{fmt(result["final_value"])}</div><div class="result-sub">at {rate}% CAGR</div></div>',unsafe_allow_html=True)
            with r3: st.markdown(f'<div class="result-box"><div class="result-label">Wealth gained</div><div class="result-val" style="color:#3B82F6">{fmt(result["wealth_gained"])}</div></div>',unsafe_allow_html=True)
            st.markdown("<div style='font-weight:600;color:#1A2B1A;margin:18px 0 6px'>Growth over time</div>", unsafe_allow_html=True)
            st.plotly_chart(sip_growth_chart(result["yearly_data"]),use_container_width=True,config={"displayModeBar":False})


def tab_tax():
    p=st.session_state.profile; exp=p.get("expenses",{}); inv=p.get("investments",{}); inc=p.get("income",0)
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>💰 Tax Planner</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>Find every rupee you can save legally.</div>", unsafe_allow_html=True)
    tc1,tc2=st.columns(2)
    with tc1: annual_inc=st.number_input("Annual income (₹)",0,50000000,inc*12,10000); hra=st.number_input("HRA exemption (₹/year)",0,500000,min(int(exp.get("rent",0)*12*0.4),100000),5000)
    with tc2: d80c=st.number_input("80C investments (₹/year)",0,150000,min(150000,int((inv.get("ppf",0)+inv.get("nps",0)+inv.get("mutual_funds",0))*12)),5000); d80d=st.number_input("80D health insurance (₹/year)",0,75000,0,1000)
    other_ded=st.number_input("Other deductions — 80E, NPS 80CCD(1B) etc. (₹/year)",0,500000,0,5000)
    if st.button("Calculate tax →",key="tax_calc"):
        with st.spinner("Calculating..."):
            result=api_post("/api/tax/calculate",{"annual_income":annual_inc,"deductions_80c":d80c,"deductions_80d":d80d,"hra_exemption":hra,"other_deductions":other_ded})
        if result:
            better=result["recommended"]; saving=result["savings"]
            bc="#F0FDF4" if better=="new" else "#EFF6FF"; brd="#22C55E" if better=="new" else "#3B82F6"; tc_="#16A34A" if better=="new" else "#1D4ED8"
            st.markdown(f'<div style="background:{bc};border-left:4px solid {brd};border-radius:12px;padding:14px 20px;margin:16px 0"><div style="font-weight:700;color:{tc_};font-size:15px">{"New" if better=="new" else "Old"} regime saves you {fmt(saving)}/year</div></div>',unsafe_allow_html=True)
            cn_,co_=st.columns(2)
            for col,label,total in [(cn_,"New Regime",result["new_regime_total"]),(co_,"Old Regime",result["old_regime_total"])]:
                with col:
                    is_b=(better=="new" and label=="New Regime") or (better=="old" and label=="Old Regime")
                    color="#16A34A" if is_b else "#DC2626"
                    border="2px solid #22C55E" if is_b else "1px solid #E8EDE0"
                    st.markdown(f'<div style="background:#FFFFFF;border:{border};border-radius:16px;padding:20px"><div style="font-size:15px;font-weight:700;margin-bottom:10px">{label} {"✅" if is_b else ""}</div><div style="font-size:28px;font-weight:700;color:{color};margin-bottom:4px">{fmt(total)}/year</div><div style="font-size:13px;color:#9CAE9C">{fmt(total/12)}/month</div></div>',unsafe_allow_html=True)


def tab_statement():
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>📂 Import Bank Statement</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:16px'>Upload PDF → AI parses all transactions → auto-fills expenses.</div>", unsafe_allow_html=True)
    st.markdown('<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#92400E">🔒 Processed in memory only — never stored on any server.</div>', unsafe_allow_html=True)
    uploaded=st.file_uploader("Upload bank statement PDF",type=["pdf"])
    if uploaded:
        if st.button("🔍 Parse with AI",use_container_width=True,key="parse_stmt"):
            with st.spinner("AI parsing... ~15 seconds"):
                result=api_upload("/api/statement/parse",uploaded.read(),uploaded.name)
            if result:
                st.session_state.transactions=result["transactions"]
                txns=result["transactions"]
                r1,r2,r3=st.columns(3)
                with r1: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Transactions</div><div class="metric-val">{result["txn_count"]}</div></div>',unsafe_allow_html=True)
                with r2: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Total spent</div><div class="metric-val" style="color:#DC2626">{fmt(result["total_debit"])}</div></div>',unsafe_allow_html=True)
                with r3: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Total received</div><div class="metric-val" style="color:#16A34A">{fmt(result["total_credit"])}</div></div>',unsafe_allow_html=True)
                st.markdown('<div class="sec-label">Parsed transactions</div>', unsafe_allow_html=True)
                for txn in txns[:30]:
                    amt_col="#DC2626" if txn["type"]=="debit" else "#16A34A"; sign="−" if txn["type"]=="debit" else "+"
                    st.markdown(f'<div style="display:flex;gap:12px;padding:8px 12px;border-bottom:1px solid #F0F4EB;font-size:13px"><span style="color:#9CAE9C;min-width:80px">{txn["date"]}</span><span style="flex:1;color:#1A2B1A;font-weight:500">{txn["description"]}</span><span style="font-size:11px;background:#F0F4EB;padding:2px 8px;border-radius:20px;color:#4A5C4A">{txn["category"]}</span><span style="color:{amt_col};font-weight:600;min-width:70px;text-align:right">{sign}{fmt(txn["amount"])}</span></div>',unsafe_allow_html=True)
                st.markdown("---")
                if st.button("✅ Apply to my profile",use_container_width=True,key="apply_stmt"):
                    summary=result.get("expense_summary",{})
                    if summary:
                        for k,v in summary.items(): st.session_state.profile["expenses"][k]=v
                        texp=sum(st.session_state.profile["expenses"].values())
                        st.session_state.profile["total_expenses"]=texp
                        with st.spinner("Updating dashboard..."):
                            new_ana=api_post("/api/profile/analyse",{"profile":build_profile_payload()})
                        if new_ana:
                            st.session_state.analysis=new_ana
                            st.session_state.profile["health_score"]=new_ana["health_score"]
                            save_to_supabase()
                            st.success("✅ Profile updated with real data!"); st.balloons()


def tab_budget():
    p=st.session_state.profile; exp=p.get("expenses",{}); inc=p.get("income",0)
    surplus=inc-sum(exp.values())
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>📋 Budget Planner</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>Set monthly limits. Track what's left. Know before you overspend.</div>", unsafe_allow_html=True)
    col_man,col_ai=st.columns([3,1])
    with col_ai:
        savings_goal=st.number_input("My savings goal (₹/month)",0,int(inc),min(5000,int(max(0,surplus))),500)
        if st.button("✨ AI suggest",use_container_width=True):
            with st.spinner("AI building budget..."):
                result=api_post("/api/budget/suggest",{"income":inc,"expenses":exp,"savings_goal":savings_goal})
            if result: st.session_state.budget_limits=result["suggested"]; st.rerun()
    CATS={"food":("🍕 Food",exp.get("food",8000)),"transport":("🚗 Transport",exp.get("transport",3000)),"entertainment":("🎬 Entertainment",exp.get("entertainment",3000)),"subscriptions":("📱 Subscriptions",exp.get("subscriptions",800)),"shopping":("🛍️ Shopping",2000),"other_expenses":("📦 Other",exp.get("other_expenses",3000))}
    limits={}
    c1,c2=st.columns(2)
    for i,(key,(label,default)) in enumerate(CATS.items()):
        with c1 if i%2==0 else c2:
            limits[key]=st.number_input(label,0,200000,int(st.session_state.budget_limits.get(key,default)),500,key=f"budget_{key}")
    if st.button("📊 Analyse budget",use_container_width=True,key="analyse_budget"):
        st.session_state.budget_limits=limits
        with st.spinner("Analysing..."):
            result=api_post("/api/budget/analyse",{"income":inc,"expenses":exp,"budget_limits":limits})
        if result: st.session_state.budget_analysis=result; st.rerun()
    ana=st.session_state.budget_analysis
    if ana:
        st.markdown('<div class="sec-label">Budget vs actual</div>', unsafe_allow_html=True)
        sm1,sm2,sm3,sm4=st.columns(4)
        overall=ana.get("overall_status","on_track"); oc={"on_track":"#16A34A","warning":"#D97706","over":"#DC2626"}.get(overall,"#16A34A"); ol={"on_track":"On Track ✅","warning":"Watch Out ⚠️","over":"Over Budget 🚨"}.get(overall,"")
        with sm1: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Budget</div><div class="metric-val">{fmt(ana["total_budget"])}</div></div>',unsafe_allow_html=True)
        with sm2: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Spent</div><div class="metric-val" style="color:#DC2626">{fmt(ana["total_spent"])}</div></div>',unsafe_allow_html=True)
        with sm3: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Remaining</div><div class="metric-val" style="color:#16A34A">{fmt(ana["total_remaining"])}</div></div>',unsafe_allow_html=True)
        with sm4: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Status</div><div class="metric-val" style="color:{oc};font-size:15px">{ol}</div></div>',unsafe_allow_html=True)
        for item in ana.get("status",[]):
            pct=min(100,item["pct_used"]); bc={"on_track":"#22C55E","warning":"#F59E0B","over":"#F43F5E"}.get(item["status"],"#22C55E")
            rl=f"₹{item['remaining']:,.0f} left" if item["status"]!="over" else f"₹{item['spent']-item['limit']:,.0f} over!"
            st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E8EDE0;border-radius:14px;padding:16px 18px;margin-bottom:10px"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><span style="font-size:14px;font-weight:600;color:#1A2B1A">{item["label"]}</span><span style="font-size:13px;color:{bc};font-weight:600">{rl}</span></div><div style="background:#E8EDE0;border-radius:99px;height:8px;margin-bottom:6px"><div style="background:{bc};border-radius:99px;height:8px;width:{pct:.0f}%"></div></div><div style="display:flex;justify-content:space-between;font-size:12px;color:#9CAE9C"><span>Spent: {fmt(item["spent"])} of {fmt(item["limit"])}</span><span>{item["pct_used"]:.0f}% used</span></div></div>',unsafe_allow_html=True)


def tab_alerts():
    p=st.session_state.profile; exp=p.get("expenses",{}); inc=p.get("income",0)
    budget_limits=st.session_state.budget_limits
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>🔔 Spending Alerts</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>Know the moment you're close to overspending.</div>", unsafe_allow_html=True)
    if not budget_limits:
        st.markdown('<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:14px;padding:20px;text-align:center"><div style="font-size:32px;margin-bottom:8px">⚠️</div><div style="font-size:15px;font-weight:600;color:#1A2B1A">No budget limits set</div><div style="font-size:13px;color:#6B7C6B">Go to Budget Planner tab first.</div></div>', unsafe_allow_html=True)
        return
    with st.spinner("Checking spending..."):
        result=api_post("/api/budget/analyse",{"income":inc,"expenses":exp,"budget_limits":budget_limits})
    if not result: return
    alerts=result.get("alerts",[]); all_cats=result.get("status",[])
    if not alerts:
        st.markdown('<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:16px;padding:28px;text-align:center"><div style="font-size:40px;margin-bottom:8px">🎉</div><div style="font-size:17px;font-weight:700;color:#1A2B1A">All clear! No alerts this month.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sec-label">{len(alerts)} alert{"s" if len(alerts)>1 else ""} need attention</div>', unsafe_allow_html=True)
        for alert in alerts:
            sev=alert.get("severity","medium"); color="#DC2626" if sev=="high" else "#D97706"; bg="#FFF1F2" if sev=="high" else "#FFFBEB"; border="#F43F5E" if sev=="high" else "#F59E0B"; icon="🚨" if sev=="high" else "⚠️"
            st.markdown(f'<div style="background:{bg};border:1px solid {border};border-left:5px solid {border};border-radius:14px;padding:16px 20px;margin-bottom:12px"><div style="display:flex;justify-content:space-between"><div><div style="font-size:15px;font-weight:700;color:#1A2B1A">{icon} {alert["label"]}</div><div style="font-size:13px;color:{color};font-weight:500;margin-top:4px">{alert["message"]}</div></div><div style="text-align:right"><div style="font-size:22px;font-weight:700;color:{color}">{alert["pct_used"]:.0f}%</div><div style="font-size:11px;color:#9CAE9C">of budget</div></div></div><div style="background:#E8EDE0;border-radius:99px;height:6px;margin-top:12px"><div style="background:{color};border-radius:99px;height:6px;width:{min(100,alert["pct_used"]):.0f}%"></div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sec-label">All categories</div>', unsafe_allow_html=True)
    cols=st.columns(3)
    for i,item in enumerate(all_cats):
        pct=min(100,item["pct_used"]); color={"on_track":"#16A34A","warning":"#D97706","over":"#DC2626"}.get(item["status"],"#16A34A"); emoji={"on_track":"✅","warning":"⚠️","over":"🚨"}.get(item["status"],"✅")
        with cols[i%3]: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">{item["label"]}</div><div class="metric-val" style="color:{color};font-size:18px">{pct:.0f}% {emoji}</div><div class="metric-sub">{fmt(item["spent"])} of {fmt(item["limit"])}</div><div style="background:#E8EDE0;border-radius:99px;height:5px;margin-top:8px"><div style="background:{color};border-radius:99px;height:5px;width:{pct:.0f}%"></div></div></div>',unsafe_allow_html=True)


def tab_weekly_report():
    p=st.session_state.profile; exp=p.get("expenses",{}); inc=p.get("income",0)
    budget_limits=st.session_state.budget_limits
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>📅 Weekly Report</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>Enter what you spent this week — AI generates your personalised summary.</div>", unsafe_allow_html=True)
    st.markdown('<div class="step-card"><div class="step-eyebrow">This week\'s spending</div><div class="step-title">What did you spend? 📝</div><div class="step-sub">Estimates are fine — even rough numbers give useful insights.</div></div>', unsafe_allow_html=True)
    WEEK_CATS={"food":("🍕 Food",int(exp.get("food",8000)/4.3)),"transport":("🚗 Transport",int(exp.get("transport",3000)/4.3)),"entertainment":("🎬 Entertainment",int(exp.get("entertainment",3000)/4.3)),"subscriptions":("📱 Subscriptions",int(exp.get("subscriptions",800)/4.3)),"shopping":("🛍️ Shopping",500),"other":("📦 Other",500)}
    week_exp={}; wc1,wc2=st.columns(2)
    for i,(key,(label,default)) in enumerate(WEEK_CATS.items()):
        stored=st.session_state.week_expenses.get(key,default)
        with wc1 if i%2==0 else wc2:
            week_exp[key]=st.number_input(label,0,100000,int(stored),100,key=f"week_{key}")
    total_week=sum(week_exp.values()); weekly_avg=sum(exp.values())/4.3
    vs_avg=((total_week-weekly_avg)/weekly_avg*100) if weekly_avg>0 else 0
    qc1,qc2,qc3=st.columns(3)
    with qc1: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">This week</div><div class="metric-val">{fmt(total_week)}</div></div>',unsafe_allow_html=True)
    with qc2: st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Weekly avg</div><div class="metric-val">{fmt(weekly_avg)}</div></div>',unsafe_allow_html=True)
    with qc3:
        avg_col="#16A34A" if vs_avg<=0 else "#D97706" if vs_avg<=20 else "#DC2626"; avg_arr="▼" if vs_avg<=0 else "▲"
        st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">vs average</div><div class="metric-val" style="color:{avg_col}">{avg_arr} {abs(vs_avg):.0f}%</div></div>',unsafe_allow_html=True)
    if st.button("🤖 Generate my weekly report",use_container_width=True,key="gen_report"):
        st.session_state.week_expenses=week_exp
        with st.spinner("AI writing your report..."):
            result=api_post("/api/budget/weekly-report",{"profile":{"name":p.get("name",""),"income":inc,"goals":p.get("goals",""),"expenses":exp},"budget_limits":budget_limits,"week_expenses":week_exp})
        if result: st.session_state.weekly_report=result; st.rerun()
    report_data=st.session_state.weekly_report
    if report_data:
        report=report_data.get("report",""); top=report_data.get("top_category",""); total=report_data.get("total_spent",0); vs=report_data.get("vs_weekly_avg",0)
        vs_col="#16A34A" if vs<=0 else "#DC2626"; vs_lbl=f"{'under' if vs<=0 else 'over'} average by {abs(vs):.0f}%"
        st.markdown(f'<div style="background:#FFFFFF;border:1px solid #E8EDE0;border-radius:20px;padding:24px 28px;margin-top:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)"><div style="display:flex;justify-content:space-between;margin-bottom:16px"><div><div style="font-size:11px;font-weight:600;color:#16A34A;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">Weekly Report</div><div style="font-size:18px;font-weight:700;color:#1A2B1A">Week in Review — {p.get("name","")}</div></div><div style="text-align:right"><div style="font-size:22px;font-weight:700;color:#1A2B1A">{fmt(total)}</div><div style="font-size:12px;color:{vs_col};font-weight:600">{vs_lbl}</div></div></div><div style="border-top:1px solid #F0F4EB;padding-top:16px;font-size:15px;color:#1A2B1A;line-height:1.8;white-space:pre-wrap">{report}</div><div style="border-top:1px solid #F0F4EB;margin-top:16px;padding-top:12px;font-size:13px;color:#9CAE9C">🏆 Biggest spend: <strong style="color:#1A2B1A">{top}</strong></div></div>',unsafe_allow_html=True)


def tab_market():
    st.markdown("<div style='font-size:22px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>🔴 Market Live</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>Live Nifty, Sensex, Gold & Silver — refreshes every time you open this tab.</div>", unsafe_allow_html=True)
    with st.spinner("Fetching live prices..."):
        data=api_get("/api/market/prices")
    if not data: st.error("Could not fetch market data."); return
    st.markdown(f"<div style='font-size:12px;color:#9CAE9C;margin-bottom:16px'>Updated: {data.get('fetched_at','')}</div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Indian indices</div>', unsafe_allow_html=True)
    idx_cols=st.columns(3)
    for i,key in enumerate(["nifty50","sensex","banknifty"]):
        item=data.get(key,{}); price=item.get("price",0); change=item.get("change",0); pct=item.get("change_pct",0); up=item.get("direction","up")=="up"
        pc="#16A34A" if up else "#DC2626"; arr="▲" if up else "▼"
        with idx_cols[i]: st.markdown(f'<div class="metric-card" style="border-left:4px solid {pc}"><div class="metric-eyebrow">{item.get("name","")}</div><div class="metric-val" style="color:#1A2B1A">{price:,.2f}</div><div style="font-size:13px;font-weight:600;color:{pc};margin-top:4px">{arr} {abs(change):,.2f} ({abs(pct):.2f}%)</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Gold & Silver (INR)</div>', unsafe_allow_html=True)
    comm_cols=st.columns(2)
    for i,(key,label,unit) in enumerate([("gold","🪙 Gold","per 10g"),("silver","⚪ Silver","per kg")]):
        item=data.get(key,{}); price=item.get("price",0); change=item.get("change",0); pct=item.get("change_pct",0); up=item.get("direction","up")=="up"
        pc="#16A34A" if up else "#DC2626"; arr="▲" if up else "▼"
        with comm_cols[i]: st.markdown(f'<div class="metric-card" style="border-left:4px solid {pc}"><div class="metric-eyebrow">{label} — {unit}</div><div class="metric-val" style="color:#1A2B1A">₹{price:,.0f}</div><div style="font-size:13px;font-weight:600;color:{pc};margin-top:4px">{arr} ₹{abs(change):,.0f} ({abs(pct):.2f}%)</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Price history</div>', unsafe_allow_html=True)
    period_map={"1 Week":"5d","1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y"}
    period_label=st.select_slider("Period",options=list(period_map.keys()),value="1 Month")
    period=period_map[period_label]
    selected=st.multiselect("Charts for",["Nifty 50","Gold","Silver"],default=["Nifty 50","Gold"])
    sym_map={"Nifty 50":"nifty50","Gold":"gold","Silver":"silver"}
    for sym_label in selected:
        hist=api_get(f"/api/market/history/{sym_map[sym_label]}?period={period}")
        if hist and hist.get("data"):
            items=hist["data"]; start=items[0]["price"]; end=items[-1]["price"]; change=end-start; pct=(change/start*100) if start>0 else 0; up=change>=0
            col="#16A34A" if up else "#DC2626"; arr="▲" if up else "▼"
            st.markdown(f'<div style="display:flex;justify-content:space-between;margin-bottom:4px"><div style="font-size:15px;font-weight:600;color:#1A2B1A">{sym_label}</div><div style="font-size:13px;font-weight:600;color:{col}">{arr} {abs(pct):.2f}% over {period_label.lower()}</div></div>',unsafe_allow_html=True)
            fig=market_sparkline(items)
            if fig: st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
def render_sidebar():
    p=st.session_state.profile; ana=st.session_state.analysis
    exp=p.get("expenses",{}); inv=p.get("investments",{})
    inc=p.get("income",0); sav=p.get("savings",0)
    score=p.get("health_score",ana.get("health_score",0))
    texp=sum(exp.values()); invested=sum(inv.values()); surplus=inc-texp

    with st.sidebar:
        # User info
        name=p.get("name","")
        badge=""
        if st.session_state.user_id:
            badge='<span style="font-size:10px;background:#F0FDF4;color:#16A34A;border:1px solid #BBF7D0;padding:2px 8px;border-radius:20px;margin-left:6px">SAVED</span>'
        else:
            badge='<span style="font-size:10px;background:#FFF7ED;color:#D97706;border:1px solid #FDE68A;padding:2px 8px;border-radius:20px;margin-left:6px">GUEST</span>'
        st.markdown(f"<div style='font-size:19px;font-weight:700;color:#1A2B1A;margin-bottom:2px'>{name}{badge}</div>", unsafe_allow_html=True)
        if st.session_state.user_email:
            st.markdown(f"<div style='font-size:12px;color:#9CAE9C;margin-bottom:14px'>{st.session_state.user_email}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:12px;color:#9CAE9C;margin-bottom:14px'>{p.get('age','')} yrs · {fmt(inc)}/month</div>", unsafe_allow_html=True)

        # Health score
        col=score_color(score)
        st.markdown(f'<div class="score-wrap"><div style="font-size:11px;font-weight:600;color:#16A34A;letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px">Health Score</div><div class="score-num" style="color:{col}">{score}</div><div style="font-size:13px;color:{col};font-weight:600;margin-top:8px">{score_label(score)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec-label">This month</div>', unsafe_allow_html=True)
        def mcard(t,v,s,c="#1A2B1A"): st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">{t}</div><div class="metric-val" style="color:{c}">{v}</div><div class="metric-sub">{s}</div></div>', unsafe_allow_html=True)
        mcard("Total expenses",fmt(texp),f"{texp/inc*100:.0f}% of income" if inc>0 else "","#DC2626" if inc>0 and texp/inc>.8 else "#D97706" if inc>0 and texp/inc>.6 else "#1A2B1A")
        mcard("Monthly surplus",fmt(surplus) if surplus>0 else "₹0","income after expenses","#16A34A" if surplus>10000 else "#D97706" if surplus>0 else "#DC2626")
        mcard("Invested/month",fmt(invested),f"{invested/inc*100:.0f}% of income" if inc>0 else "","#3B82F6")
        ef_t=texp*6; ef_pct=min(100,sav/ef_t*100) if ef_t>0 else 0; ef_c="#16A34A" if ef_pct>=100 else "#D97706" if ef_pct>=50 else "#DC2626"
        st.markdown(f'<div class="metric-card"><div class="metric-eyebrow">Emergency fund</div><div class="metric-val" style="color:{ef_c}">{ef_pct:.0f}%</div><div class="metric-sub">{fmt(sav)} of {fmt(ef_t)} target</div><div style="background:#E8EDE0;border-radius:99px;height:6px;margin-top:8px"><div style="background:{ef_c};border-radius:99px;height:6px;width:{ef_pct:.0f}%"></div></div></div>', unsafe_allow_html=True)
        if st.session_state.goals:
            mcard("Active goals",len(st.session_state.goals),"being tracked","#8B5CF6")

        st.markdown("")
        if st.session_state.user_id:
            if st.button("💾 Save profile"):
                save_to_supabase(); st.success("Saved!")
        if st.button("🔄 Update profile"):
            st.session_state.step=0; st.session_state.profile={}; st.session_state.analysis={}; st.session_state.messages=[]; st.rerun()
        if st.button("🚪 Logout"):
            logout(); st.rerun()


# ══════════════════════════════════════════════════════════════════
# CHAT
# ══════════════════════════════════════════════════════════════════
def tab_chat():
    p=st.session_state.profile; ana=st.session_state.analysis
    inc=p.get("income",0); texp=sum(p.get("expenses",{}).values())
    surplus=inc-texp; score=p.get("health_score",ana.get("health_score",0))
    st.markdown("<div style='font-size:24px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>Chat with FinanceGPT</div>", unsafe_allow_html=True)
    is_saved="Real data 🟢" if p.get("statement_parsed") else ""
    st.markdown(f"<div style='color:#9CAE9C;font-size:14px;margin-bottom:14px'>I've analysed your profile. Ask me anything. {is_saved}</div>", unsafe_allow_html=True)
    sr_pct=(surplus/inc*100) if inc>0 else 0
    st.markdown(f'<div class="summary-bar"><div class="sb-item"><span class="sb-label">Income</span><span class="sb-val">{fmt(inc)}</span></div><div class="sb-item"><span class="sb-label">Expenses</span><span class="sb-val">{fmt(texp)}</span></div><div class="sb-item"><span class="sb-label">Surplus</span><span class="sb-val" style="color:{"#16A34A" if surplus>0 else "#DC2626"}">{fmt(surplus)}</span></div><div class="sb-item"><span class="sb-label">Savings rate</span><span class="sb-val">{sr_pct:.0f}%</span></div><div class="sb-item"><span class="sb-label">Score</span><span class="sb-val" style="color:{score_color(score)}">{score}/100</span></div><div class="sb-item"><span class="sb-label">Goals</span><span class="sb-val" style="color:#8B5CF6">{len(st.session_state.goals)}</span></div></div>', unsafe_allow_html=True)
    if len(st.session_state.messages)<=1:
        st.markdown('<div class="sec-label">Quick questions</div>', unsafe_allow_html=True)
        suggs=["Build me a step-by-step plan","How much tax can I save?","When should I start my SIP?","Where am I overspending?","How long until I'm financially free?","Explain my health score"]
        c1,c2,c3=st.columns(3)
        for i,s in enumerate(suggs):
            with [c1,c2,c3][i%3]:
                if st.button(s,key=f"chip_{i}",use_container_width=True): st.session_state.pending_msg=s; st.rerun()
        st.markdown("---")
    for msg in st.session_state.messages:
        if msg["role"]=="user": st.markdown(f'<div class="msg-who you">You</div><div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="msg-who bot">FinanceGPT</div><div class="bot-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
    if st.session_state.pending_msg:
        m=st.session_state.pending_msg; st.session_state.pending_msg=None; _send(m)
    if prompt:=st.chat_input(f"Ask anything, {p.get('name','')}..."):
        _send(prompt)


def _send(user_input: str):
    history=[m for m in st.session_state.messages]
    st.session_state.messages.append({"role":"user","content":user_input})
    with st.chat_message("user"): st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result=api_post("/api/chat",{"profile":build_profile_payload(),"messages":history,"user_input":user_input})
        if result:
            st.markdown(result["reply"])
            st.session_state.messages.append({"role":"assistant","content":result["reply"]})
        else:
            st.error("Could not get response.")
    st.rerun()


# ══════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════
def main_app():
    render_sidebar()
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9=st.tabs([
        "📊 Dashboard","📋 Budget","🔔 Alerts","📅 Weekly Report",
        "📈 SIP Calc","💰 Tax","📂 Statement","🔴 Market","💬 Chat"
    ])
    p=st.session_state.profile; ana=st.session_state.analysis
    exp=p.get("expenses",{}); inv=p.get("investments",{})
    inc=p.get("income",0); texp=sum(exp.values()); invested=sum(inv.values())

    with tab1:
        st.markdown(f"<div style='font-size:24px;font-weight:700;color:#1A2B1A;margin-bottom:4px'>Your Financial Dashboard</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#9CAE9C;font-size:14px;margin-bottom:20px'>Here's where your {fmt(inc)}/month is going, {p.get('name','')}.</div>", unsafe_allow_html=True)
        ptag=ana.get("priority_tag",""); ptxt=ana.get("priority_text","")
        bc={"CRITICAL":"#FFF1F2","PRIORITY 1":"#FFFBEB","OPPORTUNITY":"#F0FDF4","OPTIMISE":"#F0FDF4"}.get(ptag,"#F0FDF4")
        brc={"CRITICAL":"#F43F5E","PRIORITY 1":"#F59E0B","OPPORTUNITY":"#22C55E","OPTIMISE":"#22C55E"}.get(ptag,"#22C55E")
        tc_={"CRITICAL":"#DC2626","PRIORITY 1":"#D97706","OPPORTUNITY":"#16A34A","OPTIMISE":"#16A34A"}.get(ptag,"#16A34A")
        if ptag: st.markdown(f'<div style="background:{bc};border:1px solid {brc};border-left:4px solid {brc};border-radius:12px;padding:12px 18px;margin-bottom:18px;display:flex;align-items:center;gap:12px"><span style="font-size:11px;font-weight:700;color:{tc_};text-transform:uppercase;letter-spacing:.08em;background:rgba(0,0,0,.06);padding:4px 10px;border-radius:20px">{ptag}</span><span style="font-size:14px;color:#1A2B1A;font-weight:500">{ptxt}</span></div>',unsafe_allow_html=True)
        ca,cb=st.columns([1.1,1])
        with ca: st.markdown("<div style='font-weight:600;color:#1A2B1A;margin-bottom:6px'>Expense breakdown</div>",unsafe_allow_html=True); st.plotly_chart(pie_chart(exp,p.get("owns_home",False)),use_container_width=True,config={"displayModeBar":False})
        with cb: st.markdown("<div style='font-weight:600;color:#1A2B1A;margin-bottom:6px'>Monthly cashflow</div>",unsafe_allow_html=True); st.plotly_chart(cashflow_chart(inc,texp,invested),use_container_width=True,config={"displayModeBar":False})
        st.markdown("<div style='font-weight:600;color:#1A2B1A;margin:12px 0 8px'>💡 Insights</div>",unsafe_allow_html=True)
        insights=ana.get("insights",[])
        if insights:
            cols=st.columns(min(3,len(insights)))
            for i,ins in enumerate(insights[:3]):
                with cols[i%len(cols)]: st.markdown(f'<div class="insight-card {ins["type"]}"><div class="insight-title">{ins["title"]}</div><div class="insight-sub">{ins["text"]}</div></div>',unsafe_allow_html=True)

    with tab2: tab_budget()
    with tab3: tab_alerts()
    with tab4: tab_weekly_report()
    with tab5: tab_sip()
    with tab6: tab_tax()
    with tab7: tab_statement()
    with tab8: tab_market()
    with tab9: tab_chat()


# ══════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    st.markdown('<div style="padding:1.5rem 0 .5rem"><div style="font-size:34px;font-weight:700;color:#1A2B1A">💚 FinanceGPT</div><div style="font-size:16px;color:#6B7C6B;margin-top:8px;margin-bottom:28px">Your personal finance coach — built for Indian professionals 24–32</div></div>', unsafe_allow_html=True)
    auth_page()
elif st.session_state.step < 4:
    st.markdown('<div style="padding:1.5rem 0 .5rem"><div style="font-size:34px;font-weight:700;color:#1A2B1A">💚 FinanceGPT</div><div style="font-size:16px;color:#6B7C6B;margin-top:8px;margin-bottom:28px">Your personal finance coach — built for Indian professionals 24–32</div></div>', unsafe_allow_html=True)
    onboarding()
else:
    main_app()