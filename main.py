import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
PASSWORD = "saker007"  # <--- Contraseña actualizada

def init_db():
    conn = sqlite3.connect('gestion_contable_v3.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos
                 (id_ref TEXT PRIMARY KEY, fecha TEXT, tipo TEXT, concepto TEXT, 
                  base_imponible REAL, iva_porcentaje REAL, iva_cuota REAL, 
                  total_bruto REAL, liquido REAL, irpf REAL, ss REAL, 
                  extra_cash REAL, metodo TEXT, estado TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acceso Privado - saker007")
    input_pass = st.text_input("Introduce clave", type="password")
    if st.button("Entrar"):
        if input_pass == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# --- APP PRINCIPAL ---
st.title("📊 Gestor Financiero Real")

tab1, tab2, tab3 = st.tabs(["📝 Registros", "📋 Historial", "⚖️ Modelos e Impuestos"])

with tab1:
    tipo = st.selectbox("Categoría de Registro", 
                        ["Venta (Factura Emitida)", "Gasto (Factura Recibida)", "Nómina Empleado", "Tasa Autónomo"])
    
    with st.form("registro_form"):
        id_ref = st.text_input("Referencia / Nº Factura", help="Debe ser único")
        concepto = st.text_input("Concepto")
        fecha = st.date_input("Fecha operación", datetime.now())
        
        # Inicializamos variables
        base, iva_p, cuota_iva, total = 0.0, 0, 0.0, 0.0
        liq, irpf, ss, extra = 0.0, 0.0, 0.0, 0.0

        if "Factura" in tipo:
            c1, c2 = st.columns(2)
            base = c1.number_input("Base Imponible (€)", min_value=0.0)
            iva_p = c2.selectbox("IVA %", [21, 10, 4, 0])
            cuota_iva = base * (iva_p / 100)
            total = base + cuota_iva
            st.info(f"Total: {total:.2f}€ (IVA: {cuota_iva:.2f}€)")

        elif "Nómina" in tipo:
            c1, c2 = st.columns(2)
            liq = c1.number_input("Líquido a percibir (€)", min_value=0.0)
            irpf = c2.number_input("Retención IRPF (Mod. 111) (€)", min_value=0.0)
            ss = c1.number_input("Seguridad Social (€)", min_value=0.0)
            extra = c2.number_input("Extra Cash (Fuera nómina) (€)", min_value=0.0)
            total = liq + irpf + ss + extra

        elif "Autónomo" in tipo:
            total = st.number_input("Cuota Autónomo Mensual (€)", min_value=0.0)
            base = total # Se cuenta como gasto total

        metodo = st.radio("Método", ["Banco", "Efectivo"])
        
        if st.form_submit_button("Guardar Datos"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO movimientos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (id_ref, fecha.strftime("%Y-%m-%d"), tipo, concepto, base, iva_p, cuota_iva, total, liq, irpf, ss, extra, metodo, "Completado"))
                conn.commit()
                st.success("¡Datos guardados!")
            except:
                st.error("Error: ID duplicado o datos inválidos")

with tab2:
    df = pd.read_sql_query("SELECT * FROM movimientos", conn)
    st.dataframe(df)
    if st.button("Limpiar todo (CUIDADO)"):
        conn.cursor().execute("DELETE FROM movimientos")
        conn.commit()
        st.rerun()

with tab3:
    st.header("🏢 Liquidación de Impuestos (Estimación)")
    if not df.empty:
        # IVA (Modelo 303)
        iva_repercutido = df[df['tipo'] == "Venta (Factura Emitida)"]['iva_cuota'].sum()
        iva_soportado = df[df['tipo'] == "Gasto (Factura Recibida)"]['iva_cuota'].sum()
        mod_303 = iva_repercutido - iva_soportado

        # Retenciones (Modelo 111)
        mod_111 = df['irpf'].sum()

        # IRPF (Modelo 130 - 20% del beneficio)
        ingresos_brutos = df[df['tipo'] == "Venta (Factura Emitida)"]['base_imponible'].sum()
        gastos_deducibles = df[df['tipo'] != "Venta (Factura Emitida)"]['base_imponible'].sum()
        beneficio_antes_irpf = ingresos_brutos - gastos_deducibles
        mod_130 = beneficio_antes_irpf * 0.20 if beneficio_antes_irpf > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Mod. 303 (IVA)", f"{mod_303:.2f}€")
        col2.metric("Mod. 111 (Retenciones)", f"{mod_111:.2f}€")
        col3.metric("Mod. 130 (IRPF)", f"{mod_130:.2f}€")

        st.divider()
        beneficio_real = beneficio_antes_irpf - mod_130 - mod_111
        st.subheader(f"💰 Ganancia Real Neta: {beneficio_real:.2f}€")
        if beneficio_real < 0:
            st.error("Estás en pérdidas")
        else:
            st.balloons()
