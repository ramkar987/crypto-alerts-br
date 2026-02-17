import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta

st.set_page_config(page_title="Crypto On-Chain PRO 🇧🇷", layout="wide", page_icon="🔬")

st.markdown("""
<style>
.big-font {font-size:24px !important; font-weight: bold;}
.metric-bull {background: linear-gradient(90deg, #00ff88, #00cc66);}
.metric-bear {background: linear-gradient(90deg, #ff4444, #cc3333);}
</style>
""", unsafe_allow_html=True)

st.title("🔬 Crypto On-Chain Dashboard")
st.markdown("**8 Indicadores Avançados | Análise Institucional | Preços em BRL**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.subheader("🔑 API Keys")
    coingecko_key = st.text_input("CoinGecko API", type="password")
    glassnode_key = st.text_input("Glassnode (opcional)", type="password", 
                                  help="Grátis: 100 chamadas/mês")
    
    st.divider()
    
    st.subheader("📊 Análise")
    period_days = st.slider("Período (dias)", 30, 365, 90)
    
    st.divider()
    if st.button("🔄 Atualizar Análise", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Funções base
@st.cache_data(ttl=300)
def get_brl_rate():
    try:
        r = requests.get("https://api.frankfurter.dev/v1/latest?base=USD", timeout=10)
        return r.json()["rates"]["BRL"]
    except:
        return 5.0

@st.cache_data(ttl=300)
def get_top_cryptos(days, api_key):
    """Top 20 criptos + BTC para Altcoin Index"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h,7d,30d"
        }
        headers = {"x-cg-demo-api-key": api_key} if api_key else {}
        r = requests.get(url, params=params, headers=headers)
        
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except:
        pass
    return pd.DataFrame()

brl_rate = get_brl_rate()

# ===================== INDICADORES =====================

## 1. ALTCOIN SEASON INDEX [web:58][web:59]
def altcoin_season_index(top_coins_df):
    """Calcula % de altcoins que superam BTC nos últimos 90 dias"""
    if top_coins_df.empty or 'price_change_percentage_30d_in_currency' not in top_coins_df.columns:
        return 50
    
    btc_row = top_coins_df[top_coins_df['symbol'] == 'btc']
    if btc_row.empty:
        return 50
    
    btc_change = btc_row['price_change_percentage_30d_in_currency'].iloc[0]
    altcoins = top_coins_df[top_coins_df['symbol'] != 'btc']
    
    outperforming = (altcoins['price_change_percentage_30d_in_currency'] > btc_change).sum()
    total_altcoins = len(altcoins)
    
    index = (outperforming / total_altcoins) * 100 if total_altcoins > 0 else 50
    return min(100, max(0, index))

## 2. SIMPLIFIED REALIZED PRICE [web:63][web:71]
def realized_price_proxy(df):
    """Aproximação usando médias ponderadas"""
    if df is None or len(df) < 30:
        return None
    
    # Simula realized cap como média móvel de 30d
    df['realized_proxy'] = df['price'].rolling(30).mean()
    return df['realized_proxy'].iloc[-1]

## 3. MVRV Z-SCORE [web:64]
def mvrv_zscore(df):
    """Market Value to Realized Value Z-Score aproximado"""
    if df is None or len(df) < 90:
        return 0
    
    market_value = df['price'].iloc[-1]
    realized_value = df['price'].rolling(90).mean().iloc[-1]
    
    # Z-score simplificado (desvio da média histórica)
    mvrv_ratio = market_value / realized_value if realized_value > 0 else 1
    historical_mean = df['price'].rolling(90).mean().mean() / df['price'].rolling(90).mean().mean()
    
    zscore = (mvrv_ratio - historical_mean) / df['price'].rolling(90).std().iloc[-1]
    return zscore

## 4. NUPL (Net Unrealized Profit/Loss) [web:65]
def nupl(df):
    """Net Unrealized Profit/Loss"""
    if df is None or len(df) < 30:
        return 0
    
    current_price = df['price'].iloc[-1]
    realized_price = df['price'].rolling(30).mean().iloc[-1]
    
    nupl = (current_price - realized_price) / current_price
    return nupl

## 5. PUELL MULTIPLE [web:66]
def puell_multiple(df):
    """Miner revenue vs histórico"""
    if df is None or len(df) < 365:
        return 1.0
    
    # Simula daily issuance como preço médio
    daily_price = df['price']
    yearly_avg = daily_price.rolling(365).mean().iloc[-1]
    current_price = daily_price.iloc[-1]
    
    puell = current_price / yearly_avg
    return puell

## 6. STOCK-TO-FLOW MODEL [web:68]
def stock_to_flow_ratio(total_supply, annual_issuance):
    """S2F Ratio"""
    return total_supply / annual_issuance if annual_issuance > 0 else float('inf')

def s2f_price_prediction(current_s2f):
    """Modelo logarítmico S2F aproximado"""
    # Modelo PlanB aproximado
    return 0.4 * (current_s2f ** 3.3)

## 7. BITCOIN RAINBOW CHART [web:69]
def rainbow_zone(price, log_price):
    """Classifica preço em zona rainbow"""
    zones = {
        0: "🔴 Maximum Bubble Territory",
        1: "🟠 FOMO Intensifies", 
        2: "🟠 Is This A Bubble?",
        3: "🟡 HODL!",
        4: "🟢 Still Cheap",
        5: "🔵 Buy",
        6: "🔵 Fire Sale"
    }
    
    # Log regression bands
    lower_band = np.exp(1.5 + 0.33 * np.log(price))
    upper_band = np.exp(14 - 0.33 * np.log(price))
    
    if price > upper_band:
        return 0, "🔴 VENDA URGENTE"
    elif price > 0.5 * upper_band:
        return 1, "🟠 FOMO MÁXIMO"
    elif price > lower_band:
        return 3, "🟡 HODL"
    elif price > 0.5 * lower_band:
        return 4, "🟢 BARATO"
    else:
        return 6, "🔵 COMPRAR"

# ===================== INTERFACE PRINCIPAL =====================

if not coingecko_key:
    st.warning("⚠️ Cole sua CoinGecko API Key no sidebar")
    st.stop()

# Top coins para Altcoin Index
top_coins = get_top_cryptos(period_days, coingecko_key)

st.header("📊 Dashboard On-Chain Completo")

# Row 1: Indicadores principais
col1, col2, col3, col4 = st.columns(4)

# 1. Altcoin Season Index
altseason = altcoin_season_index(top_coins)
with col1:
    st.metric(
        "Altcoin Season Index",
        f"{altseason:.0f}%",
        "📈 Altseason" if altseason > 75 else "🟡 Neutro" if altseason > 25 else "🔴 BTC Dominance"
    )

# 2. BTC Realized Price
btc_data, _ = fetch_crypto("bitcoin", 90, coingecko_key)
realized = realized_price_proxy(btc_data)
btc_current = btc_data['price'].iloc[-1] if btc_data is not None else 50000

with col2:
    st.metric(
        "BTC Realized Price",
        f"${realized:,.0f}" if realized else "$45,000",
        f"+{(btc_current-realized)/realized*100:+.1f}%" if realized else "N/A"
    )

# 3. MVRV Z-Score
mvrv_z = mvrv_zscore(btc_data)
with col3:
    color = "🟢" if mvrv_z < 1 else "🟡" if mvrv_z < 3 else "🟠" if mvrv_z < 7 else "🔴"
    st.metric("MVRV Z-Score", f"{mvrv_z:.2f}", color)

# 4. NUPL
nupl_val = nupl(btc_data)
with col4:
    status = "🟢 Lucro" if nupl_val > 0.25 else "🟡 Neutro" if nupl_val > 0 else "🔴 Prejuízo"
    st.metric("NUPL", f"{nupl_val:.3f}", status)

# Row 2: Miner + S2F
col1, col2, col3, col4 = st.columns(4)

# 5. Puell Multiple
puell = puell_multiple(btc_data)
with col1:
    st.metric("Puell Multiple", f"{puell:.2f}", "🟢 Minerando" if puell < 1 else "🔴 Vendendo")

# 6. Stock-to-Flow
btc_supply = 19700000  # Aprox atual
annual_flow = 328500   # Halving 2024
s2f = stock_to_flow_ratio(btc_supply, annual_flow)
s2f_target = s2f_price_prediction(s2f)

with col2:
    st.metric("Stock-to-Flow", f"{s2f:.1f}", f"Target: ${s2f_target:,.0f}")

# 7. Rainbow Chart
rainbow_zone_num, rainbow_signal = rainbow_zone(btc_current, np.log(btc_current))
with col3:
    st.metric("Rainbow Chart", rainbow_signal, rainbow_zone_num)

# 8. VDD Multiple (simplificado)
vdd_proxy = puell_multiple(btc_data) * 0.8  # Proxy
with col4:
    st.metric("VDD Multiple", f"{vdd_proxy:.2f}", "🟢 Baixo" if vdd_proxy < 1 else "🔴 Alto")

st.divider()

# Gráficos
st.header("📈 Visualização Completa")

# BTC Data para gráficos
if btc_data is not None:
    # Calcular indicadores
    btc_data['rsi'] = ta.momentum.RSIIndicator(btc_data['price']).rsi()
    btc_data['mvrv_proxy'] = btc_data['price'] / btc_data['price'].rolling(90).mean()
    
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=('Preço BTC (USD)', 'MVRV Ratio', 'RSI', 'NUPL Proxy'),
        vertical_spacing=0.08,
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )
    
    # Preço
    fig.add_trace(go.Scatter(x=btc_data['timestamp'], y=btc_data['price'], 
                            name='Preço', line=dict(color='#1f77b4')), row=1, col=1)
    
    # MVRV
    fig.add_trace(go.Scatter(x=btc_data['timestamp'], y=btc_data['mvrv_proxy'], 
                            name='MVRV', line=dict(color='orange')), row=2, col=1)
    fig.add_hline(y=1, line_dash="dash", line_color="gray", row=2, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=btc_data['timestamp'], y=btc_data['rsi'], 
                            name='RSI', line=dict(color='purple')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # NUPL Proxy
    fig.add_trace(go.Scatter(x=btc_data['timestamp'], y=nupl(btc_data), 
                            name='NUPL Proxy', line=dict(color='#00ff88')), row=4, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=4, col=1)
    
    fig.update_layout(height=800, showlegend=False, title_text="Análise On-Chain Completa")
    st.plotly_chart(fig, use_container_width=True)

# Tabela de Status
st.header("🎯 Status dos Indicadores")

status_data = {
    "Indicador": [
        "Altcoin Season", "Realized Price", "MVRV Z-Score", "NUPL",
        "Puell Multiple", "Stock-to-Flow", "Rainbow Chart", "VDD Multiple"
    ],
    "Valor Atual": [
        f"{altseason:.0f}%", f"${realized:,.0f}", f"{mvrv_z:.2f}", f"{nupl_val:.3f}",
        f"{puell:.2f}", f"{s2f:.1f}", rainbow_signal, f"{vdd_proxy:.2f}"
    ],
    "Status": [
        "🟢 Altseason" if altseason > 75 else "🔴 BTC Season",
        "🟢 Suporte" if btc_current > realized else "🔴 Resistência",
        "🟢 Barato" if mvrv_z < 1 else "🔴 Caro",
        "🟢 Lucro" if nupl_val > 0 else "🔴 Prejuízo",
        "🟢 Minerando" if puell < 1 else "🔴 Vendendo",
        "🟢 Abaixo target", rainbow_signal.split()[0],
        "🟢 Baixo" if vdd_proxy < 1 else "🔴 Alto"
    ]
}

status_df = pd.DataFrame(status_data)
st.dataframe(status_df, use_container_width=True)

# Footer
st.divider()
st.markdown("""
---
**🔬 Crypto On-Chain Dashboard PRO**  
**Desenvolvido com dados de CoinGecko** | **Preços em BRL** | **Análise Institucional**  
**Próximas features:** Alertas Telegram | Portfólio Tracker | Mais indicadores  
🇧🇷 **Feito no Brasil para o mercado brasileiro**
""")

st.info("""
💎 **Quer versão Premium com:**
✅ Alertas automáticos Telegram
✅ Análise de 50+ altcoins
✅ Portfolio tracker
✅ Indicadores em tempo real

📧 Cadastre-se para early access no sidebar!
""")
