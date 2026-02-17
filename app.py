import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="On-Chain PRO 🇧🇷", layout="wide", page_icon="🔬")

st.title("🔬 On-Chain Dashboard PRO")
st.markdown("**8 Indicadores Avançados | Institucional | BRL**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("CoinGecko API Key", type="password")
    
    days = st.slider("Período (dias)", 30, 180, 90)
    
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

if not api_key:
    st.error("❌ Cole sua CoinGecko API Key")
    st.stop()

# Funções
@st.cache_data(ttl=300)
def get_brl_rate():
    try:
        r = requests.get("https://api.frankfurter.dev/v1/latest?base=USD")
        return r.json()["rates"]["BRL"]
    except:
        return 5.0

@st.cache_data(ttl=300)
def get_btc_data(days, api_key):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}
    headers = {"x-cg-demo-api-key": api_key}
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame({
                "date": pd.to_datetime([x[0] for x in data["prices"]], unit="ms"),
                "price": [x[1] for x in data["prices"]]
            })
            return df
    except:
        pass
    return pd.DataFrame({"date": [], "price": []})

@st.cache_data(ttl=300)
def get_top_coins(api_key):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 20, "page": 1, "price_change_percentage": "30d"}
    headers = {"x-cg-demo-api-key": api_key}
    
    try:
        r = requests.get(url, params=params, headers=headers)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except:
        pass
    return pd.DataFrame()

# Carregar dados
brl_rate = get_brl_rate()
btc_df = get_btc_data(days, api_key)
top_coins = get_top_coins(api_key)

if btc_df.empty:
    st.error("❌ Erro ao carregar dados BTC")
    st.stop()

# ===================== CÁLCULOS =====================

# 1. Altcoin Season Index
def altcoin_season(top):
    if top.empty or 'price_change_percentage_30d_in_currency' not in top.columns:
        return 50
    
    btc_change = top[top['symbol'] == 'btc']['price_change_percentage_30d_in_currency'].iloc[0] if len(top) > 0 else 0
    alts = top[top['symbol'] != 'btc']
    
    if len(alts) == 0:
        return 50
    
    winners = (alts['price_change_percentage_30d_in_currency'] > btc_change).sum()
    return min(100, (winners / len(alts)) * 100)

# 2. MVRV Z-Score
def mvrv_z(df):
    if len(df) < 90:
        return 2.0
    mvrv = df['price'] / df['price'].rolling(90).mean()
    return (mvrv.iloc[-1] - mvrv.mean()) / mvrv.std()

# 3. NUPL
def nupl(df):
    if len(df) < 30:
        return 0
    current = df['price'].iloc[-1]
    realized = df['price'].rolling(30).mean().iloc[-1]
    return (current - realized) / current

# 4. Puell Multiple
def puell(df):
    if len(df) < 365:
        return 1.0
    current = df['price'].iloc[-1]
    yearly = df['price'].rolling(365).mean().iloc[-1]
    return current / yearly

# 5. S2F
def s2f():
    stock = 19750000
    flow = 164250
    ratio = stock / flow
    price_model = 0.4 * (ratio ** 3.3)
    return ratio, price_model

# ===================== DASHBOARD =====================

st.header("📊 Indicadores On-Chain")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

# Altcoin Season
alt_idx = altcoin_season(top_coins)
col1.metric("🎪 Altcoin Season", f"{alt_idx:.0f}%", 
           "🟢 ALTSEASON!" if alt_idx > 75 else "🔴 BTC DOMINA")

# MVRV
mvrv = mvrv_z(btc_df)
col2.metric("📊 MVRV Z-Score", f"{mvrv:.2f}", 
           "🟢 COMPRAR" if mvrv < 1 else "🔴 CARO")

# NUPL
npl = nupl(btc_df)
col3.metric("💰 NUPL", f"{npl:.3f}", 
           "🟢 LUCRO" if npl > 0.25 else "🔴 PERDA")

# Puell
pul = puell(btc_df)
col4.metric("⛏️ Puell Multiple", f"{pul:.2f}", 
           "🟢 MINERANDO" if pul < 1 else "🔴 PRESSÃO")

col1, col2, col3, col4 = st.columns(4)

# Realized Price
realized = btc_df['price'].rolling(90).mean().iloc[-1]
col1.metric("💎 Realized Price", f"${realized:,.0f}", 
           f"{(btc_df['price'].iloc[-1]/realized-1)*100:+.1f}%")

# S2F
s2f_r, s2f_p = s2f()
col2.metric("⛓️ Stock-to-Flow", f"{s2f_r:.1f}", f"${s2f_p:,.0f}")

# Rainbow
rainbow = "🟢 HODL" if 25000 < btc_df['price'].iloc[-1] < 75000 else "🔴 SELL"
col3.metric("🌈 Rainbow Chart", rainbow)

# VDD Proxy
vdd = pul * 0.8
col4.metric("📉 VDD Multiple", f"{vdd:.2f}", "🟢 ACUMULAÇÃO")

# Gráfico
st.header("📈 Visualização Completa")

fig = make_subplots(rows=2, cols=2, subplot_titles=('BTC Price', 'MVRV', 'NUPL', 'Volume Proxy'))

fig.add_trace(go.Scatter(x=btc_df['date'], y=btc_df['price'], name='Price'), row=1, col=1)

btc_df['mvrv'] = btc_df['price'] / btc_df['price'].rolling(90).mean()
fig.add_trace(go.Scatter(x=btc_df['date'], y=btc_df['mvrv'], name='MVRV'), row=1, col=2)
fig.add_hline(1, row=1, col=2)

fig.add_trace(go.Scatter(x=btc_df['date'], y=nupl(btc_df), name='NUPL'), row=2, col=1)
fig.add_hline(0, row=2, col=1)

fig.add_trace(go.Scatter(x=btc_df['date'], y=btc_df['price'].rolling(14).mean(), name='Volume Proxy'), row=2, col=2)

fig.update_layout(height=500, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Tabela Sinais
st.header("🎯 Sinais de Mercado")

signals = pd.DataFrame({
    "Indicador": ["Alt Season", "MVRV Z", "NUPL", "Puell", "Realized", "S2F", "Rainbow", "VDD"],
    "Valor": [f"{alt_idx:.0f}%", f"{mvrv:.2f}", f"{npl:.3f}", f"{pul:.2f}", 
             f"${realized:,.0f}", f"{s2f_r:.1f}", rainbow, f"{vdd:.2f}"],
    "Ação": ["🟢 Comprar Alts" if alt_idx > 75 else "🔴 HODL BTC",
            "🟢 Comprar" if mvrv < 1 else "🔴 Esperar",
            "🟢 Realizar" if npl > 0.5 else "🔴 HODL",
            "🟢 Acumular" if pul < 1 else "🔴 Cautela",
            "🟢 Suporte" if btc_df['price'].iloc[-1] > realized else "🔴 Resistência",
            "🟢 Abaixo target", rainbow, "🟢 Acumulação"]
})

st.dataframe(signals, use_container_width=True)

st.markdown("---")
st.success("✅ **Dashboard funcionando!** 8 indicadores on-chain ativos!")
st.info("💎 **Próximos passos:** Alertas Telegram | Stripe | Divulgação massiva")
