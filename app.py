# app.py
# Ejecuta: pip install streamlit pandas plotly openpyxl xlsxwriter
# Luego: streamlit run app.py

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
        tipo_orden = st.sidebar.multiselect("Tipo de orden", tipo_orden_opts, default=["CORRECTIVO"] if "CORRECTIVO" in tipo_orden_opts else [])
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
            tabs = st.tabs(["📊 Indicadores y Tablas", "📋 Detalle por Proveedor", "📈 Visualizaciones", "🎯 Metas y Cumplimiento"])

            with tabs[0]:
                st.subheader("📌 Indicadores clave del mes")
                total_ordenes = df_filtrado.shape[0]
                total_importe = df_filtrado["IMPORTE"].sum()
                proveedor_top = df_filtrado["PROVEEDOR"].value_counts().idxmax()
                ordenes_prom = total_ordenes / df_filtrado["PROVEEDOR"].nunique()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🗂 Total de Órdenes", f"{total_ordenes:,}")
                col2.metric("💰 Importe Total", f"${total_importe:,.0f}")
                col3.metric("🥇 Proveedor con Más Órdenes", proveedor_top)
                col4.metric("📊 Órdenes Promedio", f"{ordenes_prom:.2f}")

                st.subheader("📊 Tabla de Recuento por Proveedor y Estatus")

                # Construye la tabla de recuento (pivot)
                tabla_ordenes = pd.pivot_table(
                    df_filtrado,
                    index="PROVEEDOR",
                    columns="ESTATUS DE USUARIO",
                    values="ORDEN",
                    aggfunc="count",
                    fill_value=0
                )

                tabla_ordenes["TOTAL_ORDENES"] = tabla_ordenes.sum(axis=1)
                fila_total = pd.DataFrame(tabla_ordenes.sum(numeric_only=True)).T
                fila_total.index = ["TOTAL GENERAL"]
                tabla_ordenes = pd.concat([tabla_ordenes, fila_total])

                # Calcula y agrega el porcentaje enseguida de cada estatus
                cols = []
                for col in tabla_ordenes.columns:
                    if col == "TOTAL_ORDENES":
                        continue
                    tabla_ordenes[f"% {col}"] = (tabla_ordenes[col] / tabla_ordenes["TOTAL_ORDENES"] * 100).round(2)
                for col in tabla_ordenes.columns:
                    if col.startswith('% '):
                        continue
                    cols.append(col)
                    if f"% {col}" in tabla_ordenes.columns:
                        cols.append(f"% {col}")
                cols.append("TOTAL_ORDENES")
                tabla_ordenes = tabla_ordenes[cols]

                # Muestra tabla en Streamlit
                st.dataframe(
                    tabla_ordenes.style
                        .format("{:.2f}")
                        .apply(lambda x: ["background-color: #dbeafe; font-weight: bold" if x.name == "TOTAL GENERAL" else "" for _ in x], axis=1)
                )

                # Exporta la tabla a Excel (igualita con porcentajes)
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    tabla_ordenes.to_excel(writer, sheet_name="Recuento Ordenes")
                    df_filtrado.to_excel(writer, sheet_name="Detalle", index=False)
                st.download_button(
                    "📤 Descargar tabla de recuento (Excel)",
                    data=buffer.getvalue(),
                    file_name="tabla_recuento_con_porcentajes.xlsx",
                    mime="application/vnd.ms-excel"
                )

# ---- Detalle por proveedor
            with tabs[1]:
                st.subheader("📋 Detalle completo de Órdenes")
                st.dataframe(df_filtrado)

            # ---- Visualizaciones
            with tabs[2]:
                st.subheader("📈 Órdenes por Estatus")
                grafico1 = df_filtrado["ESTATUS DE USUARIO"].value_counts().reset_index()
                grafico1.columns = ["Estatus", "Cantidad"]
                fig = px.bar(
                    grafico1,
                    x="Estatus",
                    y="Cantidad",
                    title="Órdenes por Estatus",
                    color="Cantidad",
                    text="Cantidad",
                    labels={"Cantidad": "Cantidad de Órdenes"}
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("💸 Importe por Proveedor")
                grafico2 = df_filtrado.groupby("PROVEEDOR")["IMPORTE"].sum().reset_index().sort_values(by="IMPORTE", ascending=False)
                grafico2["IMPORTE"] = grafico2["IMPORTE"].round(2)
                fig2 = px.bar(
                    grafico2,
                    x="PROVEEDOR",
                    y="IMPORTE",
                    title="Importe Total por Proveedor",
                    text=grafico2["IMPORTE"].apply(lambda x: f"${x:,.0f}"),
                    labels={"IMPORTE": "Importe ($MXN)"},
                    color="IMPORTE"
                )
                st.plotly_chart(fig2, use_container_width=True)

                st.subheader("📅 Tendencia de creación de órdenes por mes")
                df_filtrado["MES"] = df_filtrado["FECHA DE CREACIÓN"].dt.month
                df_filtrado["AÑO"] = df_filtrado["FECHA DE CREACIÓN"].dt.year
                tendencia = df_filtrado.groupby(["AÑO", "MES"]).size().reset_index(name="FOLIOS")
                fig3 = px.line(
                    tendencia,
                    x="MES",
                    y="FOLIOS",
                    color="AÑO",
                    markers=True,
                    title="Tendencia de creación de órdenes por mes",
                    labels={"MES": "Mes", "FOLIOS": "Cantidad de Órdenes", "AÑO": "Año"}
                )
                fig3.update_traces(
                    text=tendencia["FOLIOS"],
                    textposition="top center",
                    mode="lines+markers+text"
                )
                fig3.update_layout(xaxis=dict(tickmode="linear"))
                st.plotly_chart(fig3, use_container_width=True)
                
                st.subheader("📆 Tendencia diaria de creación de órdenes")
                df_filtrado["DIA"] = df_filtrado["FECHA DE CREACIÓN"].dt.date
                tendencia_dia = df_filtrado.groupby("DIA").size().reset_index(name="FOLIOS")

                fig_dia = px.line(
                    tendencia_dia,
                    x="DIA",
                    y="FOLIOS",
                    markers=True,
                    title="Tendencia diaria de creación de órdenes",
                    labels={"DIA": "Fecha", "FOLIOS": "Cantidad de Órdenes"}
                )

                fig_dia.update_traces(
                    text=tendencia_dia["FOLIOS"],
                    textposition="top center",
                    mode="lines+markers+text"
                )

                fig_dia.update_layout(
                    xaxis=dict(tickformat="%d-%b"),
                    hovermode="x unified"
                )

                st.plotly_chart(fig_dia, use_container_width=True)

            # ---- Análisis financiero PEP
            with tabs[3]:
                st.markdown("### 💲 KPIs Financieros")
                presupuesto_mensual = 4_000_000
                total_gastado = df_filtrado["IMPORTE"].sum()
                porcentaje_utilizado = (total_gastado / presupuesto_mensual) * 100 if presupuesto_mensual > 0 else 0
                pep_mas_costoso = (
                    df_filtrado.groupby("ELEMENTO PEP")["IMPORTE"].sum().idxmax()
                    if "ELEMENTO PEP" in df_filtrado.columns and not df_filtrado.empty else ""
                )
                ubicacion_mayor_gasto = (
                    df_filtrado.groupby("DENOMINACIÓN DE LA UBICACIÓN TÉCNICA")["IMPORTE"].sum().idxmax()
                    if "DENOMINACIÓN DE LA UBICACIÓN TÉCNICA" in df_filtrado.columns and not df_filtrado.empty else ""
                )

                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("💸 Total gastado", f"${total_gastado:,.0f}")
                kpi2.metric("📊 % presupuesto usado", f"{porcentaje_utilizado:.1f}%")
                kpi3.metric("🏆 Elemento PEP más costoso", f"{pep_mas_costoso}")
                kpi4.metric("🔍 Ubicación técnica con mayor gasto", f"{ubicacion_mayor_gasto}")

                if porcentaje_utilizado > 100:
                    st.error("🚨 ¡Se ha excedido el presupuesto mensual!")
                else:
                    st.success("Presupuesto dentro del límite. ¡Buen trabajo!")

                st.markdown("---")
                st.subheader("Órdenes por Elemento PEP")
                if "ELEMENTO PEP" in df_filtrado.columns:
                    ordenes_pep = df_filtrado["ELEMENTO PEP"].value_counts().reset_index()
                    ordenes_pep.columns = ["Elemento PEP", "Cantidad de Órdenes"]
                    fig_ordenes = px.bar(
                        ordenes_pep,
                        x="Elemento PEP",
                        y="Cantidad de Órdenes",
                        text="Cantidad de Órdenes",
                        color="Cantidad de Órdenes",
                        title="Órdenes por Elemento PEP"
                    )
                    fig_ordenes.update_traces(textposition="outside")
                    fig_ordenes.update_layout(xaxis_title="Elemento PEP", yaxis_title="Órdenes", showlegend=False)
                    st.plotly_chart(fig_ordenes, use_container_width=True)

                st.markdown("---")
                st.subheader("Importe acumulado por Elemento PEP")
                if "ELEMENTO PEP" in df_filtrado.columns:
                    importes_pep = df_filtrado.groupby("ELEMENTO PEP")["IMPORTE"].sum().reset_index().sort_values(by="IMPORTE", ascending=False)
                    importes_pep["IMPORTE"] = importes_pep["IMPORTE"].round(2)
                    fig_importes = px.bar(
                        importes_pep,
                        x="ELEMENTO PEP",
                        y="IMPORTE",
                        text=importes_pep["IMPORTE"].apply(lambda x: f"${x:,.0f}"),
                        color="IMPORTE",
                        title="Importe acumulado por Elemento PEP"
                    )
                    fig_importes.update_traces(textposition="outside")
                    fig_importes.update_layout(xaxis_title="Elemento PEP", yaxis_title="Importe ($MXN)", showlegend=False)
                    st.plotly_chart(fig_importes, use_container_width=True)

                st.markdown("---")
                st.markdown("#### Top ubicaciones técnicas por gasto (alerta si alguna excede el presupuesto mensual)")
                if "DENOMINACIÓN DE LA UBICACIÓN TÉCNICA" in df_filtrado.columns:
                    ubic_gasto = df_filtrado.groupby("DENOMINACIÓN DE LA UBICACIÓN TÉCNICA")["IMPORTE"].sum().reset_index()
                    ubic_gasto["status"] = ubic_gasto["IMPORTE"].apply(lambda x: "🔥 Excedido" if x > presupuesto_mensual else "✅ OK")
                    st.dataframe(ubic_gasto.sort_values(by="IMPORTE", ascending=False).round(2), use_container_width=True)

            # ---- Metas y cumplimiento
            with tabs[4]:
                st.subheader("🎯 Evaluación de cumplimiento por estatus de usuario")
                if "ESTATUS DE USUARIO" in df_filtrado.columns and not df_filtrado.empty:
                    tabla_estatus = df_filtrado.groupby(["PROVEEDOR", "ESTATUS DE USUARIO"]).agg(FOLIOS=("ORDEN", "count")).reset_index()
                    total_por_proveedor = tabla_estatus.groupby("PROVEEDOR")["FOLIOS"].sum().reset_index(name="TOTAL")
                    tabla_estatus = pd.merge(tabla_estatus, total_por_proveedor, on="PROVEEDOR")
                    pivot = tabla_estatus.pivot(index="PROVEEDOR", columns="ESTATUS DE USUARIO", values="FOLIOS").fillna(0)
                    pivot["TOTAL"] = pivot.sum(axis=1)
                    for col in ["ATEN", "VISA", "AUTO"]:
                        if col in pivot.columns:
                            pivot[f"% {col}"] = (pivot[col] / pivot["TOTAL"]) * 100
                        else:
                            pivot[f"% {col}"] = 0
                    pivot["% Visa+Auto"] = pivot.get("% VISA", 0) + pivot.get("% AUTO", 0)
                    pivot["Cumple Meta"] = (pivot.get("% ATEN", 0) <= 15) & (pivot["% Visa+Auto"] >= 85)
                    pivot["Cumple Meta"] = pivot["Cumple Meta"].apply(lambda x: "✅" if x else "❌")
                    columnas_porcentaje = [c for c in pivot.columns if "%" in c]
                    pivot[columnas_porcentaje] = pivot[columnas_porcentaje].round(2)
                    st.dataframe(pivot[[*columnas_porcentaje, "Cumple Meta"]])
                else:
                    st.warning("No se encontraron datos suficientes o la columna 'ESTATUS DE USUARIO' no está disponible.")
