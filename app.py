
# Este archivo usa Streamlit y debe ejecutarse localmente.
# Ejecuta en tu terminal: pip install -r requirements.txt
# Luego corre: streamlit run app.py

import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Dashboard Mantenimiento Correctivo", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .centered-image { display: flex; justify-content: center; margin-top: -40px; }
        .login-box {
            background-color: #ffffffdd; padding: 2rem; border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🔐 Acceso al Dashboard de Mantenimiento Correctivo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Por favor, inicia sesión para continuar.</p>", unsafe_allow_html=True)

    with st.form("login"):
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        usuario = st.text_input("Usuario")
        contraseña = st.text_input("Contraseña", type="password")
        acceso = st.form_submit_button("Ingresar")
        st.markdown('</div>', unsafe_allow_html=True)

        if acceso:
            if usuario == "admin" and contraseña == "1234":
                st.session_state.authenticated = True
                st.success("Bienvenido, acceso concedido.")
                st.rerun()
            else:
                st.error("Credenciales inválidas. Intenta de nuevo.")

else:
    st.title("🔧 Dashboard de Mantenimiento Correctivo 2025")
    archivo = st.file_uploader("Sube tu archivo Excel", type=[".xlsx"])

    if archivo:
        df = pd.read_excel(archivo)
        df.columns = df.columns.str.strip().str.upper()
        df["FECHA DE CREACIÓN"] = pd.to_datetime(df.get("FECHA DE CREACIÓN"), errors="coerce")
        df["IMPORTE"] = pd.to_numeric(df.get("IMPORTE"), errors="coerce")

        st.sidebar.header("Filtros")
        tipo_orden_opts = df["TIPO DE ORDEN"].dropna().unique().tolist() if "TIPO DE ORDEN" in df.columns else []
        default_tipo_orden = ["CORRECTIVO"] if "CORRECTIVO" in tipo_orden_opts else []
        tipo_orden = st.sidebar.multiselect("Tipo de orden", tipo_orden_opts, default=default_tipo_orden)

        anios_disponibles = df["FECHA DE CREACIÓN"].dt.year.dropna().unique()
        anio = st.sidebar.selectbox("Año", sorted(anios_disponibles, reverse=True))
        meses = st.sidebar.multiselect("Mes(es)", list(range(1, 13)), default=[datetime.now().month])
        proveedores = st.sidebar.multiselect("Proveedor", df["PROVEEDOR"].dropna().unique())
        estatus_usuario = st.sidebar.multiselect("Estatus de Usuario", df["ESTATUS DE USUARIO"].dropna().unique())

        df_filtrado = df.copy()
        if tipo_orden:
            df_filtrado = df_filtrado[df_filtrado["TIPO DE ORDEN"].isin(tipo_orden)]
        df_filtrado = df_filtrado[(df_filtrado["FECHA DE CREACIÓN"].dt.year == anio) & (df_filtrado["FECHA DE CREACIÓN"].dt.month.isin(meses))]
        if proveedores:
            df_filtrado = df_filtrado[df_filtrado["PROVEEDOR"].isin(proveedores)]
        if estatus_usuario:
            df_filtrado = df_filtrado[df_filtrado["ESTATUS DE USUARIO"].isin(estatus_usuario)]

        if df_filtrado.empty:
            st.warning("⚠️ No hay datos disponibles con los filtros seleccionados.")
        else:
            st.subheader("📌 KPIs del Mes")
            total_ordenes = df_filtrado.shape[0]
            total_importe = df_filtrado["IMPORTE"].sum()
            proveedor_top = df_filtrado["PROVEEDOR"].value_counts().idxmax()
            ordenes_prom = total_ordenes / df_filtrado["PROVEEDOR"].nunique()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🗂 Total de Órdenes", f"{total_ordenes:,}")
            col2.metric("💰 Importe Total", f"${total_importe:,.0f}")
            col3.metric("🥇 Proveedor con Más Órdenes", proveedor_top)
            col4.metric("📊 Órdenes Promedio", f"{ordenes_prom:.2f}")
