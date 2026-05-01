import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
PASSWORD = "saker007"

def init_db():
    conn = sqlite3.connect('contabilidad_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id TEXT PRIMARY KEY, fecha TEXT, categoria TEXT, concepto TEXT,
                  base_imponible REAL, iva_cuota REAL, total_bruto REAL,
                  irpf_retenido REAL, ss_coste REAL, efectivo_extra REAL,
                  mod_303 REAL, mod_111 REAL, mod_130 REAL, cuota_autonomo REAL,
                  metodo_pago TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acceso - saker007")
    if st.text_input("Clave", type="password") == PASSWORD:
        if st.button("Entrar"):
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

st.title("📊 Gestor Financiero Real")

tab_reg, tab_hist, tab_imp = st.tabs(["📝 Registros", "📋 Historial", "⚖️ Análisis de Modelos"])

with tab_reg:
    cat = st.selectbox("Categoría de Registro", 
                       ["Venta (Factura Emitida)", "Gasto (Factura Recibida)", "Nómina Empleado", "Tasa Autónomo", "Pago de Impuestos / Modelos"])
    
    with st.form("form_contable_v3"):
        id_ref = st.text_input("Referencia / ID Único")
        concepto = st.text_input("Concepto (Ej: Factura Mayo, Nómina Juan, Autónomo Junio)")
        fecha = st.date_input("Fecha", datetime.now())
        
        # Inicialización de valores
        base, iva, total, irpf, ss, extra = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        m303, m111, m130, c_aut = 0.0, 0.0, 0.0, 0.0

        if "Factura" in cat:
            c1, c2 = st.columns(2)
            base = c1.number_input("Base Imponible (€)", min_value=0.0, format="%.2f")
            tipo_iva = c2.selectbox("IVA %", [21, 10, 4, 0])
            iva = base * (tipo_iva / 100)
            total = base + iva
            st.info(f"Total: {total:.2f}€ | IVA: {iva:.2f}€")

        elif cat == "Nómina Empleado":
            st.subheader("Desglose de Nómina")
            col1, col2 = st.columns(2)
            liq = col1.number_input("Líquido a percibir (Banco) (€)", min_value=0.0)
            irpf = col2.number_input("IRPF Retenido (Mod. 111) (€)", min_value=0.0)
            ss = col1.number_input("Seguridad Social Empresa/Trab. (€)", min_value=0.0)
            extra = col2.number_input("Dinero Extra (Efectivo) (€)", min_value=0.0)
            total = liq + irpf + ss + extra
            m111 = irpf # Se vincula al modelo 111
            st.warning(f"Coste Total: {total:.2f}€")

        elif cat == "Tasa Autónomo":
            st.subheader("Desglose Autónomo")
            c_aut = st.number_input("Cuota Mensual (€)", min_value=0.0)
            otros_seguros = st.number_input("Otros seguros vinculados (€)", min_value=0.0)
            total = c_aut + otros_seguros

        elif "Impuestos" in cat:
            st.subheader("Liquidación de Modelos Oficiales")
            m303 = st.number_input("Pago Modelo 303 (IVA) (€)", min_value=0.0)
            m130 = st.number_input("Pago Modelo 130 (IRPF) (€)", min_value=0.0)
            m111 = st.number_input("Pago Modelo 111 (Retenciones) (€)", min_value=0.0)
            total = m303 + m130 + m111

        metodo = st.radio("Forma de Pago", ["Banco", "Efectivo"])

        if st.form_submit_button("Registrar Movimiento"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO registros VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (id_ref, fecha.strftime("%Y-%m-%d"), cat, concepto, base, iva, total, irpf, ss, extra, m303, m111, m130, c_aut, metodo))
                conn.commit()
                st.success("✅ Registrado con éxito en el historial contable")
            except:
                st.error("❌ Error: Ese ID ya existe o los datos son incorrectos.")

with tab_hist:
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df)

with tab_imp:
    st.header("📊 Resumen Fiscal y Autónomo")
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total IVA (Mod. 303)", f"{df['mod_303'].sum():.2f}€")
        col2.metric("Total IRPF (Mod. 130)", f"{df['mod_130'].sum():.2f}€")
        col3.metric("Total Autónomo", f"{df['cuota_autonomo'].sum():.2f}€")
        
        st.divider()
        ingresos = df[df['categoria'] == "Venta (Factura Emitida)"]['base_imponible'].sum()
        gastos_totales = df[df['categoria'] != "Venta (Factura Emitida)"]['total_bruto'].sum()
        st.subheader(f"💰 Beneficio Neto Real: {ingresos - gastos_totales:.2f}€")
