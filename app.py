import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Gastos", layout="wide")

st.title("🏗️ Registro de Gastos de Construcción")

conn = st.connection("gsheets", type=GSheetsConnection)

def lectura_segura():
    for i in range(3):
        try: 
            df = conn.read(ttl=0)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except: time.sleep(1)
    return pd.DataFrame()

df_obra = lectura_segura()

# --- REGISTRO RÁPIDO ---
with st.sidebar:
    st.header("📝 Nuevo Gasto")
    concepto = st.text_input("CONCEPTO", placeholder="Ej: Pago albañil, Cemento, etc.")
    categoria = st.selectbox("CATEGORÍA", ["Mano de Obra", "Materiales", "Fletes", "Otros"])
    monto = st.number_input("MONTO ($)", min_value=0.0, step=100.0)
    fecha_gasto = st.date_input("FECHA", datetime.now())
    
    btn_guardar = st.button("GUARDAR GASTO ✅", use_container_width=True, type="primary")

# --- ACCIÓN DE GUARDADO ---
if btn_guardar and concepto and monto > 0:
    nuevo = pd.DataFrame([{
        "FECHA_REGISTRO": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "CONCEPTO": concepto,
        "CATEGORIA": categoria,
        "MONTO": monto,
        "FECHA_GASTO": fecha_gasto.strftime("%d/%m/%Y")
    }])
    
    conn.update(data=pd.concat([df_obra, nuevo], ignore_index=True))
    st.cache_data.clear()
    st.rerun()

# --- SECCIÓN DE REPORTES ---
if not df_obra.empty:
    # Convertir fechas para cálculos
    df_obra['FECHA_GASTO_DT'] = pd.to_datetime(df_obra['FECHA_GASTO'], format="%d/%m/%Y")
    hoy = datetime.now()
    
    st.subheader("📊 Resumen de Gastos")
    col_rep, col_vacia = st.columns([1, 2])
    
    tipo_reporte = col_rep.selectbox("Ver resumen por:", ["Gasto Total", "Esta Semana", "Este Mes", "Por Categoría"])

    if tipo_reporte == "Gasto Total":
        total = df_obra["MONTO"].sum()
        st.metric("Inversión Total", f"${total:,.2f}")

    elif tipo_reporte == "Esta Semana":
        inicio_sem = hoy - timedelta(days=hoy.weekday())
        gastos_sem = df_obra[df_obra['FECHA_GASTO_DT'] >= inicio_sem]
        st.metric("Gasto de la Semana", f"${gastos_sem['MONTO'].sum():,.2f}")

    elif tipo_reporte == "Este Mes":
        gastos_mes = df_obra[df_obra['FECHA_GASTO_DT'].dt.month == hoy.month]
        st.metric(f"Gasto de {hoy.strftime('%B')}", f"${gastos_mes['MONTO'].sum():,.2f}")

    elif tipo_reporte == "Por Categoría":
        st.write(df_obra.groupby("CATEGORIA")["MONTO"].sum().map("${:,.2f}".format))

    st.divider()
    
    # --- TABLA DE REGISTROS ---
    st.subheader("📋 Historial")
    st.dataframe(
        df_obra.sort_index(ascending=False)[["FECHA_GASTO", "CONCEPTO", "CATEGORIA", "MONTO"]],
        use_container_width=True
    )
    
    if st.button("🗑️ Borrar último registro"):
        if not df_obra.empty:
            conn.update(data=df_obra.drop(df_obra.index[-1]))
            st.cache_data.clear()
            st.rerun()
else:
    st.info("No hay gastos registrados aún.")
