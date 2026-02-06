import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Obra Pro", layout="wide")

st.title("🏗️ Control de Gastos por Etapas")

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
    
    # Etapa de Obra (Por defecto Cimentación)
    etapa_opciones = ["Cimentación", "Estructura", "Instalaciones", "Acabados", "Exteriores"]
    etapa_sel = st.selectbox("ETAPA DE OBRA", etapa_opciones, index=0)
    
    # Categoría (Agregada: Permisos)
    cat_opciones = ["Mano de Obra", "Materiales", "Permisos", "Fletes", "Otros"]
    categoria_sel = st.selectbox("CATEGORÍA", cat_opciones)
    
    if categoria_sel == "Otros":
        categoria_final = st.text_input("Especificar categoría:", placeholder="Ej: Herramienta")
    else:
        categoria_final = categoria_sel

    concepto = st.text_input("CONCEPTO", placeholder="Ej: Pago a cuadrilla, Licencia municipal...")
    
    # Monto con valor por defecto de 400 para Mano de Obra
    monto_default = "400" if categoria_sel == "Mano de Obra" else ""
    monto_txt = st.text_input("MONTO ($)", value=monto_default)
    
    def limpiar_monto(val):
        try: return float(val.replace(',', ''))
        except: return 0.0

    monto = limpiar_monto(monto_txt)
    fecha_gasto = st.date_input("FECHA", datetime.now())
    
    btn_guardar = st.button("GUARDAR GASTO ✅", use_container_width=True, type="primary")

    st.divider()
    st.header("🗑️ Eliminar Registro")
    if not df_obra.empty:
        opciones_borrar = [f"{i} - {df_obra.loc[i, 'CONCEPTO']}" for i in reversed(df_obra.index)]
        seleccion_borrar = st.selectbox("Selecciona para borrar:", opciones_borrar)
        
        if st.button("ELIMINAR SELECCIONADO ❌", use_container_width=True):
            st.session_state.confirmar_borrado_obra = True

        if st.session_state.get('confirmar_borrado_obra', False):
            st.warning("¿Confirmas la eliminación?")
            c1, c2 = st.columns(2)
            if c1.button("SÍ, BORRAR"):
                id_a_borrar = int(seleccion_borrar.split(" - ")[0])
                conn.update(data=df_obra.drop(id_a_borrar))
                st.session_state.confirmar_borrado_obra = False
                st.cache_data.clear()
                st.rerun()
            if c2.button("NO"):
                st.session_state.confirmar_borrado_obra = False
                st.rerun()

# --- ACCIÓN DE GUARDADO ---
if btn_guardar and concepto and monto > 0:
    nuevo = pd.DataFrame([{
        "FECHA_REGISTRO": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "CONCEPTO": concepto,
        "CATEGORIA": categoria_final if categoria_final else "Otros",
        "ETAPA": etapa_sel,
        "MONTO": monto,
        "FECHA_GASTO": fecha_gasto.strftime("%d/%m/%Y")
    }])
    
    conn.update(data=pd.concat([df_obra, nuevo], ignore_index=True))
    st.cache_data.clear()
    st.rerun()

# --- REPORTES Y TABLA ---
if not df_obra.empty:
    df_obra['FECHA_GASTO_DT'] = pd.to_datetime(df_obra['FECHA_GASTO'], format="%d/%m/%Y")
    hoy = datetime.now()
    
    st.subheader("📊 Resumen de Gastos")
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Acumulado", f"${df_obra['MONTO'].sum():,.2f}")
    
    # Gasto de la semana
    inicio_sem = hoy - timedelta(days=hoy.weekday())
    g_sem = df_obra[df_obra['FECHA_GASTO_DT'] >= inicio_sem]['MONTO'].sum()
    t2.metric("Esta Semana", f"${g_sem:,.2f}")
    
    # Gasto por Etapa seleccionada
    etapa_filtro = st.selectbox("Ver total por Etapa:", ["Todas"] + etapa_opciones)
    if etapa_filtro != "Todas":
        total_etapa = df_obra[df_obra['ETAPA'] == etapa_filtro]['MONTO'].sum()
        st.info(f"Gasto total en **{etapa_filtro}**: ${total_etapa:,.2f}")

    st.divider()
    
    st.subheader("📋 Historial de Obra")
    # Mostrar la tabla con la nueva columna de ETAPA
    st.dataframe(
        df_obra.sort_index(ascending=False)[["FECHA_GASTO", "ETAPA", "CONCEPTO", "CATEGORIA", "MONTO"]],
        use_container_width=True
    )
else:
    st.info("Registra tu primer gasto para ver el historial.")