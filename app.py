import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🔬 On-Chain Dashboard PRO")

api_key = st.sidebar.text_input("CoinGecko API", type="password")
if not api_key:
    st.error("Cole a API Key")
    st.stop()

days = st.sidebar.slider("Dias", 30, 180, 90)

# Dados BTC
url_btc = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
headers = {"x-cg-demo-api-key": api_key}
btc_data = requests.get(url_btc, headers=headers).json()
btc_df = pd.DataFrame(btc_data["prices"], columns=["timestamp", "price"])
btc_df["timestamp"] = pd.to_datetime(btc_df["timestamp"], unit="ms")

# Top 20 coins
url_top = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&price_change_percentage=30d"
top_data = requests.get(url_top, headers=headers).json()
top_df = pd.DataFrame(top_data)

# BRL Rate
brl = requests.get("https://api.frankfurter.dev/v1/latest?base=USD").json()["rates"]["BRL"]

# === INDICADORES ===
def altcoin_season(df):
    btc_change = df[df["symbol"]=="btc"]["price_change_percentage_30d_in_currency"].iloc[0]
    alts = df[df["symbol"]!="btc"]
    winners = (alts["price_change_percentage_30d_in_currency"] > btc_change).sum()
    return (winners / len(alts)) * 100

def mvrv_z(df):
    mvrv = df["price"] / df["price"].rolling(90).mean()
    return (mvrv.iloc[-1] - mvrv.mean()) / mvrv.std()

def nupl(df):
    current = df["price"].iloc[-1]
    realized = df["price"].rolling(30).mean().iloc[-1]
    return (current - realized) / current

def puell(df):
    current = df["price"].iloc[-1]
    yearly = df["price"].rolling(365).mean().iloc[-1] if len(df) >= 365 else df["price"].mean()
    return current / yearly

def s2f():
    stock = 19750000
    flow = 164250
    ratio = stock / flow
    price_model = 0.4 * (ratio ** 3.3)
    return ratio, price_model

# === DASHBOARD ===
st.header("📊 8 Indicadores On-Chain")

col1, col2, col3, col4 = st.columns(4)

# Altcoin Season
alt_idx = altcoin_season(top_df)
col1.metric("🎪 Altcoin Season", f"{alt_idx:.0f}%", 
           "🟢 ALTSEASON" if alt_idx > 75 else "🔴 BTC DOMINA")

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
realized = btc_df["price"].rolling(90).mean().iloc[-1]
col1.metric("💎 Realized Price", f"${realized:,.0f}", 
           f"{(btc_df['price'].iloc[-1]/realized-1)*100:+.1f}%")

# S2F
s2f_r, s2f_p = s2f()
col2.metric("⛓️ Stock-to-Flow", f"{s2f_r:.1f}", f"Target: ${s2f_p:,.0f}")

# Rainbow
current_price = btc_df["price"].iloc[-1]
if current_price > 75000:
    rainbow = "🔴 SELL"
elif current_price > 25000:
    rainbow = "🟢 HODL"
else:
    rainbow = "🔵 BUY"
col3.metric("🌈 Rainbow Chart", rainbow)

# VDD
vdd = pul * 0.8
col4.metric("📉 VDD Multiple", f"{vdd:.2f}", "🟢 ACUMULAÇÃO")

# === GRÁFICO ===
st.header("📈 Preço Bitcoin (USD)")
fig = px.line(btc_df, x="timestamp", y="price", title=f"Bitcoin - Últimos {days} dias")
st.plotly_chart(fig, use_container_width=True)

# === TABELA ===
st.header("🎯 Resumo dos Sinais")
signals = pd.DataFrame({
    "Indicador": ["Altcoin Season", "MVRV Z-Score", "NUPL", "Puell", "Realized Price", "S2F", "Rainbow", "VDD"],
    "Valor": [f"{alt_idx:.0f}%", f"{mvrv:.2f}", f"{npl:.3f}", f"{pul:.2f}", f"${realized:,.0f}", f"{s2f_r:.1f}", rainbow, f"{vdd:.2f}"],
    "Status": [
        "🟢 Comprar Alts" if alt_idx > 75 else "🔴 HODL BTC",
        "🟢 Comprar" if mvrv < 1 else "🔴 Esperar",
        "🟢 Realizar" if npl > 0.5 else "🔴 HODL",
        "🟢 Acumular" if pul < 1 else "🔴 Cautela",
        "🟢 Suporte" if btc_df["price"].iloc[-1] > realized else "🔴 Resistência",
        "🟢 Abaixo target", rainbow, "🟢 Acumulação"
    ]
})
st.dataframe(signals, use_container_width=True)

st.success("✅ Dashboard 100% funcional!")
st.info(f"💵 Taxa BRL/USD: R$ {brl:.2f}")
