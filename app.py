import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import ta

st.set_page_config(page_title="Crypto On-Chain PRO 🇧🇷", layout="wide", page_icon="🔬")

st.markdown("""
<style>
.metric-bull {background: linear-gradient(90deg, #00ff88 0%, #00cc66 100%);}
.metric-bear {background: linear-gradient(90deg, #ff4444 0%, #cc3333 100%);}
.big-title {font-size: 28px !important;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="big-title">🔬 Crypto On-Chain Dashboard PRO</h1>', unsafe_allow_html=True)
st.markdown("**8 Indicadores Institucionais | Preços em BRL | Análise Avançada**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.subheader("🔑 CoinGecko API")
    api_key = st.text_input("API Key", type="password")
    
    st.divider()
    
    period = st.slider("Período (dias)", 30, 365, 90)
    
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

if not api_key:
    st.error("❌ **Cole sua CoinGecko API Key no sidebar**")
    st.stop()

# ===================== FUNÇÕES =====================

@st.cache_data(ttl=300)
def get_brl_rate():
    try:
        r = requests.get("https://api.frankfurter.dev/v1/latest?base=USD")
        return r.json()["rates"]["BRL"]
    except:
        return 5.0

@st.cache_data(ttl=300)
def fetch_btc_data(days, api_key):
    """Dados históricos BTC"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}
        headers = {"x-cg-demo-api-key": api_key}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame({
                "timestamp": pd.to_datetime([x[0] for x in data["prices"]], unit="ms"),
                "price": [x[1] for x in data["prices"]]
            })
            return df
    except Exception as e:
        st.error(f"Erro BTC: {e}")
    return None

@st.cache_data(ttl=300)
def get_top_20_coins(api_key):
    """Top 20 coins para Altcoin Index"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "price_change_percentage": "30d"
        }
        headers = {"x-cg-demo-api-key": api_key}
        r = requests.get(url, params=params, headers=headers)
        
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            return df
    except:
        pass
    return pd.DataFrame()

brl_rate = get_brl_rate()

# ===================== CÁLCULOS DOS INDICADORES =====================

def altcoin_season(top_coins):
    """Altcoin Season Index"""
    if top_coins.empty:
        return 50
    
    btc_change = top_coins[top_coins['symbol'] == 'btc']['price_change_percentage_30d_in_currency'].iloc[0] if 'btc' in top_coins['symbol'].values else 0
    alts = top_coins[top_coins['symbol'] != 'btc']
    
    outperforming = (alts['price_change_percentage_30d_in_currency'] > btc_change).sum()
    return min(100, (outperforming / len(alts)) * 100)

def mvrv_zscore(df):
    """MVRV Z-Score"""
    if df is None or len(df) < 90:
        return 2.0
    
    market_cap = df['price']
    realized_cap = market_cap.rolling(90).mean()
    mvrv = market_cap / realized_cap
    
    mean_mvrv = mvrv.mean()
    std_mvrv = mvrv.std()
    
    return (mvrv.iloc[-1] - mean_mvrv) / std_mvrv if std_mvrv > 0 else 0

def nupl(df):
    """Net Unrealized Profit/Loss"""
    if df is None or len(df) < 30:
        return 0
    
    current = df['price'].iloc[-1]
    realized = df['price'].rolling(30).mean().iloc[-1]
    return (current - realized) / current

def puell_multiple(df):
    """Puell Multiple"""
    if df is None or len(df) < 365:
        return 1.0
    
    current = df['price'].iloc[-1]
    yearly_avg = df['price'].rolling(365).mean().iloc[-1]
    return current / yearly_avg

def stock_to_flow():
    """S2F aproximado post-halving 2024"""
    stock = 19750000  # BTC atual
    flow = 164250     # Annual issuance
    s2f_ratio = stock / flow
    
    # Modelo PlanB
    price_model = 0.4 * (s2f_ratio ** 3.3)
    return s2f_ratio, price_model

def rainbow_chart(price):
    """Bitcoin Rainbow Chart"""
    log_price = np.log(price)
    
    if price > 100000:
        return "🔴 MAX BUBBLE"
    elif price > 50000:
        return "🟠 FOMO"
    elif price > 25000:
        return "🟡 HODL!"
    elif price > 10000:
        return "🟢 STILL CHEAP"
    else:
        return "🔵 BUY!"

# ===================== DASHBOARD =====================

st.header("📊 8 Indicadores On-Chain")

# Carregar dados
btc_df = fetch_btc_data(period, api_key)
top_coins = get_top_20_coins(api_key)

if btc_df is None:
    st.error("❌ Erro ao carregar dados BTC. Verifique API Key.")
    st.stop()

# Row 1: 4 principais
col1, col2, col3, col4 = st.columns(4)

# Altcoin Season
alt_idx = altcoin_season(top_coins)
col1.metric("Altcoin Season Index", f"{alt_idx:.0f}%", 
           "🟢 ALTSEASON" if alt_idx > 75 else "🔴 BTC SEASON")

# MVRV Z-Score
mvrv_z = mvrv_zscore(btc_df)
col2.metric("MVRV Z-Score", f"{mvrv_z:.2f}", 
           "🟢 BARATO" if mvrv_z < 1 else "🔴 CARO")

# NUPL
nupl_val = nupl(btc_df)
col3.metric("NUPL", f"{nupl_val:.3f}", 
           "🟢 LUCRO" if nupl_val > 0.25 else "🔴 PREJUÍZO")

# Puell Multiple
puell = puell_multiple(btc_df)
col4.metric("Puell Multiple", f"{puell:.2f}", 
           "🟢 MINERANDO" if puell < 1 else "🔴 VENDENDO")

# Row 2: 4 secundários
col1, col2, col3, col4 = st.columns(4)

# Realized Price Proxy
realized_proxy = btc_df['price'].rolling(90).mean().iloc[-1]
col1.metric("Realized Price", f"${realized_proxy:,.0f}", 
           "🟢 SUPORTE" if btc_df['price'].iloc[-1] > realized_proxy else "🔴 RESISTÊNCIA")

# S2F
s2f_ratio, s2f_price = stock_to_flow()
col2.metric("Stock-to-Flow", f"{s2f_ratio:.1f}", f"${s2f_price:,.0f}")

# Rainbow Chart
rainbow = rainbow_chart(btc_df['price'].iloc[-1])
col3.metric("Rainbow Chart", rainbow)

# VDD Proxy (simplificado)
vdd_proxy = puell * 0.8
col4.metric("VDD Multiple", f"{vdd_proxy:.2f}", "🟢 ACUMULAÇÃO")

# Gráfico
st.header("📈 Gráficos On-Chain")

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Preço BTC', 'MVRV Ratio', 'RSI 14', 'NUPL'),
    vertical_spacing=0.1
)

# Preço BTC
fig.add_trace(go.Scatter(x=btc_df['timestamp'], y=btc_df['price'], 
                        name='BTC USD'), row=1, col=1)

# MVRV
btc_df['mvrv'] = btc_df['price'] / btc_df['price'].rolling(90).mean()
fig.add_trace(go.Scatter(x=btc_df['timestamp'], y=btc_df['mvrv'], 
                        name='MVRV'), row=1, col=2)
fig.add_hline(1, row=1, col=2, line_dash="dash")

# RSI
btc_df['rsi'] = ta.momentum.RSIIndicator(btc_df['price']).rsi()
fig.add_trace(go.Scatter(x=btc_df['timestamp'], y=btc_df['rsi'], 
                        name='RSI'), row=2, col=1)
fig.add_hline(70, row=2, col=1, line_dash="dash", line_color="red")
fig.add_hline(30, row=2, col=1, line_dash="dash", line_color="green")

# NUPL
fig.add_trace(go.Scatter(x=btc_df['timestamp'], y=nupl(btc_df), 
                        name='NUPL'), row=2, col=2)
fig.add_hline(0, row=2, col=2, line_dash="dash")

fig.update_layout(height=600, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Tabela Resumo
st.header("🎯 Resumo dos Sinais")

signals = pd.DataFrame({
    "Indicador": ["Altcoin Season", "MVRV Z-Score", "NUPL", "Puell", "Realized Price", "S2F", "Rainbow", "VDD"],
    "Valor": [f"{alt_idx:.0f}%", f"{mvrv_z:.2f}", f"{nupl_val:.3f}", f"{puell:.2f}", 
             f"${realized_proxy:,.0f}", f"{s2f_ratio:.1f}", rainbow, f"{vdd_proxy:.2f}"],
    "Sinal": ["🟢 Comprar Altcoins" if alt_idx > 75 else "🔴 HODL Bitcoin",
             "🟢 Comprar" if mvrv_z < 1 else "🔴 Caro",
             "🟢 Lucro" if nupl_val > 0.25 else "🔴 Prejuízo",
             "🟢 Minerando" if puell < 1 else "🔴 Pressão Venda",
             "🟢 Suporte" if btc_df['price'].iloc[-1] > realized_proxy else "🔴 Resistência",
             "🟢 Abaixo target", rainbow.split()[0], "🟢 Acumulação"]
})

st.dataframe(signals, use_container_width=True)

# Footer
st.markdown("---")
st.caption("🔬 **On-Chain PRO** | Dados CoinGecko | Feito no Brasil 🇧🇷")
st.info("💎 **Premium em breve:** Alertas Telegram | 50+ moedas | Portfolio tracker")
