import pandas as pd
import streamlit as st
from datetime import date

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("Error al cargar la conexión de Google.")

st.set_page_config(page_title="Mi Presupuesto Quincenal", layout="wide")

# --- 1. CONEXIÓN ---
url_hoja = "https://docs.google.com/spreadsheets/d/1hwTThiotKRPqiDBEh5hvILvtEUkrdmnCIYoLnChFA7Y/edit"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNCIONES DE MEMORIA (LEER DEL EXCEL) ---
def cargar_tabla(nombre_hoja, columnas_esperadas):
    try:
        df = conn.read(spreadsheet=url_hoja, worksheet=nombre_hoja, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=columnas_esperadas)
        return df
    except:
        return pd.DataFrame(columns=columnas_esperadas)

def cargar_valor_estado(columna, valor_defecto):
    try:
        df_est = conn.read(spreadsheet=url_hoja, worksheet="Estado_Actual", ttl=0)
        if not df_est.empty:
            return float(df_est.iloc[-1][columna])
        return float(valor_defecto)
    except:
        return float(valor_defecto)

# --- 3. CARGA INICIAL DE DATOS ---
# Esto hace que la app "recuerde" lo que hay en el Excel al abrirse
df_fijos_memoria = cargar_tabla("Fijos_Actuales", ["Fecha", "Concepto", "Monto", "Pagado"])
df_ahorro_memoria = cargar_tabla("Ahorro_Actual", ["Fecha", "Concepto", "Monto", "Listo"])
df_prog_memoria = cargar_tabla("Prog_Actual", ["Fecha", "Concepto", "Monto", "Pagado"])
df_noprog_memoria = cargar_tabla("NoProg_Actual", ["Fecha", "Concepto", "Monto", "Hecho"])

st.title("💸 Mi Presupuesto con Memoria Total")

# --- 4. SECCIÓN DE INGRESOS (ERROR ROJO CORREGIDO AQUÍ) ---
st.header("1. Mis Ingresos")
col_ing1, col_ing2 = st.columns([1, 2])
with col_ing1:
    # Usamos .0 para evitar el error de "Mixed Types"
    ingreso_base = st.number_input("Sueldo Base ($):", value=cargar_valor_estado("Ingresos_Totales", 1313500.0), step=1000.0)

with col_ing2:
    st.write("Ingresos Extras:")
    edit_extras = st.data_editor(pd.DataFrame([{"Concepto": "Extra", "Monto": 0.0}]), num_rows="dynamic", use_container_width=True, key="extras")
    total_extras = edit_extras["Monto"].sum()

ingreso_total = ingreso_base + total_extras
st.metric("TOTAL INGRESOS", f"$ {ingreso_total:,.0f}")

st.divider()

# --- 5. EGRESOS FIJOS ---
st.header("2. Egresos Fijos")
config_tablas = {"Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"), "Monto": st.column_config.NumberColumn("Monto ($)", format="$ %d")}

# Aquí cargamos lo que viene de la pestaña "Fijos_Actuales"
edit_fijos = st.data_editor(df_fijos_memoria, num_rows="dynamic", use_container_width=True, column_config=config_tablas, key="fijos_table")

total_fijos_proyectado = edit_fijos["Monto"].sum()
gastado_fijos_real = edit_fijos[edit_fijos["Pagado"] == True]["Monto"].sum()
presupuesto_base = ingreso_total - total_fijos_proyectado

st.info(f"💰 **Presupuesto restante:** ${presupuesto_base:,.0f}")

st.divider()

# --- 6. DISTRIBUCIÓN ---
st.header("3. Distribución")
c1, c2, c3 = st.columns(3)
with c1: p_ahorro = st.slider("% Ahorro", 0, 100, 42)
with c2: p_prog = st.slider("% Programados", 0, 100, 43)
with c3: p_noprog = st.slider("% No Programados", 0, 100, 15)

# Función para dibujar las 3 tablas de abajo
def seccion_detalle(col, titulo, pct, df_inicial, key_name, col_check):
    with col:
        asignado = presupuesto_base * (pct / 100)
        st.subheader(titulo)
        edit_df = st.data_editor(df_inicial, num_rows="dynamic", use_container_width=True, column_config=config_tablas, key=key_name)
        gastado = edit_df[edit_df[col_check] == True]["Monto"].sum()
        st.metric(f"Saldo {titulo}", f"$ {asignado - gastado:,.0f}")
        return gastado, edit_df

g1, df_ahorro_final = seccion_detalle(st.columns(3)[0], "Ahorro", p_ahorro, df_ahorro_memoria, "t_ah", "Listo")
g2, df_prog_final = seccion_detalle(st.columns(3)[1], "Programados", p_prog, df_prog_memoria, "t_pr", "Pagado")
g3, df_noprog_final = seccion_detalle(st.columns(3)[2], "No Prog.", p_noprog, df_noprog_memoria, "t_np", "Hecho")

# --- 7. SALDO REAL ---
st.divider()
saldo_final_cuenta = ingreso_total - (gastado_fijos_real + g1 + g2 + g3)
st.header("4. Saldo Real en Cuenta")
st.metric("Deberías tener hoy:", f"$ {saldo_final_cuenta:,.0f}")

# --- 8. BOTÓN DE GUARDADO (MEMORIA TOTAL) ---
if st.button("💾 Guardar TODO en Google Sheets"):
    with st.spinner("Guardando en todas las pestañas..."):
        try:
            # 1. Guardar resumen en Estado_Actual (Sobreescribir)
            resumen = pd.DataFrame([{
                "Fecha": date.today().strftime("%d/%m/%Y"),
                "Ingresos_Totales": float(ingreso_total),
                "Saldo_Final": float(saldo_final_cuenta)
            }])
            conn.update(spreadsheet=url_hoja, worksheet="Estado_Actual", data=resumen)

            # 2. Guardar el detalle de las 4 tablas (Para que se mantengan al recargar)
            conn.update(spreadsheet=url_hoja, worksheet="Fijos_Actuales", data=edit_fijos)
            conn.update(spreadsheet=url_hoja, worksheet="Ahorro_Actual", data=df_ahorro_final)
            conn.update(spreadsheet=url_hoja, worksheet="Prog_Actual", data=df_prog_final)
            conn.update(spreadsheet=url_hoja, worksheet="NoProg_Actual", data=df_noprog_final)

            # 3. Histórico (Acumular)
            try:
                hist_old = conn.read(spreadsheet=url_hoja, worksheet="Historico", ttl=0)
                hist_new = pd.concat([hist_old, resumen], ignore_index=True)
            except:
                hist_new = resumen
            conn.update(spreadsheet=url_hoja, worksheet="Historico", data=hist_new)

            st.balloons()
            st.success("✅ ¡Todo guardado! Las listas aparecerán tal cual las dejaste al volver a abrir la app.")
        except Exception as e:
            st.error(f"Error al guardar: {e}")