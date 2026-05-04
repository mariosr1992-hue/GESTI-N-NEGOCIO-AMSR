import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time

# --- CONFIGURACIÓN ---
PASSWORD = "saker007"

def init_db():
    conn = sqlite3.connect('contabilidad_saker_v9.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla de contabilidad (la que ya teníamos)
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id_interno INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ref_factura TEXT, fecha TEXT, categoria TEXT, concepto TEXT,
                  base_imponible REAL, iva_cuota REAL, total_bruto REAL,
                  irpf_retenido REAL, ss_coste REAL, efectivo_extra REAL,
                  mod_303 REAL, mod_111 REAL, mod_130 REAL, cuota_autonomo REAL,
                  metodo_pago TEXT)''')
    
    # NUEVA TABLA: Control de presencia
    c.execute('''CREATE TABLE IF NOT EXISTS fichajes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  empleado TEXT,
                  evento TEXT,
                  hora TEXT,
                  ubicacion TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LOGIN (Igual que antes) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acceso - saker007")
    if st.text_input("Clave", type="password") == PASSWORD:
        if st.button("Entrar"):
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

st.title("📊 Sistema Integral saker007")

# --- PESTAÑAS ---
tab_reg, tab_hist, tab_fichar, tab_imp = st.tabs(["📝 Contabilidad", "📋 Historial", "🕒 Control Horario", "⚖️ Impuestos"])

# (Mantenemos el código de tab_reg y tab_hist de la versión anterior)

with tab_fichar:
    st.header("🕒 Registro de Jornada")
    
    empleado = st.selectbox("Selecciona tu nombre", ["Empleado 1", "Empleado 2", "Gerente"])
    
    # Simulación de Geolocalización (Streamlit requiere componentes externos para GPS real, 
    # pero aquí preparamos el campo para recibirlo)
    st.info("Al pulsar, se registrará tu ubicación actual.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏁 ENTRADA"):
            # Aquí iría la lógica de captura GPS
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c = conn.cursor()
            c.execute("INSERT INTO fichajes (empleado, evento, hora, ubicacion) VALUES (?, ?, ?, ?)",
                      (empleado, "ENTRADA", ahora, "Ubicación GPS capturada"))
            conn.commit()
            st.success(f"Entrada registrada: {ahora}")

        if st.button("☕ DESAYUNO (Pausa)"):
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.cursor().execute("INSERT INTO fichajes (empleado, evento, hora, ubicacion) VALUES (?, ?, ?, ?)",
                                  (empleado, "DESAYUNO", ahora, "Ubicación GPS"))
            conn.commit()
            st.info("Pausa de desayuno iniciada (No descuenta)")

    with col2:
        if st.button("🍽️ COMIDA (Descuenta)"):
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.cursor().execute("INSERT INTO fichajes (empleado, evento, hora, ubicacion) VALUES (?, ?, ?, ?)",
                                  (empleado, "COMIDA", ahora, "Ubicación GPS"))
            conn.commit()
            st.warning("Pausa de comida iniciada (Se descontará del tiempo total)")

        if st.button("🛑 SALIDA"):
            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.cursor().execute("INSERT INTO fichajes (empleado, evento, hora, ubicacion) VALUES (?, ?, ?, ?)",
                                  (empleado, "SALIDA", ahora, "Ubicación GPS"))
            conn.commit()
            st.error(f"Salida registrada: {ahora}")

    st.divider()
    st.subheader("Registros de hoy")
    fichajes_df = pd.read_sql_query(f"SELECT evento, hora, ubicacion FROM fichajes WHERE empleado='{empleado}' ORDER BY hora DESC", conn)
    st.table(fichajes_df)

# (Mantenemos la pestaña de impuestos igual)
