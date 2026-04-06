"""Luna Web Search — live crypto, stock, weather data (no API keys needed)."""
import re, urllib.parse
try:
    import requests
    _OK = True
except ImportError:
    _OK = False

def _get(url, timeout=6):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        return r if r.status_code == 200 else None
    except Exception:
        return None

def get_crypto(coin: str) -> str:
    ids = {"btc":"bitcoin","bitcoin":"bitcoin","eth":"ethereum","ethereum":"ethereum",
           "sol":"solana","solana":"solana","bnb":"binancecoin","xrp":"ripple",
           "ripple":"ripple","ada":"cardano","doge":"dogecoin","dogecoin":"dogecoin",
           "ltc":"litecoin","dot":"polkadot","avax":"avalanche-2","matic":"matic-network",
           "polygon":"matic-network","link":"chainlink","uni":"uniswap","atom":"cosmos",
           "shib":"shiba-inu","trx":"tron","ton":"the-open-network"}
    cid = ids.get(coin.lower().strip(), coin.lower().strip())
    r = _get(f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true")
    if r:
        try:
            d = r.json().get(cid, {})
            price = d.get("usd",0); ch = d.get("usd_24h_change",0); mc = d.get("usd_market_cap",0)
            arrow = "▲" if ch >= 0 else "▼"
            return f"${price:,.2f} USD | 24h: {arrow}{abs(ch):.2f}% | MCap: ${mc/1e9:.2f}B"
        except Exception:
            pass
    return ""

def get_stock(sym: str) -> str:
    sym_map = {"apple":"AAPL","google":"GOOGL","microsoft":"MSFT","amazon":"AMZN",
               "tesla":"TSLA","nvidia":"NVDA","netflix":"NFLX","meta":"META","amd":"AMD"}
    sym = sym_map.get(sym.lower(), sym.upper())
    r = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d")
    if r:
        try:
            meta  = r.json()["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice",0); prev = meta.get("previousClose",0)
            ch    = ((price-prev)/prev*100) if prev else 0
            arrow = "▲" if ch >= 0 else "▼"
            return f"${price:.2f} USD | {arrow}{abs(ch):.2f}%"
        except Exception:
            pass
    return ""

def get_weather(city: str) -> str:
    r = _get(f"https://wttr.in/{urllib.parse.quote(city)}?format=j1")
    if r:
        try:
            c = r.json()["current_condition"][0]
            return (f"{c['weatherDesc'][0]['value']} | {c['temp_C']}°C ({c['temp_F']}°F) | "
                    f"Feels {c['FeelsLikeC']}°C | Humidity {c['humidity']}% | Wind {c['windspeedKmph']}km/h")
        except Exception:
            pass
    return ""

def detect_and_fetch(text: str) -> str:
    if not _OK: return ""
    tl = text.lower(); extra = ""
    # Crypto
    cm = re.search(r"\b(bitcoin|btc|ethereum|eth|solana|sol|bnb|xrp|ada|doge|dogecoin|"
                   r"ltc|litecoin|dot|avax|matic|polygon|link|shib|trx|ton|atom)\b", tl)
    if cm and re.search(r"(price|worth|cost|value|rate|usd|market|today|live|current|how much)", tl):
        p = get_crypto(cm.group(1))
        if p: extra += f"\n[LIVE] {cm.group(1).upper()} Price: {p}\n"
    # Stock
    sm = re.search(r"\b(aapl|apple|googl|google|msft|microsoft|amzn|amazon|tsla|tesla|"
                   r"meta|nvda|nvidia|nflx|netflix|amd|intc|spy|qqq)\b", tl)
    if sm and re.search(r"(stock|share|price|worth|trading)", tl):
        p = get_stock(sm.group(1))
        if p: extra += f"\n[LIVE] {sm.group(1).upper()} Stock: {p}\n"
    # Weather
    wm = re.search(r"weather\s+(?:in\s+|at\s+|for\s+)?([a-zA-Z ]{2,30})(?:\?|$| today| now)", tl)
    if not wm: wm = re.search(r"(?:temperature|temp|climate)\s+(?:in\s+|at\s+)?([a-zA-Z ]{2,20})(?:\?|$)", tl)
    if wm:
        city = wm.group(1).strip()
        if city:
            w = get_weather(city)
            if w: extra += f"\n[LIVE] Weather in {city.title()}: {w}\n"
    return extra
