import pandas as pd
import streamlit as st
from datetime import date

st.set_page_config(page_title="Mi Presupuesto Quincenal", layout="wide")

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
    df_extras_init = pd.DataFrame([{"Concepto": "Venta ropa", "Monto": 0}])
    edit_extras = st.data_editor(df_extras_init, num_rows="dynamic", use_container_width=True, key="extras")
    total_extras = edit_extras["Monto"].sum()

ingreso_total = ingreso_base + total_extras
st.metric("TOTAL INGRESOS", f"$ {ingreso_total:,.0f}")

st.divider()

# --- 2. EGRESOS FIJOS (CON TUS NUEVAS PETICIONES) ---
st.header("2. Egresos Fijos")

# Datos iniciales
df_fijos_init = pd.DataFrame([
    {"Fecha": date(2024, 4, 17), "Concepto": "Gasolina", "Monto": 11000, "Pagado": True},
    {"Fecha": date(2024, 4, 19), "Concepto": "Gasolina", "Monto": 25000, "Pagado": False},
    {"Fecha": date(2024, 4, 24), "Concepto": "Davivienda", "Monto": 306000, "Pagado": True},
    {"Fecha": date(2024, 4, 24), "Concepto": "Nubank", "Monto": 235000, "Pagado": True},
])

# Configuración de columnas
config_fijos = {
    "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$ %d")
}

# Editor de la tabla
edit_fijos = st.data_editor(df_fijos_init, num_rows="dynamic", use_container_width=True, column_config=config_fijos, key="fijos_table")

# CALCULOS NUEVOS
total_fijos_proyectado = edit_fijos["Monto"].sum()
porcentaje_fijos = (total_fijos_proyectado / ingreso_total * 100) if ingreso_total > 0 else 0

# Mostramos los valores que pediste justo debajo de la tabla (o encima si prefieres)
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

# Verificación de suma 100%
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
        return gastado

df_ah_init = pd.DataFrame([{"Fecha": date(2024, 4, 15), "Concepto": "Ahorro SOAT", "Monto": 78200, "Listo": True}])
df_pr_init = pd.DataFrame([{"Fecha": date(2024, 4, 24), "Concepto": "Depilación Láser", "Monto": 125000, "Pagado": False}])
df_np_init = pd.DataFrame([{"Fecha": date(2024, 4, 18), "Concepto": "Retiro Efectivo", "Monto": 50000, "Hecho": True}])

g1 = crear_seccion_rubro(col_r1, "Ahorro", p_ahorro, df_ah_init, "t_ahorro")
g2 = crear_seccion_rubro(col_r2, "Programados", p_prog, df_pr_init, "t_prog")
g3 = crear_seccion_rubro(col_r3, "No Prog.", p_noprog, df_np_init, "t_noprog")

# --- 4. SALDO GLOBAL ---
st.divider()
total_pagado_real = edit_fijos[edit_fijos["Pagado"] == True]["Monto"].sum() + g1 + g2 + g3
saldo_final_cuenta = ingreso_total - total_pagado_real
st.header("4. Saldo Real en Cuenta")
st.metric("Dinero que debería haber hoy:", f"$ {saldo_final_cuenta:,.0f}")