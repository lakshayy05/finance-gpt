from fastapi import APIRouter
import yfinance as yf
from datetime import datetime
import pytz

router = APIRouter(prefix="/api/market", tags=["market"])

# ── Symbols ───────────────────────────────────────────────────────
SYMBOLS = {
    "nifty50":   {"ticker": "^NSEI",   "name": "Nifty 50",    "type": "index"},
    "sensex":    {"ticker": "^BSESN",  "name": "Sensex",      "type": "index"},
    "banknifty": {"ticker": "^NSEBANK","name": "Bank Nifty",  "type": "index"},
    "gold":      {"ticker": "GC=F",    "name": "Gold",        "type": "commodity", "unit": "per 10g"},
    "silver":    {"ticker": "SI=F",    "name": "Silver",      "type": "commodity", "unit": "per kg"},
    "usdinr":    {"ticker": "USDINR=X","name": "USD/INR",     "type": "forex"},
}

# Approx troy oz conversions for Indian units
GOLD_OZ_TO_10G   = 10 / 31.1035   # 1 troy oz = 31.1g → per 10g
SILVER_OZ_TO_KG  = 1000 / 31.1035  # per kg


def _get_inr_rate() -> float:
    """Fetch live USD to INR conversion rate."""
    try:
        t = yf.Ticker("USDINR=X")
        info = t.fast_info
        return float(info.last_price or 83.5)
    except Exception:
        return 83.5  # fallback


def _fetch_one(ticker_sym: str, name: str, sym_type: str, unit: str = "", inr_rate: float = 83.5) -> dict:
    try:
        t    = yf.Ticker(ticker_sym)
        info = t.fast_info

        price  = float(info.last_price or 0)
        prev   = float(info.previous_close or price)
        change = price - prev
        pct    = (change / prev * 100) if prev else 0

        # Convert commodity prices to INR
        if sym_type == "commodity":
            if "GC" in ticker_sym:   # Gold per 10g in INR
                price  = price  * inr_rate * GOLD_OZ_TO_10G
                prev   = prev   * inr_rate * GOLD_OZ_TO_10G
                change = price - prev
                pct    = (change / prev * 100) if prev else 0
            elif "SI" in ticker_sym:  # Silver per kg in INR
                price  = price  * inr_rate * SILVER_OZ_TO_KG
                prev   = prev   * inr_rate * SILVER_OZ_TO_KG
                change = price - prev
                pct    = (change / prev * 100) if prev else 0

        return {
            "name":        name,
            "price":       round(price, 2),
            "change":      round(change, 2),
            "change_pct":  round(pct, 2),
            "direction":   "up" if change >= 0 else "down",
            "type":        sym_type,
            "unit":        unit,
        }
    except Exception as e:
        return {
            "name": name, "price": 0, "change": 0,
            "change_pct": 0, "direction": "flat",
            "type": sym_type, "unit": unit,
            "error": str(e),
        }


@router.get("/prices")
def get_market_prices():
    """
    Returns live prices for Nifty 50, Sensex, Bank Nifty,
    Gold (per 10g INR), Silver (per kg INR), USD/INR.
    Cached at the route level — refresh every 5 mins in production.
    """
    inr_rate = _get_inr_rate()
    data     = {}

    for key, meta in SYMBOLS.items():
        data[key] = _fetch_one(
            meta["ticker"], meta["name"],
            meta["type"], meta.get("unit", ""), inr_rate
        )

    ist = pytz.timezone("Asia/Kolkata")
    data["fetched_at"] = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")
    data["usd_inr"]    = round(inr_rate, 2)
    return data


@router.get("/history/{symbol}")
def get_history(symbol: str, period: str = "1mo"):
    """
    Returns historical price data for a symbol.
    symbol: nifty50 | sensex | banknifty | gold | silver
    period: 1d | 5d | 1mo | 3mo | 6mo | 1y
    """
    if symbol not in SYMBOLS:
        return {"error": f"Unknown symbol: {symbol}"}

    meta   = SYMBOLS[symbol]
    inr_rate = _get_inr_rate()

    try:
        t    = yf.Ticker(meta["ticker"])
        hist = t.history(period=period)
        if hist.empty:
            return {"data": [], "symbol": symbol}

        rows = []
        for date, row in hist.iterrows():
            close = float(row["Close"])
            # Convert commodities to INR
            if meta["type"] == "commodity":
                if "GC" in meta["ticker"]:
                    close = close * inr_rate * GOLD_OZ_TO_10G
                elif "SI" in meta["ticker"]:
                    close = close * inr_rate * SILVER_OZ_TO_KG
            rows.append({
                "date":  date.strftime("%d %b"),
                "price": round(close, 2),
            })
        return {"data": rows, "symbol": symbol, "name": meta["name"]}
    except Exception as e:
        return {"error": str(e), "data": []}