import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Obra", layout="wide")

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

# --- SIDEBAR: REGISTRO ---
with st.sidebar:
    st.header("📝 Nuevo Gasto")
    
    # Selección de categoría primero para ajustar el monto
    cat_opciones = ["Mano de Obra", "Materiales", "Fletes", "Otros"]
    categoria_sel = st.selectbox("CATEGORÍA", cat_opciones)
    
    # Si es "Otros", habilitar campo de texto
    if categoria_sel == "Otros":
        categoria_final = st.text_input("¿Qué tipo de gasto es?", placeholder="Ej: Trámites")
    else:
        categoria_final = categoria_sel

    concepto = st.text_input("CONCEPTO", placeholder="Ej: Pago albañil Juan")
    
    # Monto por defecto basado en la selección
    monto_default = "400" if categoria_sel == "Mano de Obra" else ""
    monto_txt = st.text_input("MONTO ($)", value=monto_default, placeholder="Solo números")
    
    def limpiar_monto(val):
        try: return float(val.replace(',', ''))
        except: return 0.0

    monto = limpiar_monto(monto_txt)
    fecha_gasto = st.date_input("FECHA", datetime.now())
    
    btn_guardar = st.button("GUARDAR GASTO ✅", use_container_width=True, type="primary")

    st.divider()
    st.header("🗑️ Eliminar Registro")
    if not df_obra.empty:
        # Lista de opciones para borrar (ID + Concepto)
        opciones_borrar = [f"{i} - {df_obra.loc[i, 'CONCEPTO']}" for i in reversed(df_obra.index)]
        seleccion_borrar = st.selectbox("Selecciona para borrar:", opciones_borrar)
        
        if st.button("ELIMINAR SELECCIONADO ❌", use_container_width=True):
            st.session_state.confirmar_borrado = True

        if st.session_state.get('confirmar_borar_obra', False) or st.session_state.get('confirmar_borrado', False):
            st.warning("¿Estás seguro?")
            c1, c2 = st.columns(2)
            if c1.button("SÍ, BORRAR", type="primary"):
                id_a_borrar = int(seleccion_borrar.split(" - ")[0])
                df_nuevo = df_obra.drop(id_a_borrar)
                conn.update(data=df_nuevo)
                st.session_state.confirmar_borrado = False
                st.cache_data.clear()
                st.rerun()
            if c2.button("NO"):
                st.session_state.confirmar_borrado = False
                st.rerun()

# --- ACCIÓN DE GUARDADO ---
if btn_guardar and concepto and monto > 0:
    nuevo = pd.DataFrame([{
        "FECHA_REGISTRO": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "CONCEPTO": concepto,
        "CATEGORIA": categoria_final if categoria_final else "Otros",
        "MONTO": monto,
        "FECHA_GASTO": fecha_gasto.strftime("%d/%m/%Y")
    }])
    
    conn.update(data=pd.concat([df_obra, nuevo], ignore_index=True))
    st.cache_data.clear()
    st.rerun()

# --- REPORTES ---
if not df_obra.empty:
    df_obra['FECHA_GASTO_DT'] = pd.to_datetime(df_obra['FECHA_GASTO'], format="%d/%m/%Y")
    hoy = datetime.now()
    
    st.subheader("📊 Resumen de Gastos")
    t1, t2, t3 = st.columns(3)
    
    # Gasto Total
    t1.metric("Total Acumulado", f"${df_obra['MONTO'].sum():,.2f}")
    
    # Gasto de esta Semana
    inicio_sem = hoy - timedelta(days=hoy.weekday())
    g_sem = df_obra[df_obra['FECHA_GASTO_DT'] >= inicio_sem]['MONTO'].sum()
    t2.metric("Esta Semana", f"${g_sem:,.2f}")
    
    # Gasto de este Mes
    g_mes = df_obra[df_obra['FECHA_GASTO_DT'].dt.month == hoy.month]['MONTO'].sum()
    t3.metric(f"Mes ({hoy.strftime('%B')})", f"${g_mes:,.2f}")

    st.divider()
    
    # --- TABLA DE REGISTROS ---
    st.subheader("📋 Historial Completo")
    st.dataframe(
        df_obra.sort_index(ascending=False)[["FECHA_GASTO", "CONCEPTO", "CATEGORIA", "MONTO"]],
        use_container_width=True
    )
else:
    st.info("No hay gastos registrados. Usa el panel de la izquierda para comenzar.")