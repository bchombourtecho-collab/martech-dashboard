import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Binder · LinkedIn Ads Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-delta-positive { color: #34d399; }
    h1 { color: #60a5fa; }
    h2, h3 { color: #93c5fd; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# ── Load & clean data ──────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(base, 'data_campañas.csv'), encoding='utf-8-sig')

    # Parse dates
    df['date'] = pd.to_datetime(df['Start Date (in UTC)'], format='%m/%d/%Y')
    df['month'] = df['date'].dt.strftime('%b %Y')
    df['month_order'] = df['date'].dt.to_period('M')

    # Numeric columns
    num_cols = [
        'Total Spent', 'Impressions', 'Clicks', 'Click Through Rate',
        'Average CPM', 'Average CPC', 'Reactions', 'Comments', 'Shares',
        'Follows', 'Total Engagements', 'Engagement Rate',
        'Leads', 'Lead Forms Opened', 'Lead Form Completion Rate',
        'Cost per Lead', 'Leads (Work Email)', 'Cost Per Lead (Work Email)',
        'Clicks to Landing Page', 'Total Social Actions',
        'Conversions', 'Post-Click Conversions', 'View-Through Conversions',
        'Conversion Rate', 'Cost per Conversion',
        'Viral Impressions', 'Viral Clicks', 'Viral Reactions',
        'Card Impressions', 'Card Clicks',
        'Sends', 'Opens', 'Open Rate',
        'Clicks (Sponsored Messaging)',
        'Average Dwell Time (in Seconds)',
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Columnas unificadas: InMail usa Sends/Clicks(SM), el resto usa Impressions/Clicks
    is_inmail = df['Campaign Name'].str.upper().str.contains('INMAIL')
    df['uni_impressions'] = np.where(is_inmail, df['Sends'],                          df['Impressions'])
    df['uni_clicks']      = np.where(is_inmail, df['Clicks (Sponsored Messaging)'],   df['Clicks'])

    # Legible campaign names
    CAMP_NAMES = {
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_CLM_P1_SINGLEIMAGE_291025': 'CLM · Fase 1 · Single Image · Oct 25',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_CLM_P2_SINGLEIMAGE_291025': 'CLM · Fase 2 · Single Image · Oct 25',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_CLM_P1_CARROUSEL_141025':   'CLM · Fase 1 · Carrusel · Oct 25',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_CLM_P2_CARROUSEL_041125':   'CLM · Fase 2 · Carrusel · Nov 25',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_SCORE_CARROUSEL_011225':     'SCORE · Carrusel · Dic 25',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_SCORE_INMAIL_190126':        'SCORE · InMail · Ene 26',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_SCORE_CARROUSEL_190126':     'SCORE · Carrusel · Ene 26',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_SPONSORED_190126':           'Sponsored · Ene 26',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_NARROW1_INMAIL_230226':      'Narrow 1 · InMail · Feb 26',
        'ADQ_LKD_CAMP_ADS_LEADMAGNET_BDR_SPONSORED_090326':           'Sponsored · Mar 26',
    }
    df['campaign_short'] = df['Campaign Name'].map(CAMP_NAMES).fillna(df['Campaign Name'])
    df['group_short'] = df['Campaign Group Name'].apply(
        lambda x: x.replace('ADQ_LKD_ADS_BDR_', '').replace('_', ' ')
    )

    # Ad format
    def ad_format(name):
        n = name.upper()
        if 'CARROUSEL' in n: return 'Carrusel'
        if 'INMAIL' in n: return 'InMail'
        if 'SINGLEIMAGE' in n: return 'Single Image'
        if 'SPONSORED' in n: return 'Sponsored Content'
        return 'Otro'

    df['ad_format'] = df['Campaign Name'].apply(ad_format)

    return df

df = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://thelegalbinder.com/favicon.ico", width=40)
    st.title("Binder · LinkedIn Ads")
    st.markdown("---")

    months_available = sorted(df['month_order'].unique())
    month_labels = [str(m) for m in months_available]
    selected_months = st.multiselect(
        "Meses",
        options=month_labels,
        default=month_labels,
    )

    groups = df['group_short'].unique().tolist()
    selected_groups = st.multiselect(
        "Grupo de campaña",
        options=groups,
        default=groups,
    )

    formats = df['ad_format'].unique().tolist()
    selected_formats = st.multiselect(
        "Formato de anuncio",
        options=formats,
        default=formats,
    )

    st.markdown("---")
    st.caption("Datos reales · LinkedIn Campaign Manager\nCuenta: 515713485")

# ── Filter ──────────────────────────────────────────────────────────────────────
mask = (
    df['month_order'].astype(str).isin(selected_months) &
    df['group_short'].isin(selected_groups) &
    df['ad_format'].isin(selected_formats)
)
fdf = df[mask].copy()

# Aggregate by campaign for charts
by_camp = fdf.groupby('campaign_short', as_index=False).agg(
    Spent=('Total Spent', 'sum'),
    Impressions=('Impressions', 'sum'),
    Clicks=('Clicks', 'sum'),
    Leads=('Leads', 'sum'),
    LeadForms=('Lead Forms Opened', 'sum'),
    Reactions=('Reactions', 'sum'),
    Shares=('Shares', 'sum'),
    Comments=('Comments', 'sum'),
    Engagements=('Total Engagements', 'sum'),
    ClicksLP=('Clicks to Landing Page', 'sum'),
    DwellTime=('Average Dwell Time (in Seconds)', 'mean'),
)
by_camp['CPL'] = by_camp['Spent'] / by_camp['Leads'].replace(0, np.nan)
by_camp['CTR'] = by_camp['Clicks'] / by_camp['Impressions'].replace(0, np.nan) * 100
by_camp['CPM'] = by_camp['Spent'] / by_camp['Impressions'].replace(0, np.nan) * 1000
by_camp['LeadConvRate'] = by_camp['Leads'] / by_camp['Clicks'].replace(0, np.nan) * 100

# Aggregate by month
by_month = fdf.groupby(['month_order', 'month'], as_index=False).agg(
    Spent=('Total Spent', 'sum'),
    Impressions=('Impressions', 'sum'),
    Clicks=('Clicks', 'sum'),
    Leads=('Leads', 'sum'),
    Engagements=('Total Engagements', 'sum'),
).sort_values('month_order')

# Monthly efficiency metrics (recalculated from totals, not averaged)
by_month['CPM'] = by_month['Spent'] / by_month['Impressions'].replace(0, np.nan) * 1000
by_month['CTR'] = by_month['Clicks'] / by_month['Impressions'].replace(0, np.nan) * 100
by_month['CPC'] = by_month['Spent'] / by_month['Clicks'].replace(0, np.nan)
by_month['CPL'] = by_month['Spent'] / by_month['Leads'].replace(0, np.nan)

# Month-over-month % change
for metric in ['CPM', 'CTR', 'CPC', 'CPL']:
    by_month[f'{metric}_delta'] = by_month[metric].pct_change() * 100

# Aggregate by format
by_format = fdf.groupby('ad_format', as_index=False).agg(
    Spent=('Total Spent', 'sum'),
    UniImpressions=('uni_impressions', 'sum'),
    UniClicks=('uni_clicks', 'sum'),
    Leads=('Leads', 'sum'),
)
by_format['CPM'] = by_format['Spent'] / by_format['UniImpressions'].replace(0, np.nan) * 1000
by_format['CTR'] = by_format['UniClicks'] / by_format['UniImpressions'].replace(0, np.nan) * 100
by_format['CPC'] = by_format['Spent']    / by_format['UniClicks'].replace(0, np.nan)
by_format['CPL'] = by_format['Spent']    / by_format['Leads'].replace(0, np.nan)

# ── Header ───────────────────────────────────────────────────────────────────────
st.title("⚖️ Binder · LinkedIn Ads Dashboard")
st.markdown(f"**Período:** Oct 2025 – Mar 2026 &nbsp;|&nbsp; **Cuenta:** 515713485 &nbsp;|&nbsp; **Moneda:** PEN")
st.markdown("---")

# ── KPIs ─────────────────────────────────────────────────────────────────────────
total_spent = fdf['Total Spent'].sum()
total_impressions = fdf['Impressions'].sum()
total_clicks = fdf['Clicks'].sum()
total_leads = fdf['Leads'].sum()
total_lead_forms = fdf['Lead Forms Opened'].sum()
avg_cpl = total_spent / total_leads if total_leads else 0
avg_ctr = total_clicks / total_impressions * 100 if total_impressions else 0
avg_cpm = total_spent / total_impressions * 1000 if total_impressions else 0
avg_cpc = total_spent / total_clicks if total_clicks else 0
lead_form_rate = total_leads / total_lead_forms * 100 if total_lead_forms else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("💰 Total Invertido", f"S/ {total_spent:,.2f}")
col2.metric("👁️ Impresiones", f"{total_impressions:,.0f}")
col3.metric("🖱️ Clicks", f"{total_clicks:,.0f}")
col4.metric("🎯 Leads", f"{int(total_leads):,}")
col5.metric("💵 Costo por Lead", f"S/ {avg_cpl:,.2f}")
col6.metric("📋 Lead Form Rate", f"{lead_form_rate:.1f}%")

st.markdown("---")

# ── Row 1: Tendencia mensual ──────────────────────────────────────────────────────
col_l, col_r = st.columns([2, 1])

with col_l:
    st.subheader("Inversión y Leads por Mes")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=by_month['month'], y=by_month['Spent'],
        name='Spend (S/)', marker_color='#3b82f6', yaxis='y1',
    ))
    fig.add_trace(go.Scatter(
        x=by_month['month'], y=by_month['Leads'],
        name='Leads', mode='lines+markers+text',
        marker=dict(size=10, color='#f59e0b'),
        line=dict(color='#f59e0b', width=3),
        text=by_month['Leads'].astype(int),
        textposition='top center',
        yaxis='y2',
    ))
    fig.update_layout(
        height=340, template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0),
        legend=dict(orientation='h', y=-0.25),
        yaxis=dict(title='Spend (S/)', showgrid=False),
        yaxis2=dict(title='Leads', overlaying='y', side='right', showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader("Mix por Formato")
    fig2 = px.pie(
        by_format, values='Leads', names='ad_format',
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.45, template='plotly_dark',
    )
    fig2.update_layout(
        height=340,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0),
        legend=dict(orientation='h', y=-0.2),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: CPL y Leads por campaña ───────────────────────────────────────────────
col_l2, col_r2 = st.columns(2)

with col_l2:
    st.subheader("Costo por Lead por Campaña")
    camp_cpl = by_camp[by_camp['CPL'].notna()].sort_values('CPL')
    fig3 = px.bar(
        camp_cpl, x='CPL', y='campaign_short', orientation='h',
        color='CPL', color_continuous_scale='RdYlGn_r',
        text=camp_cpl['CPL'].apply(lambda x: f"S/ {x:,.0f}"),
        template='plotly_dark',
        labels={'CPL': 'Costo por Lead (S/)', 'campaign_short': ''},
    )
    fig3.update_traces(textposition='outside')
    fig3.update_layout(
        height=380,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0), coloraxis_showscale=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

with col_r2:
    st.subheader("Leads por Campaña")
    camp_leads = by_camp[by_camp['Leads'] > 0].sort_values('Leads', ascending=True)
    fig4 = px.bar(
        camp_leads, x='Leads', y='campaign_short', orientation='h',
        color='Leads', color_continuous_scale='Blues',
        text='Leads', template='plotly_dark',
        labels={'Leads': 'Leads generados', 'campaign_short': ''},
    )
    fig4.update_traces(textposition='outside')
    fig4.update_layout(
        height=380,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0), coloraxis_showscale=False,
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Engagement + Clicks trend ─────────────────────────────────────────────
col_l3, col_r3 = st.columns(2)

with col_l3:
    st.subheader("CTR y CPM por Campaña")
    camp_metrics = by_camp[by_camp['CTR'].notna()].copy()
    fig5 = px.scatter(
        camp_metrics,
        x='CPM', y='CTR',
        size='Leads',
        color='campaign_short',
        text='campaign_short',
        template='plotly_dark',
        labels={'CPM': 'CPM (S/)', 'CTR': 'CTR (%)', 'campaign_short': 'Campaña'},
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig5.update_traces(textposition='top center', textfont_size=9)
    fig5.update_layout(
        height=360,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0), showlegend=False,
    )
    st.plotly_chart(fig5, use_container_width=True)

with col_r3:
    st.subheader("Impresiones y Clicks por Mes")
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=by_month['month'], y=by_month['Impressions'],
        name='Impresiones', marker_color='#6366f1', yaxis='y1',
    ))
    fig6.add_trace(go.Scatter(
        x=by_month['month'], y=by_month['Clicks'],
        name='Clicks', mode='lines+markers',
        marker=dict(size=8, color='#f472b6'),
        line=dict(color='#f472b6', width=2),
        yaxis='y2',
    ))
    fig6.update_layout(
        height=360, template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=0),
        legend=dict(orientation='h', y=-0.25),
        yaxis=dict(showgrid=False),
        yaxis2=dict(overlaying='y', side='right', showgrid=False),
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── Tabla detalle por campaña ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Detalle por Campaña")

table = by_camp.copy()
table = table.sort_values('Leads', ascending=False)
table['Spent'] = table['Spent'].apply(lambda x: f"S/ {x:,.2f}" if pd.notna(x) else '-')
table['CPL'] = table['CPL'].apply(lambda x: f"S/ {x:,.2f}" if pd.notna(x) else '-')
table['CTR'] = table['CTR'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else '-')
table['CPM'] = table['CPM'].apply(lambda x: f"S/ {x:,.2f}" if pd.notna(x) else '-')
table['LeadConvRate'] = table['LeadConvRate'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else '-')
table['Leads'] = table['Leads'].apply(lambda x: int(x) if pd.notna(x) else 0)
table['Impressions'] = table['Impressions'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '-')
table['Clicks'] = table['Clicks'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '-')

display_cols = {
    'campaign_short': 'Campaña',
    'Spent': 'Inversión',
    'Impressions': 'Impresiones',
    'Clicks': 'Clicks',
    'CTR': 'CTR',
    'CPM': 'CPM',
    'Leads': 'Leads',
    'CPL': 'Costo/Lead',
    'LeadConvRate': 'Lead Conv. Rate',
}
st.dataframe(
    table[list(display_cols.keys())].rename(columns=display_cols),
    use_container_width=True,
    hide_index=True,
)

# ── Comparativa de eficiencia por formato ─────────────────────────────────────────
st.markdown("---")
st.subheader("Eficiencia por Formato de Anuncio")
st.caption("Comparativa de métricas clave desde plataforma (CPM, CTR, CPC) hasta resultado final (CPL)")

FORMAT_COLORS = {
    'Carrusel':         '#6366f1',
    'InMail':           '#f59e0b',
    'Single Image':     '#10b981',
    'Sponsored Content':'#f472b6',
}

fmt_valid = by_format.dropna(subset=['CPM','CTR','CPC','CPL'])

# 4 mini bar charts en 2 filas × 2 columnas
METRIC_CFG = [
    ('CPM', 'CPM (S/)',      'S/ {:.2f}', True,  'Costo por Mil Impresiones'),
    ('CTR', 'CTR (%)',       '{:.2f}%',   False, 'Click Through Rate'),
    ('CPC', 'CPC (S/)',      'S/ {:.2f}', True,  'Costo por Click'),
    ('CPL', 'CPL (S/)',      'S/ {:.2f}', True,  'Costo por Lead'),
]

row_a, row_b = st.columns(2), st.columns(2)
grid = [row_a[0], row_a[1], row_b[0], row_b[1]]

for ax, (key, label, fmt, lower_better, title) in zip(grid, METRIC_CFG):
    df_sorted = fmt_valid.sort_values(key, ascending=lower_better)
    colors = [FORMAT_COLORS.get(f, '#94a3b8') for f in df_sorted['ad_format']]
    texts  = [fmt.format(v) for v in df_sorted[key]]

    fig = go.Figure(go.Bar(
        x=df_sorted['ad_format'],
        y=df_sorted[key],
        marker_color=colors,
        text=texts,
        textposition='outside',
        textfont=dict(size=12),
    ))

    # Highlight best (first after sort)
    best_idx = 0
    marker_line_colors = ['#ffffff' if i == best_idx else 'rgba(0,0,0,0)'
                          for i in range(len(df_sorted))]
    fig.update_traces(marker_line_color=marker_line_colors, marker_line_width=2)

    note = '↓ menor es mejor' if lower_better else '↑ mayor es mejor'
    fig.update_layout(
        title=dict(text=f'<b>{title}</b><br><sup>{note}</sup>', font=dict(size=13)),
        height=300,
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=55, b=10, l=10, r=10),
        yaxis=dict(showgrid=False, showticklabels=False),
        xaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
    )
    ax.plotly_chart(fig, use_container_width=True)

# Heatmap resumen (normalizado por rango 0-1 para comparar en misma escala)
st.markdown("##### Mapa de calor comparativo (mejor → peor por métrica)")

heat_formats = fmt_valid['ad_format'].tolist()
heat_metrics = [('CPM', True), ('CTR', False), ('CPC', True), ('CPL', True)]
heat_labels  = ['CPM (S/)', 'CTR (%)', 'CPC (S/)', 'CPL (S/)']

z_norm = []   # normalized 0→1 where 1 = best
z_text = []
for _, row in fmt_valid.iterrows():
    row_z = []
    row_t = []
    for (m, lower), lbl in zip(heat_metrics, heat_labels):
        val = row[m]
        col_vals = fmt_valid[m].dropna()
        mn, mx = col_vals.min(), col_vals.max()
        rng = mx - mn if mx != mn else 1
        norm = (val - mn) / rng          # 0 = worst raw
        score = (1 - norm) if lower else norm   # 1 = best
        row_z.append(score)
        fmt_str = 'S/ {:.2f}' if m != 'CTR' else '{:.2f}%'
        row_t.append(fmt_str.format(val))
    z_norm.append(row_z)
    z_text.append(row_t)

fig_heat2 = go.Figure(go.Heatmap(
    z=z_norm,
    x=heat_labels,
    y=heat_formats,
    text=z_text,
    texttemplate='%{text}',
    textfont=dict(size=14, color='white'),
    colorscale=[[0, '#7f1d1d'], [0.5, '#374151'], [1, '#14532d']],
    zmin=0, zmax=1,
    showscale=False,
))
fig_heat2.update_layout(
    height=220,
    template='plotly_dark',
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=10, b=10, l=120, r=20),
    xaxis=dict(side='top', tickfont=dict(size=13)),
    yaxis=dict(tickfont=dict(size=12)),
)
st.plotly_chart(fig_heat2, use_container_width=True)
st.caption("🟢 Verde = mejor rendimiento · 🔴 Rojo = peor rendimiento · Escala normalizada por métrica")

# ── Tabla comparativa de variaciones mensuales ────────────────────────────────────
st.markdown("---")
st.subheader("Variaciones Mensuales de Eficiencia")
st.caption("Comparación mes a mes de las métricas clave de costo y rendimiento")

# ── Heatmap de % cambio ───────────────────────────────────────────────────────────
METRICS = {
    'CPM':  {'label': 'CPM (S/)',  'lower_is_better': True,  'fmt': 'S/ {:.2f}'},
    'CTR':  {'label': 'CTR (%)',   'lower_is_better': False, 'fmt': '{:.2f}%'},
    'CPC':  {'label': 'CPC (S/)',  'lower_is_better': True,  'fmt': 'S/ {:.2f}'},
    'CPL':  {'label': 'CPL (S/)',  'lower_is_better': True,  'fmt': 'S/ {:.2f}'},
}

months_sorted = by_month.sort_values('month_order')['month'].tolist()
metric_keys   = list(METRICS.keys())

# Build value matrix and delta matrix
val_matrix   = []   # raw values
delta_matrix = []   # % change vs prev month
text_matrix  = []   # cell text: value + delta
color_matrix = []   # numeric score: positive=favorable, negative=unfavorable

months_sorted_df = by_month.sort_values('month_order').reset_index(drop=True)

for _, row in months_sorted_df.iterrows():
    val_row   = []
    delta_row = []
    text_row  = []
    color_row = []
    for m in metric_keys:
        val   = row[m]
        delta = row[f'{m}_delta']
        cfg   = METRICS[m]

        # Format value
        if pd.isna(val):
            val_row.append(np.nan)
            delta_row.append(np.nan)
            text_row.append('—')
            color_row.append(0)
        else:
            val_row.append(val)
            delta_row.append(delta if pd.notna(delta) else 0)

            delta_str = ''
            score = 0
            if pd.notna(delta) and delta != 0:
                sign = '+' if delta > 0 else ''
                delta_str = f'\n{sign}{delta:.1f}%'
                # Score: favorable = green direction
                if cfg['lower_is_better']:
                    score = -delta   # decrease = good (positive score)
                else:
                    score = delta    # increase = good (positive score)

            text_row.append(cfg['fmt'].format(val) + delta_str)
            color_row.append(score)

    val_matrix.append(val_row)
    delta_matrix.append(delta_row)
    text_matrix.append(text_row)
    color_matrix.append(color_row)

fig_heat = go.Figure(data=go.Heatmap(
    z=color_matrix,
    x=[METRICS[m]['label'] for m in metric_keys],
    y=months_sorted,
    text=text_matrix,
    texttemplate='%{text}',
    textfont=dict(size=13),
    colorscale=[
        [0.0,  '#7f1d1d'],
        [0.35, '#dc2626'],
        [0.48, '#374151'],
        [0.52, '#374151'],
        [0.65, '#16a34a'],
        [1.0,  '#14532d'],
    ],
    zmin=-60, zmax=60,
    showscale=False,
    hoverongaps=False,
))

fig_heat.update_layout(
    height=320,
    template='plotly_dark',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(t=10, b=10, l=80, r=20),
    xaxis=dict(side='top', tickfont=dict(size=13)),
    yaxis=dict(tickfont=dict(size=12)),
)

st.plotly_chart(fig_heat, use_container_width=True)
st.caption("🟢 Verde = mejora · 🔴 Rojo = deterioro · Primera fila sin Δ% (base)")

# ── Tabla numérica detallada ──────────────────────────────────────────────────────
with st.expander("Ver tabla numérica completa"):
    tbl = months_sorted_df[['month', 'Spent', 'Impressions', 'Clicks', 'Leads',
                             'CPM', 'CTR', 'CPC', 'CPL',
                             'CPM_delta', 'CTR_delta', 'CPC_delta', 'CPL_delta']].copy()

    def fmt_delta(v):
        if pd.isna(v): return '—'
        sign = '+' if v > 0 else ''
        return f'{sign}{v:.1f}%'

    tbl['CPM_Δ'] = tbl['CPM_delta'].apply(fmt_delta)
    tbl['CTR_Δ'] = tbl['CTR_delta'].apply(fmt_delta)
    tbl['CPC_Δ'] = tbl['CPC_delta'].apply(fmt_delta)
    tbl['CPL_Δ'] = tbl['CPL_delta'].apply(fmt_delta)
    tbl['CPM']   = tbl['CPM'].apply(lambda x: f'S/ {x:.2f}' if pd.notna(x) else '—')
    tbl['CTR']   = tbl['CTR'].apply(lambda x: f'{x:.2f}%' if pd.notna(x) else '—')
    tbl['CPC']   = tbl['CPC'].apply(lambda x: f'S/ {x:.2f}' if pd.notna(x) else '—')
    tbl['CPL']   = tbl['CPL'].apply(lambda x: f'S/ {x:.2f}' if pd.notna(x) else '—')
    tbl['Spent'] = tbl['Spent'].apply(lambda x: f'S/ {x:,.2f}')
    tbl['Impressions'] = tbl['Impressions'].apply(lambda x: f'{int(x):,}')
    tbl['Clicks'] = tbl['Clicks'].apply(lambda x: f'{int(x):,}')
    tbl['Leads']  = tbl['Leads'].apply(lambda x: f'{int(x):,}')
    tbl = tbl.rename(columns={
        'month': 'Mes', 'Spent': 'Invertido', 'Impressions': 'Impresiones',
        'Clicks': 'Clicks', 'Leads': 'Leads',
    })
    st.dataframe(
        tbl[['Mes','Invertido','Impresiones','Clicks','Leads',
             'CPM','CPM_Δ','CTR','CTR_Δ','CPC','CPC_Δ','CPL','CPL_Δ']],
        use_container_width=True, hide_index=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Fuente: LinkedIn Campaign Manager · Cuenta 515713485 · Binder Legal Ops")
