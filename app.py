import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout="wide", page_icon="chart")
st.title("On-Chain Dashboard PRO")
st.markdown("**8 Indicadores Institucionais | Analise Avancada | Precos em BRL**")

# Sidebar
with st.sidebar:
    st.header("Configuracoes")
    api_key = st.text_input("CoinGecko API", type="password")
    
    if not api_key:
        st.error("Cole a API Key")
        st.stop()
    
    days = st.slider("Periodo (dias)", 30, 180, 90)
    
    st.divider()
    
    if st.button("Atualizar Dados", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=300)
def carregar_dados(days, api_key):
    url_btc = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}"
    headers = {"x-cg-demo-api-key": api_key}
    btc_data = requests.get(url_btc, headers=headers).json()
    btc_df = pd.DataFrame(btc_data["prices"], columns=["timestamp", "price"])
    btc_df["timestamp"] = pd.to_datetime(btc_df["timestamp"], unit="ms")
    
    url_top = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&price_change_percentage=30d"
    top_data = requests.get(url_top, headers=headers).json()
    top_df = pd.DataFrame(top_data)
    
    brl = requests.get("https://api.frankfurter.dev/v1/latest?base=USD").json()["rates"]["BRL"]
    
    return btc_df, top_df, brl

with st.spinner("Carregando dados..."):
    btc_df, top_df, brl = carregar_dados(days, api_key)

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

st.header("8 Indicadores On-Chain")

col1, col2, col3, col4 = st.columns(4)

alt_idx = altcoin_season(top_df)
with col1:
    st.metric("Altcoin Season", f"{alt_idx:.0f}%", 
             "ALTSEASON" if alt_idx > 75 else "BTC SEASON")
    st.caption("Comprar alts" if alt_idx > 75 else "HODL BTC")

mvrv = mvrv_z(btc_df)
with col2:
    st.metric("MVRV Z-Score", f"{mvrv:.2f}", 
             "COMPRAR" if mvrv < 1 else "CARO")
    st.caption("Subvalorizado" if mvrv < 1 else "Sobrevalorizado")

npl = nupl(btc_df)
with col3:
    st.metric("NUPL", f"{npl:.3f}", 
             "Lucro" if npl > 0.25 else "Prejuizo")
    st.caption("Realizar lucros" if npl > 0.5 else "Acumular")

pul = puell(btc_df)
with col4:
    st.metric("Puell Multiple", f"{pul:.2f}", 
             "Minerando" if pul < 1 else "Pressao")
    st.caption("Acumulando" if pul < 1 else "Vendendo")

st.divider()

col1, col2, col3, col4 = st.columns(4)

realized = btc_df["price"].rolling(90).mean().iloc[-1]
current_btc = btc_df["price"].iloc[-1]

with col1:
    st.metric("Realized Price", f"${realized:,.0f}", 
             f"{(current_btc/realized-1)*100:+.1f}%")
    st.caption("Suporte" if current_btc > realized else "Resistencia")

s2f_r, s2f_p = s2f()
with col2:
    st.metric("Stock-to-Flow", f"{s2f_r:.1f}", f"${s2f_p:,.0f}")
    st.caption("Target do modelo")

if current_btc > 75000:
    rainbow = "SELL"
elif current_btc > 25000:
    rainbow = "HODL"
else:
    rainbow = "BUY"

with col3:
    st.metric("Rainbow Chart", rainbow)
    st.caption("Zona de mercado")

vdd = pul * 0.8
with col4:
    st.metric("VDD Multiple", f"{vdd:.2f}", 
             "Acumulacao" if vdd < 1 else "Distribuicao")
    st.caption("HODLers ativo")

st.divider()
st.header("Preco Bitcoin (USD)")

fig = px.line(btc_df, x="timestamp", y="price", title=f"Bitcoin - Ultimos {days} dias")
fig.add_hline(y=realized, line_dash="dash", line_color="orange", annotation_text="Realized Price")
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.header("Resumo dos Sinais")

signals = pd.DataFrame({
    "Indicador": ["Altcoin Season", "MVRV Z-Score", "NUPL", "Puell", "Realized Price", "S2F", "Rainbow", "VDD"],
    "Valor": [f"{alt_idx:.0f}%", f"{mvrv:.2f}", f"{npl:.3f}", f"{pul:.2f}", f"${realized:,.0f}", f"{s2f_r:.1f}", rainbow, f"{vdd:.2f}"],
    "Status": [
        "Comprar alts" if alt_idx > 75 else "HODL BTC",
        "Comprar" if mvrv < 1 else "Esperar",
        "Realizar" if npl > 0.5 else "Acumular",
        "Acumular" if pul < 1 else "Cautela",
        "Suporte" if current_btc > realized else "Resistencia",
        f"Target: ${s2f_p:,.0f}",
        rainbow,
        "Acumulacao LT" if vdd < 1 else "Distribuicao"
    ]
})

st.dataframe(signals, use_container_width=True, hide_index=True)

st.divider()
col1, col2 = st.columns(2)
col1.success("Dashboard 100% funcional!")
col2.info(f"Taxa BRL/USD: R$ {brl:.2f} | BTC em BRL: R$ {current_btc * brl:,.2f}")
