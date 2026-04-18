import pandas as pd
import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection # Necesitamos instalar esto

st.set_page_config(page_title="Mi Presupuesto Quincenal", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. INGRESOS ---
st.header("1. Mis Ingresos")
ingreso_base = st.number_input("Sueldo Base ($):", value=1313500)
# (Para simplificar esta versión, sumaremos solo el base, puedes luego añadir los extras)

# --- 2. TABLAS DE GASTOS (Simplificadas para el ejemplo) ---
st.header("2. Registro de Movimientos")
# (Aquí iría todo el código de tus tablas que ya tienes, lo resumo para enfocarnos en el guardado)
# Supongamos que ya tienes los totales calculados:
total_fijos = 577000 # Esto vendría de tus tablas
total_ahorro = 278200
total_prog = 113000
total_noprog = 50000

total_gastado = total_fijos + total_ahorro + total_prog + total_noprog
saldo_final = ingreso_base - total_gastado

st.metric("SALDO FINAL HOY", f"$ {saldo_final:,.0f}")

# --- 3. EL BOTÓN MÁGICO: CERRAR QUINCENA ---
st.divider()
st.subheader("💾 Finalizar y Guardar Historial")
st.write("Presiona este botón solo cuando termines tu quincena para guardar el resumen en tu historial.")

if st.button("Guardar en mi Historial de Google Sheets"):
    # Creamos la fila de datos
    nueva_fila = pd.DataFrame([{
        "Fecha_Registro": date.today().strftime("%d/%m/%Y"),
        "Ingresos_Totales": ingreso_base,
        "Gastos_Fijos": total_fijos,
        "Ahorro_Realizado": total_ahorro,
        "Programados_Realizado": total_prog,
        "No_Programados_Realizado": total_noprog,
        "Saldo_Final": saldo_final
    }])
    
    # Leemos lo que ya hay en Google Sheets
    datos_existentes = conn.read(worksheet="Historico")
    
    # Unimos los datos viejos con la nueva fila
    tabla_actualizada = pd.concat([datos_existentes, nueva_fila], ignore_index=True)
    
    # Lo mandamos de vuelta a Google
    conn.update(worksheet="Historico", data=tabla_actualizada)
    
    st.success("✅ ¡Datos guardados con éxito en tu Google Sheets!")
    st.balloons()