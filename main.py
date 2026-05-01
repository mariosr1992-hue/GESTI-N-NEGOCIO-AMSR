import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
PASSWORD = "saker007"

def init_db():
    conn = sqlite3.connect('contabilidad_total.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id TEXT PRIMARY KEY, fecha TEXT, categoria TEXT, concepto TEXT,
                  base_imponible REAL, iva_cuota REAL, total_bruto REAL,
                  irpf_retenido REAL, ss_coste REAL, efectivo_extra REAL,
                  modelo_asociado TEXT, metodo_pago TEXT)''')
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

tab_reg, tab_hist, tab_imp = st.tabs(["📝 Registros", "📋 Historial", "⚖️ Modelos Fiscales"])

with tab_reg:
    cat = st.selectbox("Categoría de Registro", 
                       ["Venta (Factura Emitida)", "Gasto (Factura Recibida)", "Nómina Empleado", "Tasa Autónomo", "Pago de Impuestos"])
    
    with st.form("form_contable"):
        id_ref = st.text_input("Referencia / ID Único")
        concepto = st.text_input("Concepto")
        fecha = st.date_input("Fecha", datetime.now())
        
        # Variables por defecto
        base, iva, total, irpf, ss, extra = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        modelo = "Ninguno"

        if "Factura" in cat:
            c1, c2 = st.columns(2)
            base = c1.number_input("Base Imponible (€)", min_value=0.0)
            tipo_iva = c2.selectbox("IVA %", [21, 10, 4, 0])
            iva = base * (tipo_iva / 100)
            total = base + iva
            modelo = "Mod. 303 (IVA)"
            st.info(f"Total Bruto: {total:.2f}€ | IVA: {iva:.2f}€")

        elif cat == "Nómina Empleado":
            st.subheader("Desglose de Nómina")
            col1, col2 = st.columns(2)
            liq = col1.number_input("Líquido a percibir (Banco) (€)", min_value=0.0)
            irpf = col2.number_input("IRPF Retenido (Mod. 111) (€)", min_value=0.0)
            ss = col1.number_input("Seguridad Social (€)", min_value=0.0)
            extra = col2.number_input("Dinero Extra (Efectivo) (€)", min_value=0.0)
            total = liq + irpf + ss + extra
            modelo = "Mod. 111 (Nóminas)"
            st.warning(f"Coste Total Empleado: {total:.2f}€")

        elif cat == "Tasa Autónomo":
            total = st.number_input("Importe Cuota (€)", min_value=0.0)
            modelo = "Gasto Deducible (Mod. 130)"

        metodo = st.radio("Forma de Pago", ["Banco", "Efectivo"])

        if st.form_submit_button("Registrar en Contabilidad"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO registros VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (id_ref, fecha.strftime("%Y-%m-%d"), cat, concepto, base, iva, total, irpf, ss, extra, modelo, metodo))
                conn.commit()
                st.success(f"Registrado correctamente en {modelo}")
            except:
                st.error("Error: Ese ID ya existe. Usa uno diferente.")

with tab_hist:
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df)
    if st.button("Eliminar seleccionado (Por ID)"):
        # Lógica de eliminación simple por referencia
        st.info("Escribe el ID arriba para borrar (Función en desarrollo)")

with tab_imp:
    st.header("🏢 Resumen para Modelos Oficiales")
    if not df.empty:
        # Lógica de cálculo real
        iva_ventas = df[df['categoria'] == "Venta (Factura Emitida)"]['iva_cuota'].sum()
        iva_gastos = df[df['categoria'] == "Gasto (Factura Recibida)"]['iva_cuota'].sum()
        
        st.subheader("Modelo 303 (IVA)")
        st.write(f"IVA a pagar: **{iva_ventas - iva_gastos:.2f}€**")
        
        st.subheader("Modelo 111 (Retenciones Nómina)")
        st.write(f"Total a ingresar: **{df['irpf_retenido'].sum():.2f}€**")
        
        st.subheader("Modelo 130 (Tu IRPF - 20%)")
        ingresos = df[df['categoria'] == "Venta (Factura Emitida)"]['base_imponible'].sum()
        gastos = df[df['categoria'] != "Venta (Factura Emitida)"]['base_imponible'].sum()
        resultado = ingresos - gastos
        st.write(f"Resultado actividad: {resultado:.2f}€")
        st.write(f"A pagar (20%): **{max(0, resultado * 0.20):.2f}€**")
