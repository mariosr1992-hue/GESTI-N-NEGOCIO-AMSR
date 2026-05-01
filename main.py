import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
PASSWORD = "saker007"

def init_db():
    conn = sqlite3.connect('contabilidad_final_v5.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id_interno INTEGER PRIMARY KEY AUTOINCREMENT, 
                  ref_factura TEXT, fecha TEXT, categoria TEXT, concepto TEXT,
                  base_imponible REAL, iva_cuota REAL, total_bruto REAL,
                  irpf_retenido REAL, ss_coste REAL, efectivo_extra REAL,
                  mod_303 REAL, mod_111 REAL, mod_130 REAL, cuota_autonomo REAL,
                  metodo_pago TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def obtener_siguiente_factura():
    # Lógica para generar el formato F_AÑO_001
    anio_actual = datetime.now().year
    c = conn.cursor()
    # Buscamos facturas emitidas de este año
    c.execute("SELECT ref_factura FROM registros WHERE categoria = 'Venta (Factura Emitida)' AND ref_factura LIKE ?", (f'F_{anio_actual}_%',))
    facturas = c.fetchall()
    
    if not facturas:
        return f"F_{anio_actual}_001"
    
    # Extraemos los números, buscamos el máximo y sumamos 1
    numeros = [int(f[0].split('_')[-1]) for f in facturas]
    siguiente = max(numeros) + 1
    return f"F_{anio_actual}_{siguiente:03d}"

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

tab_reg, tab_hist, tab_imp = st.tabs(["📝 Registros", "📋 Historial", "⚖️ Análisis"])

with tab_reg:
    cat = st.selectbox("Categoría de Registro", 
                       ["Venta (Factura Emitida)", "Gasto (Factura Recibida)", "Nómina Empleado", "Tasa Autónomo", "Pago de Impuestos / Modelos"])
    
    # Sugerir referencia automática si es venta
    sugerencia_ref = obtener_siguiente_factura() if cat == "Venta (Factura Emitida)" else ""

    with st.form("form_v5"):
        ref_factura = st.text_input("Referencia / Nº Factura", value=sugerencia_ref)
        concepto = st.text_input("Concepto / Cliente")
        fecha = st.date_input("Fecha", datetime.now())
        
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
            st.subheader("Desglose Nómina")
            c1, c2 = st.columns(2)
            liq = c1.number_input("Líquido (€)", min_value=0.0)
            irpf = c2.number_input("IRPF (Mod 111) (€)", min_value=0.0)
            ss = c1.number_input("Seg. Social (€)", min_value=0.0)
            extra = c2.number_input("Extra Efectivo (€)", min_value=0.0)
            total = liq + irpf + ss + extra
            m111 = irpf

        elif cat == "Tasa Autónomo":
            c_aut = st.number_input("Cuota Mensual (€)", min_value=0.0)
            total = c_aut

        elif "Impuestos" in cat:
            m303 = st.number_input("Mod 303 (€)", min_value=0.0)
            m130 = st.number_input("Mod 130 (€)", min_value=0.0)
            m111 = st.number_input("Mod 111 (€)", min_value=0.0)
            total = m303 + m130 + m111

        metodo = st.radio("Forma de Pago", ["Banco", "Efectivo"])

        if st.form_submit_button("Guardar Registro"):
            c = conn.cursor()
            c.execute("INSERT INTO registros (ref_factura, fecha, categoria, concepto, base_imponible, iva_cuota, total_bruto, irpf_retenido, ss_coste, efectivo_extra, mod_303, mod_111, mod_130, cuota_autonomo, metodo_pago) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (ref_factura, fecha.strftime("%Y-%m-%d"), cat, concepto, base, iva, total, irpf, ss, extra, m303, m111, m130, c_aut, metodo))
            conn.commit()
            st.success(f"✅ Guardado como {ref_factura}")
            st.rerun()

with tab_hist:
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df)

with tab_imp:
    # ... (Mantenemos la lógica de cálculos anterior)
    st.header("📊 Resumen Fiscal")
    if not df.empty:
        col1, col2 = st.columns(2)
        col1.metric("IVA Acumulado", f"{df['iva_cuota'].sum():.2f}€")
        col2.metric("Total Gastos", f"{df[df['categoria'] != 'Venta (Factura Emitida)']['total_bruto'].sum():.2f}€")
