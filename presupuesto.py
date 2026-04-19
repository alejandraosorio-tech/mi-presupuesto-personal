import pandas as pd
import streamlit as st
from datetime import date
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("Error al cargar la conexión de Google. Verifica el archivo requirements.txt")

st.set_page_config(page_title="Mi Presupuesto Quincenal", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# 1. Define tu link una sola vez aquí arriba
url_hoja = "https://docs.google.com/spreadsheets/d/1hwTThiotKRPqiDBEh5hvILvtEUkrdmnCIYoLnChFA7Y/edit?usp=sharing" 

# 2. Pásale el link a la conexión para que lo use siempre
conn = st.connection("gsheets", type=GSheetsConnection)

# --- MOTOR DE MEMORIA (CACHÉ) ---
# Esto guarda la "foto" por 10 minutos para que Google no nos bloquee
@st.cache_data(ttl=600)
def cargar_tabla(nombre_hoja, columnas_defecto):
    try:
        df = conn.read(spreadsheet= url_hoja , worksheet=nombre_hoja, ttl=0)
        if df.empty:
            return pd.DataFrame(columnas_defecto)
        return df
    except Exception:
        return pd.DataFrame(columnas_defecto)
# Estilo para los números
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 35px; color: #1E88E5; }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 Control Financiero Interactivo")

# --- 1. INGRESOS ---
st.header("1. Mis Ingresos")
col_ing1, col_ing2 = st.columns([1, 2])
with col_ing1:
    ingreso_base = st.number_input("Sueldo Base ($):", value=1313500, step=1000)
with col_ing2:
    st.write("Historial de Ingresos Extras:")
    df_extras_init = cargar_tabla("Extras_Actual", [{"Concepto": "Venta ropa", "Monto": 0}])
    edit_extras = st.data_editor(df_extras_init, num_rows="dynamic", use_container_width=True, key="extras")
    total_extras = edit_extras["Monto"].sum()

ingreso_total = ingreso_base + total_extras
st.metric("TOTAL INGRESOS", f"$ {ingreso_total:,.0f}")

st.divider()

# --- 2. EGRESOS FIJOS ---
st.header("2. Egresos Fijos")

df_fijos_init = cargar_tabla("Fijos_Actuales", [{"Fecha": date.today(), "Concepto": "Ejemplo", "Monto": 0, "Pagado": False}])

config_fijos = {
    "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$ %d")
}
# --- LIMPIEZA DE DATOS (Filtro anti-errores de Google Sheets) ---
# 1. Obligamos a que la columna 'Monto' sea numérica
if "Monto" in df_fijos_init.columns:
    df_fijos_init["Monto"] = pd.to_numeric(df_fijos_init["Monto"], errors="coerce").fillna(0)
    
# 2. Si tienes una columna de casillas (ej. 'Pagado', 'Listo', etc.), pon su nombre exacto aquí:
# Esto convierte los "TRUE" de Excel a casillas marcadas de Python
nombre_columna_checkbox = "Pagado" 
if nombre_columna_checkbox in df_fijos_init.columns:
    df_fijos_init[nombre_columna_checkbox] = df_fijos_init[nombre_columna_checkbox].astype(str).str.upper() == "TRUE"

# ----------------------------------------------------------------

# AQUÍ VA TU LÍNEA ORIGINAL:
edit_fijos = st.data_editor(df_fijos_init, num_rows="dynamic", use_container_width=True, column_config=config_fijos, key="fijos_table")

total_fijos_proyectado = edit_fijos["Monto"].sum()
gastado_fijos_real = edit_fijos[edit_fijos["Pagado"] == True]["Monto"].sum()
porcentaje_fijos = (total_fijos_proyectado / ingreso_total * 100) if ingreso_total > 0 else 0

c_f1, c_f2 = st.columns(2)
with c_f1:
    st.metric("Total Gastos Fijos (Proyectado)", f"$ {total_fijos_proyectado:,.0f}")
with c_f2:
    st.metric("Peso en mis Ingresos", f"{porcentaje_fijos:.1f}%")

presupuesto_base = ingreso_total - total_fijos_proyectado
st.info(f"💰 **Presupuesto restante para repartir:** ${presupuesto_base:,.0f}")

st.divider()

# --- 3. DISTRIBUCIÓN DE PRESUPUESTO ---
st.header("3. Distribución de Presupuesto")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1: p_ahorro = st.slider("% Ahorro", 0, 100, 42)
with col_p2: p_prog = st.slider("% Programados", 0, 100, 43)
with col_p3: p_noprog = st.slider("% No Programados", 0, 100, 15)

if (p_ahorro + p_prog + p_noprog) != 100:
    st.warning("⚠️ Los porcentajes no suman 100%.")

col_r1, col_r2, col_r3 = st.columns(3)

def crear_seccion_rubro(col, titulo, porcentaje, df_inicial, key_name):
    with col:
        asignado = presupuesto_base * (porcentaje / 100)
        st.subheader(f"{titulo}")
        st.write(f"Asignado: **${asignado:,.0f}**")
        config = {
            "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
            "Monto": st.column_config.NumberColumn("Monto ($)", format="$ %d")
        }
        edit_df = st.data_editor(df_inicial, num_rows="dynamic", use_container_width=True, column_config=config, key=key_name)
        gastado = edit_df[edit_df.iloc[:, -1] == True]["Monto"].sum()
        saldo = asignado - gastado
        st.metric(f"Saldo {titulo}", f"$ {saldo:,.0f}")
        return gastado, edit_df

df_ah_init = cargar_tabla("Ahorro_Actual", [{"Fecha": date.today(), "Concepto": "Ahorro", "Monto": 0, "Listo": False}])
df_pr_init = cargar_tabla("Prog_Actual", [{"Fecha": date.today(), "Concepto": "Láser", "Monto": 0, "Pagado": False}])
df_np_init = cargar_tabla("NoProg_Actual", [{"Fecha": date.today(), "Concepto": "Efectivo", "Monto": 0, "Hecho": False}])

g1, edit_ahorro = crear_seccion_rubro(col_r1, "Ahorro", p_ahorro, df_ah_init, "t_ahorro")
g2, edit_prog = crear_seccion_rubro(col_r2, "Programados", p_prog, df_pr_init, "t_prog")
g3, edit_noprog = crear_seccion_rubro(col_r3, "No Prog.", p_noprog, df_np_init, "t_noprog")

# --- 4. SALDO GLOBAL ---
st.divider()
total_pagado_real = gastado_fijos_real + g1 + g2 + g3
saldo_final_cuenta = ingreso_total - total_pagado_real
st.header("4. Saldo Real en Cuenta")
st.metric("Dinero que debería haber hoy:", f"$ {saldo_final_cuenta:,.0f}")

st.divider()

# --- 5. GUARDAR HISTORIAL ---
st.subheader("💾 Finalizar y Guardar Historial")
st.write("Presiona este botón cuando termines tu quincena.")

if st.button("Guardar en mi Historial de Google Sheets"):
    nueva_fila = pd.DataFrame([{
        "Fecha_Registro": date.today().strftime("%d/%m/%Y"),
        "Ingresos_Totales": float(ingreso_total),
        "Gastos_Fijos": float(gastado_fijos_real),
        "Ahorro_Realizado": float(g1), # Temporal, lo ajustaremos
        "Programados_Realizado": float(g2),
        "No_Programados_Realizado": float(g3),
        "Saldo_Final": float(saldo_final_cuenta)
    }])
    
    try:
        # 1. Guarda el histórico
        datos_existentes = conn.read(spreadsheet = url_hoja, worksheet="Historico", ttl=0)
        tabla_actualizada = pd.concat([datos_existentes, nueva_fila], ignore_index=True)
        conn.update(spreadsheet = url_hoja, worksheet="Historico", data=tabla_actualizada)
        
        # 2. Guarda las listas individuales en sus pestañas
        conn.update(spreadsheet= url_hoja, worksheet="Extras_Actual", data=edit_extras)
        conn.update(spreadsheet= url_hoja, worksheet="Fijos_Actuales", data=edit_fijos)
        conn.update(spreadsheet= url_hoja, worksheet="Ahorro_Actual", data=edit_ahorro)
        conn.update(spreadsheet= url_hoja, worksheet="Prog_Actual", data=edit_prog)
        conn.update(spreadsheet= url_hoja, worksheet="NoProg_Actual", data=edit_noprog)
        
        # 3. ¡EL TRUCO DE MAGIA! Borramos el caché para que lea lo nuevo
        st.cache_data.clear()
        
        st.success("✅ ¡Datos y listas guardadas con éxito en tu Google Sheets!")
        st.balloons()
        
    except Exception as e:
        st.error(f"Hubo un error al guardar: {e}")