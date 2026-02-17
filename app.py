import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Crypto Alerts BR 🇧🇷", layout="wide", page_icon="📈")

# CSS
st.markdown("""
    <style>
    .big-font {font-size:20px !important; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Crypto Alerts BR")
st.markdown("**Monitor de criptomoedas em reais com indicadores técnicos**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.subheader("🔑 CoinGecko API")
    api_key = st.text_input("API Key", type="password", 
                            help="Crie em: coingecko.com/en/developers/dashboard")
    
    st.divider()
    
    st.subheader("💰 Criptomoedas")
    cryptos = {
        "Bitcoin": "bitcoin",
        "Ethereum": "ethereum", 
        "Cardano": "cardano",
        "Solana": "solana"
    }
    
    selected = st.multiselect("Selecione", list(cryptos.keys()), default=["Bitcoin"])
    
    st.divider()
    
    days = st.slider("Período (dias)", 7, 30, 14)
    
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

# Taxa BRL
@st.cache_data(ttl=300)
def get_brl_rate():
    try:
        r = requests.get("https://api.frankfurter.dev/v1/latest?base=USD", timeout=10)
        if r.status_code == 200:
            return r.json()["rates"].get("BRL", 5.0)
    except:
        return 5.0
    return 5.0

# Dados cripto
@st.cache_data(ttl=300)
def fetch_crypto(symbol, days, api_key):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}
        headers = {"x-cg-demo-api-key": api_key} if api_key else {}
        
        r = requests.get(url, params=params, headers=headers, timeout=15)
        
        if r.status_code == 401:
            return None, "API Key inválida"
        if r.status_code == 429:
            return None, "Limite de API atingido"
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame({
                "timestamp": pd.to_datetime([x[0] for x in data["prices"]], unit="ms"),
                "price": [x[1] for x in data["prices"]]
            })
            return df, None
    except Exception as e:
        return None, str(e)
    return None, "Erro desconhecido"

# Verificar API
if not api_key:
    st.warning("⚠️ **Configure sua API Key do CoinGecko no sidebar**")
    st.info("📖 **Como obter:** Acesse coingecko.com/en/developers/dashboard")
    st.stop()

# Taxa
brl_rate = get_brl_rate()
st.sidebar.metric("💵 BRL/USD", f"R$ {brl_rate:.2f}")

# Dashboard
if not selected:
    st.info("👈 Selecione criptomoedas no sidebar")
    st.stop()

st.header("📊 Dashboard")

tabs = st.tabs(selected)

for idx, (name, tab) in enumerate(zip(selected, tabs)):
    crypto_id = cryptos[name]
    
    with tab:
        st.subheader(name)
        
        with st.spinner("Carregando..."):
            df, error = fetch_crypto(crypto_id, days, api_key)
        
        if error:
            st.error(f"❌ Erro: {error}")
            continue
        
        if df is None or len(df) == 0:
            st.error("❌ Sem dados disponíveis")
            continue
        
        # Métricas
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        price_brl = latest["price"] * brl_rate
        change = ((latest["price"] - previous["price"]) / previous["price"] * 100)
        
        cols = st.columns(3)
        cols[0].metric("Preço (BRL)", f"R$ {price_brl:,.2f}", f"{change:+.2f}%")
        cols[1].metric("Preço (USD)", f"${latest['price']:,.2f}")
        cols[2].metric("Volume 24h", f"${df['price'].iloc[-1]:,.0f}")
        
        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"],
            y=df["price"],
            mode='lines',
            name='Preço',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.update_layout(
            title=f"{name} - Últimos {days} dias",
            xaxis_title="Data",
            yaxis_title="Preço (USD)",
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Estatísticas")
            st.metric("Máxima", f"${df['price'].max():,.2f}")
            st.metric("Mínima", f"${df['price'].min():,.2f}")
        
        with col2:
            st.markdown("### 💡 Status")
            if change > 5:
                st.success("🟢 Alta forte (+5%)")
            elif change > 0:
                st.info("🔵 Alta moderada")
            elif change > -5:
                st.warning("🟡 Queda moderada")
            else:
                st.error("🔴 Queda forte (-5%)")

# Footer
st.divider()
cols = st.columns(3)
cols[0].caption(f"🕐 Atualizado: {datetime.now().strftime('%H:%M:%S')}")
cols[1].caption("📊 Dados: CoinGecko")
cols[2].caption("🇧🇷 by Ramkar987")
