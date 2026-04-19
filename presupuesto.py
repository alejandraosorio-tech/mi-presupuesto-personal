import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# Configuración de la página
st.set_page_config(page_title="Mi Presupuesto Persistente", page_icon="💰")

st.title("💰 Gestión de Presupuesto Quincenal")
st.write("Los datos se mantienen guardados incluso si cierras la app.")

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
url_hoja = "https://docs.google.com/spreadsheets/d/1hwTThiotKRPqiDBEh5hvILvtEUkrdmnCIYoLnChFA7Y/edit"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. LECTURA DE MEMORIA (ESTADO ACTUAL) ---
# Intentamos leer lo último que se guardó para rellenar los campos
try:
    df_estado = conn.read(spreadsheet=url_hoja, worksheet="Estado_Actual", ttl=0)
    if not df_estado.empty:
        # Convertimos la última fila en un diccionario para fácil acceso
        memoria = df_estado.iloc[-1].to_dict()
    else:
        memoria = {}
except Exception:
    memoria = {}

# Función auxiliar para cargar el valor guardado o 0.0 si no existe
def cargar(nombre_columna):
    valor = memoria.get(nombre_columna, 0.0)
    try:
        return float(valor)
    except:
        return 0.0

# --- 3. INTERFAZ DE ENTRADA DE DATOS ---
st.header("📥 Ingresos y Gastos")

col1, col2 = st.columns(2)

with col1:
    ingreso_total = st.number_input(
        "Ingresos Totales (Quincena)", 
        value=cargar("Ingresos_Totales"), 
        step=10.0
    )
    
    gastado_fijos_real = st.number_input(
        "Gastos Fijos Reales", 
        value=cargar("Gastos_Fijos"), 
        step=10.0
    )

with col2:
    g1 = st.number_input(
        "Ahorro Realizado", 
        value=cargar("Ahorro_Realizado"), 
        step=10.0
    )
    
    g2 = st.number_input(
        "Gastos Programados", 
        value=cargar("Programados_Realizado"), 
        step=10.0
    )
    
    g3 = st.number_input(
        "Gastos NO Programados", 
        value=cargar("No_Programados_Realizado"), 
        step=10.0
    )

# --- 4. CÁLCULOS ---
# Calculamos el saldo final basado en lo que hay en pantalla
saldo_final_cuenta = ingreso_total - (gastado_fijos_real + g1 + g2 + g3)

st.divider()
st.metric(label="Saldo Final en Cuenta", value=f"${saldo_final_cuenta:,.2f}")

# --- 5. BOTÓN DE GUARDADO Y PERSISTENCIA ---
st.subheader("💾 Finalizar y Sincronizar")

if st.button("Guardar y Mantener Cambios"):
    # Creamos la fila con los datos actuales
    nueva_fila = pd.DataFrame([{
        "Fecha_Registro": date.today().strftime("%d/%m/%Y"),
        "Ingresos_Totales": float(ingreso_total),
        "Gastos_Fijos": float(gastado_fijos_real),
        "Ahorro_Realizado": float(g1),
        "Programados_Realizado": float(g2),
        "No_Programados_Realizado": float(g3),
        "Saldo_Final": float(saldo_final_cuenta)
    }])
    
    try:
        # A. GUARDAR EN HISTORICO (Añadir fila)
        # Leemos lo que ya hay en el historial
        try:
            historial_viejo = conn.read(spreadsheet=url_hoja, worksheet="Historico", ttl=0)
            historial_actualizado = pd.concat([historial_viejo, nueva_fila], ignore_index=True)
        except:
            historial_actualizado = nueva_fila
            
        conn.update(spreadsheet=url_hoja, worksheet="Historico", data=historial_actualizado)
        
        # B. GUARDAR EN ESTADO ACTUAL (Sobreescribir para que la app "recuerde")
        # Aquí solo guardamos la fila actual para que sea lo que lea la app al iniciar
        conn.update(spreadsheet=url_hoja, worksheet="Estado_Actual", data=nueva_fila)
        
        st.success("✅ ¡Datos guardados en la nube y memorizados en la app!")
        st.balloons()
        
        # C. RECARGAR (Para que los valores se asienten)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al guardar: {e}")

# --- 6. VISUALIZAR HISTORIAL ---
if st.checkbox("Ver últimos registros del historial"):
    try:
        df_ver = conn.read(spreadsheet=url_hoja, worksheet="Historico", ttl=0)
        st.dataframe(df_ver.tail(10))
    except:
        st.info("Aún no hay datos en el historial.")