import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Crypto Alerts BR 🇧🇷", layout="wide", page_icon="📈")

# CSS customizado
st.markdown("""
    <style>
    .big-font {font-size:24px !important; font-weight: bold;}
    .metric-positive {color: #00ff00;}
    .metric-negative {color: #ff4444;}
    </style>
    """, unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🚀 Crypto Alerts BR")
    st.markdown("**Monitor de criptomoedas em reais com análise inteligente**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.subheader("🔑 CoinGecko API")
    api_key = st.text_input("API Key", type="password", 
                            help="Cole a API Key que você recebeu")
    
    if not api_key:
        st.warning("⚠️ Cole sua API Key acima")
    else:
        st.success("✅ API Key configurada")
    
    st.divider()
    
    # Criptomoedas
    st.subheader("💰 Criptomoedas")
    cryptos = {
        "Bitcoin": "bitcoin",
        "Ethereum": "ethereum", 
        "Cardano": "cardano",
        "Solana": "solana",
        "Ripple": "ripple",
        "Polkadot": "polkadot",
        "Dogecoin": "dogecoin",
        "Chainlink": "chainlink"
    }
    
    selected = st.multiselect("Selecione", list(cryptos.keys()), default=["Bitcoin", "Ethereum"])
    
    st.divider()
    
    days = st.slider("Período histórico (dias)", 7, 30, 14)
    
    st.divider()
    
    # Waitlist Premium
    with st.expander("🔥 ACESSO PREMIUM - 50% OFF"):
        st.markdown("""
        ### Versão Premium em breve!
        
        ✅ 30+ criptomoedas
        ✅ Alertas Telegram automáticos
        ✅ Indicadores RSI/MACD
        ✅ Atualização em tempo real
        ✅ Análise de portfólio
        
        **De R$ 59,90 por R$ 29,90/mês**
        
        🎁 *Apenas para os primeiros 50 cadastros!*
        """)
        
        email_premium = st.text_input("Seu melhor email:", key="premium_email")
        whatsapp_premium = st.text_input("WhatsApp (opcional):", key="premium_whatsapp")
        
        if st.button("🚀 Garantir Vaga com 50% OFF", type="primary", use_container_width=True):
            if email_premium:
                st.success(f"✅ Email {email_premium} cadastrado! Você receberá acesso em breve.")
                st.balloons()
            else:
                st.error("Por favor, preencha seu email")
    
    st.divider()
    
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Funções
@st.cache_data(ttl=300)
def get_brl_rate():
    try:
        r = requests.get("https://api.frankfurter.dev/v1/latest?base=USD", timeout=10)
        if r.status_code == 200:
            return r.json()["rates"].get("BRL", 5.0)
    except:
        return 5.0
    return 5.0

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
    st.warning("⚠️ **Configure sua API Key do CoinGecko no sidebar para começar**")
    
    st.info("📖 **Você acabou de criar sua conta?** Cole a API Key que você copiou no campo ao lado →")
    
    with st.expander("🎓 Como usar este app"):
        st.markdown("""
        ### Passo a passo:
        
        1. **Cole sua API Key** no sidebar (você acabou de copiar)
        2. **Selecione criptomoedas** que deseja monitorar
        3. **Ajuste o período** de análise (7-30 dias)
        4. **Clique em Atualizar** para ver os dados
        
        ### Recursos atuais:
        - 📊 Gráficos interativos
        - 💵 Preços em Reais (BRL)
        - 📈 Análise de variação
        - 🧮 Calculadora de investimento
        - 📋 Ranking de performance
        """)
    
    st.stop()

# Taxa BRL
brl_rate = get_brl_rate()
st.sidebar.metric("💵 Câmbio Atual", f"R$ {brl_rate:.2f}/USD")

# Dashboard
if not selected:
    st.info("👈 Selecione pelo menos uma criptomoeda no sidebar")
    st.stop()

# Métricas resumidas
st.header("📊 Visão Geral")

metric_cols = st.columns(len(selected))
crypto_data = {}

for idx, name in enumerate(selected):
    crypto_id = cryptos[name]
    df, error = fetch_crypto(crypto_id, days, api_key)
    
    if df is not None and len(df) > 1:
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        price_brl = latest["price"] * brl_rate
        change = ((latest["price"] - previous["price"]) / previous["price"] * 100)
        
        crypto_data[name] = {"df": df, "latest": latest, "change": change, "price_brl": price_brl}
        
        with metric_cols[idx]:
            st.metric(
                name, 
                f"R$ {price_brl:,.2f}",
                f"{change:+.2f}%"
            )

st.divider()

# Ranking
st.header("🏆 Ranking de Performance (24h)")

if crypto_data:
    ranking_data = []
    for name, data in crypto_data.items():
        ranking_data.append({
            "Cripto": name,
            "Preço (BRL)": f"R$ {data['price_brl']:,.2f}",
            "Variação 24h": f"{data['change']:+.2f}%",
            "Status": "🟢 Alta" if data['change'] > 0 else "🔴 Queda"
        })
    
    ranking_df = pd.DataFrame(ranking_data)
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)

st.divider()

# Calculadora de Investimento
st.header("🧮 Calculadora de Investimento")

calc_cols = st.columns(4)

with calc_cols[0]:
    calc_crypto = st.selectbox("Criptomoeda", selected)

with calc_cols[1]:
    invested_brl = st.number_input("Valor investido (R$)", min_value=0.0, value=1000.0, step=100.0)

with calc_cols[2]:
    if calc_crypto in crypto_data:
        current_price = crypto_data[calc_crypto]["price_brl"]
        buy_price = st.number_input("Preço de compra (R$)", min_value=0.0, value=current_price * 0.9, step=10.0)
    else:
        buy_price = st.number_input("Preço de compra (R$)", min_value=0.0, value=100.0)

with calc_cols[3]:
    if st.button("💰 Calcular", type="primary"):
        if calc_crypto in crypto_data:
            current_price = crypto_data[calc_crypto]["price_brl"]
            quantity = invested_brl / buy_price
            current_value = quantity * current_price
            profit = current_value - invested_brl
            profit_pct = (profit / invested_brl) * 100
            
            result_cols = st.columns(3)
            result_cols[0].metric("Valor Atual", f"R$ {current_value:,.2f}", f"{profit:+,.2f}")
            result_cols[1].metric("Lucro/Prejuízo", f"R$ {profit:+,.2f}")
            result_cols[2].metric("Rentabilidade", f"{profit_pct:+.2f}%")

st.divider()

# Tabs com análises detalhadas
st.header("📈 Análise Detalhada")

tabs = st.tabs(selected)

for idx, (name, tab) in enumerate(zip(selected, tabs)):
    crypto_id = cryptos[name]
    
    with tab:
        if name in crypto_data:
            data = crypto_data[name]
            df = data["df"]
            
            # Gráfico
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df["price"],
                mode='lines',
                name='Preço USD',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))
            
            # Média móvel
            df['ma7'] = df['price'].rolling(window=7).mean()
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df["ma7"],
                mode='lines',
                name='Média 7 dias',
                line=dict(color='orange', width=1, dash='dash')
            ))
            
            fig.update_layout(
                title=f"{name} - Últimos {days} dias",
                xaxis_title="Data",
                yaxis_title="Preço (USD)",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas
            st.subheader("📊 Estatísticas do Período")
            
            stat_cols = st.columns(5)
            stat_cols[0].metric("Máxima", f"${df['price'].max():,.2f}")
            stat_cols[1].metric("Mínima", f"${df['price'].min():,.2f}")
            stat_cols[2].metric("Média", f"${df['price'].mean():,.2f}")
            stat_cols[3].metric("Volatilidade", f"{df['price'].std():,.2f}")
            
            total_change = ((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0] * 100)
            stat_cols[4].metric(f"Variação {days}d", f"{total_change:+.2f}%")
            
            # Análise
            st.subheader("💡 Análise Técnica Simplificada")
            
            change = data['change']
            
            if change > 5:
                st.success(f"🟢 **{name} está em alta forte** (+{change:.2f}% nas últimas 24h)")
            elif change > 0:
                st.info(f"🔵 **{name} está em leve alta** (+{change:.2f}% nas últimas 24h)")
            elif change > -5:
                st.warning(f"🟡 **{name} está em leve queda** ({change:.2f}% nas últimas 24h)")
            else:
                st.error(f"🔴 **{name} está em queda forte** ({change:.2f}% nas últimas 24h)")
        else:
            st.error(f"Erro ao carregar dados de {name}")

# Footer
st.divider()

footer_cols = st.columns([2, 1, 1])

with footer_cols[0]:
    st.caption(f"🕐 Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")

with footer_cols[1]:
    st.caption("📊 Dados: CoinGecko API | 💱 Câmbio: Frankfurter")

with footer_cols[2]:
    st.caption("🇧🇷 Desenvolvido no Brasil")

# CTA Premium
st.info("💎 **Gostou?** Cadastre-se no sidebar para ter acesso antecipado à versão Premium com 50% OFF!")
