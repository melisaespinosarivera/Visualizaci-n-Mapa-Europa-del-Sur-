import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ── CONFIG ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mujeres en I+D · Europa del Sur",
    page_icon="🔬",
    layout="wide",
)

# ══════════════════════════════════════════════════════════════════════════════
# 👇 CAMBIA ESTA RUTA por la ubicación real de tu archivo CSV
CSV_PATH = "/Users/melisaespinosarivera/Desktop/rd_p_perssci$defaultview_linear_2_0.csv"   # ← ruta relativa (misma carpeta que app.py)
# CSV_PATH = r"C:\Users\TuUsuario\Descargas\rd_p_perssci.csv"  # ← ruta absoluta Windows
# CSV_PATH = "/home/usuario/datos/rd_p_perssci.csv"            # ← ruta absoluta Linux/Mac
# ══════════════════════════════════════════════════════════════════════════════

# ── CSS personalizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
    }
    .main-title {
        font-family: 'Syne', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6C3FC5, #D64F8A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #888;
        font-size: 0.95rem;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }
    .kpi-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #D64F8A;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #6C3FC5 !important;
    }
    .note-box {
        background: #1a1a2e;
        border-left: 3px solid #6C3FC5;
        padding: 0.7rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.85rem;
        color: #aaa;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTES ─────────────────────────────────────────────────────────────────
SOUTHERN_EU = {
    "ES": "España",
    "PT": "Portugal",
    "IT": "Italia",
    "EL": "Grecia",    # Eurostat usa EL, no GR
    "HR": "Croacia",
    "SI": "Eslovenia",
    "MT": "Malta",
    "CY": "Chipre",
}

# Corrección Eurostat → ISO-2 estándar (solo Grecia lo necesita)
ISO_FIX = {"EL": "GR"}

SECTORS = {
    "TOTAL": "Total I+D",
    "BES":   "Sector empresarial",
    "GOV":   "Gobierno",
    "HES":   "Educación superior",
    "PNP":   "Privado sin ánimo de lucro",
}

# ISO-3 completo (cubre tanto EL como GR para robustez)
ISO3_MAP = {
    "ES": "ESP", "PT": "PRT", "IT": "ITA",
    "EL": "GRC", "GR": "GRC", "HR": "HRV",
    "SI": "SVN", "MT": "MLT", "CY": "CYP",
}

YEARS = list(range(2015, 2025))

# ── CARGA Y PROCESAMIENTO ──────────────────────────────────────────────────────
@st.cache_data(show_spinner="Procesando datos…")
def load_and_process(path: str) -> pd.DataFrame:
    """
    Lee el CSV de Eurostat (RD_P_PERSSCI) y calcula el % de mujeres
    dividiendo Headcount femenino entre el total.

    Filtros aplicados internamente:
      - unit     = HC   (Headcount — conteo real de personas)
      - prof_pos = TOTAL (todo el personal I+D, no solo investigadores)
      - ford     = TOTAL (sin desglose por campo científico)
      - geo      = Países de Europa del Sur
      - year     = 2015–2024
    """
    raw = pd.read_csv(path)

    mask = (
        raw["geo"].isin(SOUTHERN_EU.keys()) &
        raw["TIME_PERIOD"].between(2015, 2024) &
        (raw["ford"]     == "TOTAL") &
        (raw["prof_pos"] == "TOTAL") &
        (raw["unit"]     == "HC")
    )
    df = raw[mask].copy()

    females = (
        df[df["sex"] == "F"][["geo", "TIME_PERIOD", "sectperf", "OBS_VALUE"]]
        .rename(columns={"OBS_VALUE": "females"})
    )
    total = (
        df[df["sex"] == "T"][["geo", "TIME_PERIOD", "sectperf", "OBS_VALUE"]]
        .rename(columns={"OBS_VALUE": "total"})
    )

    merged = pd.merge(females, total, on=["geo", "TIME_PERIOD", "sectperf"])
    merged["pct_women"]    = (merged["females"] / merged["total"] * 100).round(1)
    merged["country"]      = merged["geo"].map(SOUTHERN_EU)
    merged["sector_label"] = merged["sectperf"].map(SECTORS)
    merged["iso2"]         = merged["geo"].replace(ISO_FIX)
    merged["iso3"]         = merged["geo"].map(ISO3_MAP)
    merged                 = merged.rename(columns={"TIME_PERIOD": "year"})

    return merged.dropna(subset=["pct_women"])


# ── COMPROBACIÓN DEL ARCHIVO ───────────────────────────────────────────────────
if not os.path.exists(CSV_PATH):
    st.markdown('<p class="main-title">🔬 Mujeres en I+D · Europa del Sur</p>', unsafe_allow_html=True)
    st.error(
        f"❌ No se encontró el archivo CSV en la ruta: `{CSV_PATH}`\n\n"
        "Edita la variable **CSV_PATH** al inicio de `app.py` con la ruta correcta."
    )
    st.markdown("""
    <div class="note-box">
        <b>Ejemplos de rutas válidas:</b><br>
        • Misma carpeta que app.py: <code>CSV_PATH = "rd_p_perssci.csv"</code><br>
        • Windows: <code>CSV_PATH = r"C:\\Users\\TuNombre\\Descargas\\rd_p_perssci.csv"</code><br>
        • Linux/Mac: <code>CSV_PATH = "/home/usuario/datos/rd_p_perssci.csv"</code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = load_and_process(CSV_PATH)

# ── SIDEBAR (solo filtros, sin uploader) ───────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filtros")

    paises_sel = st.multiselect(
        "🌍 Países",
        options=list(SOUTHERN_EU.values()),
        default=list(SOUTHERN_EU.values()),
    )

    year_range = st.slider(
        "📅 Años",
        min_value=YEARS[0],
        max_value=YEARS[-1],
        value=(YEARS[0], YEARS[-1]),
    )

    sectores_sel = st.multiselect(
        "🏭 Sector",
        options=list(SECTORS.values()),
        default=["Total I+D"],
    )

    st.markdown("---")
    st.caption(
        "**Fuente:** Eurostat · RD_P_PERSSCI  \n"
        "**Unidad:** Headcount (HC)  \n"
        "**Cálculo:** % = mujeres / total personal I+D × 100  \n"
        "**Filtros internos:** prof_pos=TOTAL, ford=TOTAL"
    )

# ── FILTRADO ───────────────────────────────────────────────────────────────────
mask = (
    df["country"].isin(paises_sel) &
    df["year"].between(*year_range) &
    df["sector_label"].isin(sectores_sel)
)
dff = df[mask].copy()

if dff.empty:
    st.warning("⚠️ No hay datos disponibles para la selección actual. Prueba con otros filtros.")
    st.stop()

# ── CABECERA ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🔬 Mujeres en I+D · Europa del Sur</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="subtitle">% de mujeres sobre el total de personal de I+D · '
    f'Unidad: Headcount · {year_range[0]}–{year_range[1]} · '
    f'{len(paises_sel)} países · {", ".join(sectores_sel)}</p>',
    unsafe_allow_html=True
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

def kpi(col, label, value):
    col.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(k1, "Media global (%)",    f"{dff['pct_women'].mean():.1f}")
kpi(k2, "Máximo (%)",          f"{dff['pct_women'].max():.1f}")
kpi(k3, "Mínimo (%)",          f"{dff['pct_women'].min():.1f}")
kpi(k4, "Registros totales",   str(len(dff)))

st.markdown("<br>", unsafe_allow_html=True)

# ── MAPA COROPLÉTICO ───────────────────────────────────────────────────────────
st.subheader("🗺️ Mapa — Media del período seleccionado")

map_df = dff.groupby(["iso3", "country"], as_index=False)["pct_women"].mean().round(1)

fig_map = px.choropleth(
    map_df,
    locations="iso3",
    locationmode="ISO-3",
    color="pct_women",
    hover_name="country",
    hover_data={"pct_women": ":.1f", "iso3": False},
    color_continuous_scale="RdYlGn",
    range_color=[20, 65],
    labels={"pct_women": "% mujeres"},
    scope="europe",
)
fig_map.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=0),
    height=450,
    coloraxis_colorbar=dict(
        title="% mujeres",
        thickness=14,
        len=0.6,
    ),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="#444",
        bgcolor="rgba(0,0,0,0)",
        showland=True,
        landcolor="#1a1a2e",
        showocean=True,
        oceancolor="#0d0d1a",
        projection_type="mercator",
        center=dict(lat=41, lon=14),
        projection_scale=3.2,
    ),
)
st.plotly_chart(fig_map, use_container_width=True)

# ── EVOLUCIÓN TEMPORAL ─────────────────────────────────────────────────────────
st.subheader("📈 Evolución anual por país")

line_df = dff.groupby(["year", "country"], as_index=False)["pct_women"].mean().round(1)

fig_line = px.line(
    line_df,
    x="year", y="pct_women", color="country",
    markers=True,
    labels={"pct_women": "% mujeres", "year": "Año", "country": "País"},
    color_discrete_sequence=px.colors.qualitative.Vivid,
)
fig_line.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(range=[0, 75], gridcolor="#2a2a4a", title="% mujeres"),
    xaxis=dict(dtick=1, gridcolor="#2a2a4a"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="x unified",
)
fig_line.update_traces(line_width=2.5, marker_size=7)
st.plotly_chart(fig_line, use_container_width=True)

# ── COMPARATIVA POR SECTOR ─────────────────────────────────────────────────────
if len(sectores_sel) > 1:
    st.subheader("🏭 Comparativa por sector y país")

    bar_df = dff.groupby(["country", "sector_label"], as_index=False)["pct_women"].mean().round(1)

    fig_bar = px.bar(
        bar_df,
        x="country", y="pct_women", color="sector_label",
        barmode="group",
        labels={"pct_women": "% mujeres", "country": "País", "sector_label": "Sector"},
        color_discrete_sequence=px.colors.qualitative.Vivid,
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#2a2a4a"),
        xaxis=dict(gridcolor="#2a2a4a"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── TABLA ──────────────────────────────────────────────────────────────────────
with st.expander("📋 Ver tabla de datos completa"):
    display_df = (
        dff[["country", "year", "sector_label", "females", "total", "pct_women"]]
        .rename(columns={
            "country":      "País",
            "year":         "Año",
            "sector_label": "Sector",
            "females":      "Mujeres (HC)",
            "total":        "Total (HC)",
            "pct_women":    "% Mujeres",
        })
        .sort_values(["País", "Año"])
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.download_button(
        label="⬇️ Descargar CSV procesado",
        data=display_df.to_csv(index=False).encode("utf-8"),
        file_name="mujeres_ID_europa_sur.csv",
        mime="text/csv",
    )

    #Nota para ejecutar el app py streamlit : streamlit run "/Users/melisaespinosarivera/Desktop/Mapa visualizacion Europa del Sur.py"