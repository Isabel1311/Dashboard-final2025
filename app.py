import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# ---------------------- ESTILO GLOBAL ----------------------
st.set_page_config(page_title="Corte de Gestión", layout="wide")

st.markdown("""
    <style>
        body, .stApp {
            background-color: #f5f6fa !important;
        }
        .titulo-app {
            font-size: 2.7rem;
            font-weight: 900;
            color: #16213e;
            text-align: center;
            margin-top: 2rem;
        }
        .subtitulo-app {
            font-size: 1.2rem;
            font-weight: 500;
            color: #3a4750;
            text-align: center;
        }
        .kpi-card {
            border-radius: 18px !important;
            box-shadow: 0 4px 24px 0 rgba(30,34,90,.07);
            background: #fff;
            padding: 1.4rem 0.5rem 1.2rem 0.5rem;
            text-align: center;
            margin-bottom: 1.2rem;
        }
        .kpi-value {
            font-size: 2.4rem;
            font-weight: bold;
            margin: 0.4rem 0 0 0;
        }
        .kpi-label {
            font-size: 1.2rem;
            font-weight: 600;
            color: #3a4750;
        }
        .kpi-icon {
            font-size: 2.5rem;
            margin-bottom: 0.4rem;
        }
        .blue-row {
            background-color: #dbeafe !important;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------- SIDEBAR FILTROS Y CARGA -------------------
with st.sidebar:
    st.header("Filtros y Configuración")
    archivo = st.file_uploader("Carga tu archivo Excel", type=["xlsx"])
    proveedor = supervisor = estatus = dz = None
    fecha_inicio = fecha_fin = None

# ----------- INICIO DE APP (HEADER Y PORTADA) -------------
st.markdown("<div class='titulo-app'>Corte de Gestión</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitulo-app'>Gestión que transforma, datos que mandan.</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if not archivo:
    st.info("Por favor, sube tu archivo Excel para comenzar.")
    st.stop()

# ------------------- PROCESAMIENTO DE DATOS -------------------
df = pd.read_excel(archivo)
df.columns = df.columns.str.strip().str.upper()

if "FECHA DE CREACIÓN" in df.columns:
    df["FECHA DE CREACIÓN"] = pd.to_datetime(df["FECHA DE CREACIÓN"], errors="coerce")
if "IMPORTE" in df.columns:
    df["IMPORTE"] = pd.to_numeric(df["IMPORTE"], errors="coerce")

# ----------- SIDEBAR: DETECCIÓN Y OPCIONES DE FILTRO ----------
with st.sidebar:
    if "PROVEEDOR" in df.columns:
        proveedor = st.selectbox("Proveedor", options=["Todos"] + sorted(df["PROVEEDOR"].dropna().unique().tolist()))
    if "SUPERVISOR" in df.columns:
        supervisor = st.selectbox("Supervisor", options=["Todos"] + sorted(df["SUPERVISOR"].dropna().unique().tolist()))
    if "ESTATUS DE USUARIO" in df.columns:
        estatus = st.selectbox("Estatus", options=["Todos"] + sorted(df["ESTATUS DE USUARIO"].dropna().unique().tolist()))
    if "DZ" in df.columns:
        dz = st.selectbox("DZ", options=["Todos"] + sorted(df["DZ"].dropna().unique().tolist()))
    fechas = df["FECHA DE CREACIÓN"].dropna()
    if not fechas.empty:
        fecha_inicio = st.date_input("Fecha de entrada (inicio)", fechas.min().date())
        fecha_fin = st.date_input("Fecha de entrada (fin)", fechas.max().date())

# ------------- FILTRADO DE DATOS SEGÚN SELECCIÓN -------------
df_filtrado = df.copy()
if proveedor and proveedor != "Todos":
    df_filtrado = df_filtrado[df_filtrado["PROVEEDOR"] == proveedor]
if supervisor and supervisor != "Todos":
    df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"] == supervisor]
if estatus and estatus != "Todos":
    df_filtrado = df_filtrado[df_filtrado["ESTATUS DE USUARIO"] == estatus]
if dz and dz != "Todos":
    df_filtrado = df_filtrado[df_filtrado["DZ"] == dz]
if fecha_inicio and fecha_fin:
    df_filtrado = df_filtrado[(df_filtrado["FECHA DE CREACIÓN"] >= pd.Timestamp(fecha_inicio)) &
                             (df_filtrado["FECHA DE CREACIÓN"] <= pd.Timestamp(fecha_fin))]

# -------------------- KPI PRINCIPALES ARRIBA --------------------
total_ordenes = df_filtrado.shape[0]
en_tiempo = df_filtrado[df_filtrado["ESTATUS DE USUARIO"].str.lower().str.contains("en tiempo", na=False)].shape[0] if "ESTATUS DE USUARIO" in df_filtrado.columns else 0
fuera_tiempo = df_filtrado[df_filtrado["ESTATUS DE USUARIO"].str.lower().str.contains("fuera", na=False)].shape[0] if "ESTATUS DE USUARIO" in df_filtrado.columns else 0
sabatinas = df_filtrado[df_filtrado["ESTATUS DE USUARIO"].str.lower().str.contains("sabati", na=False)].shape[0] if "ESTATUS DE USUARIO" in df_filtrado.columns else 0

# Si tienes otra columna para "Sucursales", cámbiala aquí.
sucursales = df_filtrado["SUCURSAL"].nunique() if "SUCURSAL" in df_filtrado.columns else None

st.markdown("<br>", unsafe_allow_html=True)
kpi_cols = st.columns(5 if sucursales is not None else 4)
with kpi_cols[0]:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon'>📋</div><div class='kpi-label'>Total de Órdenes</div><div class='kpi-value'>{total_ordenes:,}</div></div>", unsafe_allow_html=True)
with kpi_cols[1]:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon'>⏱️</div><div class='kpi-label'>En Tiempo</div><div class='kpi-value' style='color: #188038'>{en_tiempo:,}</div></div>", unsafe_allow_html=True)
with kpi_cols[2]:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon'>⚠️</div><div class='kpi-label'>Fuera de Tiempo</div><div class='kpi-value' style='color: #b88b20'>{fuera_tiempo:,}</div></div>", unsafe_allow_html=True)
with kpi_cols[3]:
    st.markdown(f"<div class='kpi-card'><div class='kpi-icon'>📅</div><div class='kpi-label'>Sabatinas</div><div class='kpi-value' style='color: #a03131'>{sabatinas:,}</div></div>", unsafe_allow_html=True)
if sucursales is not None:
    with kpi_cols[4]:
        st.markdown(f"<div class='kpi-card'><div class='kpi-icon'>🏢</div><div class='kpi-label'>Sucursales</div><div class='kpi-value' style='color: #3053a0'>{sucursales:,}</div></div>", unsafe_allow_html=True)

# ------------------- TABLA GENERAL COMPARATIVA ------------------
st.markdown("<br><h3>📊 Panel Comparativo de Proveedores</h3>", unsafe_allow_html=True)

if "PROVEEDOR" in df_filtrado.columns:
    tabla = pd.pivot_table(
        df_filtrado,
        index="PROVEEDOR",
        columns="ESTATUS DE USUARIO",
        values="ORDEN" if "ORDEN" in df_filtrado.columns else df_filtrado.columns[0],
        aggfunc="count",
        fill_value=0
    )
    tabla["TOTAL_ORDENES"] = tabla.sum(axis=1)
    fila_total = pd.DataFrame(tabla.sum(numeric_only=True)).T
    fila_total.index = ["TOTAL GENERAL"]
    tabla = pd.concat([tabla, fila_total])

    # Porcentajes por estatus (solo columnas de estatus)
    estatus_cols = [col for col in tabla.columns if col != "TOTAL_ORDENES"]
    for col in estatus_cols:
        pct_col = f"% {col}"
        tabla[pct_col] = (tabla[col] / tabla["TOTAL_ORDENES"] * 100).round(2).astype(str) + "%"

    # Organiza columnas intercalando porcentajes
    cols_final = []
    for col in estatus_cols:
        cols_final += [col, f"% {col}"]
    cols_final.append("TOTAL_ORDENES")
    tabla = tabla[cols_final]

    def highlight_totals(row):
        return ['background-color: #dbeafe; font-weight: bold;' if row.name == 'TOTAL GENERAL' else '' for _ in row]

    st.dataframe(
        tabla.style.apply(highlight_totals, axis=1),
        use_container_width=True
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        tabla.to_excel(writer, sheet_name="Panel Proveedores")
        df_filtrado.to_excel(writer, sheet_name="Detalle", index=False)
    st.download_button(
        "📤 Descargar tabla de recuento (Excel)",
        data=buffer.getvalue(),
        file_name="panel_comparativo_proveedores.xlsx",
        mime="application/vnd.ms-excel"
    )
else:
    st.warning("No se encontró columna PROVEEDOR para generar el panel.")

# Puedes agregar más tablas, visualizaciones o análisis debajo según necesites
