import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_generator import generate_daily_traffic, generate_campaigns, generate_funnel, generate_email_metrics

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Martech Growth Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
        border: 1px solid #3a3a5c;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .block-container { padding-top: 1.5rem; }
    h1 { color: #a78bfa; }
    h2, h3 { color: #c4b5fd; }
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    traffic = generate_daily_traffic(90)
    campaigns = generate_campaigns()
    funnel = generate_funnel()
    email = generate_email_metrics(12)
    return traffic, campaigns, funnel, email

traffic_df, campaigns_df, funnel_df, email_df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Martech Growth")
    st.markdown("---")

    date_range = st.slider(
        "Período (últimos N días)",
        min_value=7, max_value=90, value=30, step=7
    )

    selected_channels = st.multiselect(
        "Canales",
        options=traffic_df["channel"].unique().tolist(),
        default=traffic_df["channel"].unique().tolist(),
    )

    st.markdown("---")
    st.caption("Datos de ejemplo generados para demo")

# ── Filter data ───────────────────────────────────────────────────────────────
from datetime import datetime, timedelta
cutoff = (datetime.today() - timedelta(days=date_range)).date()
filtered = traffic_df[
    (traffic_df["date"] >= cutoff) &
    (traffic_df["channel"].isin(selected_channels))
]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Martech Growth Dashboard")
st.markdown(f"Mostrando los últimos **{date_range} días** · {len(selected_channels)} canales activos")
st.markdown("---")

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_sessions = filtered["sessions"].sum()
total_conversions = filtered["conversions"].sum()
total_revenue = filtered["revenue"].sum()
conv_rate = total_conversions / total_sessions * 100 if total_sessions else 0
total_spend = campaigns_df["spend"].sum()
roas = total_revenue / total_spend if total_spend else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Sesiones", f"{total_sessions:,.0f}", "+12%")
col2.metric("Conversiones", f"{total_conversions:,.0f}", "+8%")
col3.metric("Revenue", f"${total_revenue:,.0f}", "+15%")
col4.metric("Conv. Rate", f"{conv_rate:.2f}%", "+0.3pp")
col5.metric("ROAS", f"{roas:.2f}x", "+0.4x")

st.markdown("---")

# ── Row 1: Traffic over time + Channel breakdown ──────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Tráfico por Canal")
    daily = filtered.groupby(["date", "channel"])["sessions"].sum().reset_index()
    fig = px.area(
        daily, x="date", y="sessions", color="channel",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        template="plotly_dark",
    )
    fig.update_layout(
        height=350, legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Mix de Canales")
    mix = filtered.groupby("channel")["sessions"].sum().reset_index()
    fig2 = px.pie(
        mix, values="sessions", names="channel",
        color_discrete_sequence=px.colors.qualitative.Vivid,
        template="plotly_dark", hole=0.45,
    )
    fig2.update_layout(
        height=350, showlegend=True,
        legend=dict(orientation="v", x=1.0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Funnel + Campaign performance ─────────────────────────────────────
col_left2, col_right2 = st.columns([1, 2])

with col_left2:
    st.subheader("Funnel de Conversión")
    fig3 = go.Figure(go.Funnel(
        y=funnel_df["stage"],
        x=funnel_df["count"],
        textinfo="value+percent initial",
        marker=dict(color=["#a78bfa", "#818cf8", "#6366f1", "#4f46e5", "#4338ca"]),
    ))
    fig3.update_layout(
        height=350, template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=0),
    )
    st.plotly_chart(fig3, use_container_width=True)

with col_right2:
    st.subheader("Performance de Campañas")
    fig4 = px.bar(
        campaigns_df.sort_values("roas", ascending=True),
        x="roas", y="campaign", orientation="h",
        color="roas",
        color_continuous_scale="Viridis",
        text="roas",
        template="plotly_dark",
        labels={"roas": "ROAS", "campaign": "Campaña"},
    )
    fig4.update_traces(texttemplate="%{text:.1f}x", textposition="outside")
    fig4.update_layout(
        height=350,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=0), coloraxis_showscale=False,
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Email metrics ──────────────────────────────────────────────────────
st.subheader("Email Marketing — Últimas 12 semanas")
col_e1, col_e2 = st.columns(2)

with col_e1:
    fig5 = px.line(
        email_df, x="week", y=["open_rate", "ctr"],
        template="plotly_dark",
        labels={"value": "%", "variable": "Métrica", "week": "Semana"},
        color_discrete_map={"open_rate": "#a78bfa", "ctr": "#34d399"},
        markers=True,
    )
    fig5.update_layout(
        title="Open Rate vs CTR (%)",
        height=300,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.3), margin=dict(t=40, b=0),
    )
    st.plotly_chart(fig5, use_container_width=True)

with col_e2:
    fig6 = px.bar(
        email_df, x="week", y="sent",
        template="plotly_dark",
        color_discrete_sequence=["#818cf8"],
        labels={"sent": "Emails enviados", "week": "Semana"},
    )
    fig6.update_layout(
        title="Volumen de Envíos",
        height=300,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=0),
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── Campaign table ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Detalle de Campañas")
display_cols = campaigns_df.copy()
display_cols["spend"] = display_cols["spend"].apply(lambda x: f"${x:,.0f}")
display_cols["revenue"] = display_cols["revenue"].apply(lambda x: f"${x:,.0f}")
display_cols["roas"] = display_cols["roas"].apply(lambda x: f"{x:.2f}x")
display_cols["ctr"] = display_cols["ctr"].apply(lambda x: f"{x:.2f}%")
display_cols["cpc"] = display_cols["cpc"].apply(lambda x: f"${x:.2f}")
display_cols.columns = ["Campaña", "Spend", "Revenue", "ROAS", "Impresiones", "Clicks", "Conversiones", "CTR", "CPC"]
st.dataframe(display_cols, use_container_width=True, hide_index=True)
