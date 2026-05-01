import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
PASSWORD = "saker007"

def init_db():
    conn = sqlite3.connect('contabilidad_saker_v7.db', check_same_thread=False)
    c = conn.cursor()
    # Usamos un ID interno automático para que NO te de error al repetir nombres de factura
    c.execute('''CREATE TABLE IF NOT EXISTS registros
                 (id_auto INTEGER PRIMARY KEY AUTOINCREMENT, 
                  referencia TEXT, fecha TEXT, categoria TEXT, concepto TEXT,
                  base_imponible REAL, iva_cuota REAL, total_bruto REAL,
                  irpf REAL, ss REAL, extra_efectivo REAL,
                  m303 REAL, m111 REAL, m130 REAL, cuota_autonomo REAL,
                  metodo TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acceso - saker007")
    if st.text_input("Introduce la clave", type="password") == PASSWORD:
        if st.button("Entrar"):
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- APP ---
st.title("📊 Gestor Financiero saker007")

menu = st.sidebar.radio("Menú", ["Registrar", "Historial", "Impuestos y Beneficios"])

if menu == "Registrar":
    cat = st.selectbox("Categoría", ["Venta", "Gasto", "Nómina Empleado", "Autónomo / Impuestos"])
    
    with st.form("main_form"):
        ref = st.text_input("Nº Factura / Ref (Ej: F_2026_001)")
        concepto = st.text_input("Concepto")
        fecha = st.date_input("Fecha", datetime.now())
        
        # Valores por defecto
        base, iva, total, irpf, ss, extra = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        m303, m111, m130, cau = 0.0, 0.0, 0.0, 0.0

        if cat in ["Venta", "Gasto"]:
            c1, c2 = st.columns(2)
            base = c1.number_input("Base Imponible (€)", min_value=0.0)
            tipo_iva = c2.selectbox("IVA %", [21, 10, 4, 0])
            iva = base * (tipo_iva / 100)
            total = base + iva
            st.info(f"Total calculado: {total:.2f}€")

        elif cat == "Nómina Empleado":
            c1, c2 = st.columns(2)
            liq = c1.number_input("Líquido a percibir (€)", min_value=0.0)
            irpf = c2.number_input("Retención IRPF (Mod. 111) (€)", min_value=0.0)
            ss = c1.number_input("Seguridad Social (€)", min_value=0.0)
            extra = c2.number_input("Extra en Efectivo (€)", min_value=0.0)
            total = liq + irpf + ss + extra
            m111 = irpf

        elif cat == "Autónomo / Impuestos":
            c1, c2 = st.columns(2)
            cau = c1.number_input("Cuota Autónomo (€)", min_value=0.0)
            m303 = c2.number_input("Pago IVA (Mod. 303) (€)", min_value=0.0)
            m130 = c1.number_input("Pago IRPF (Mod. 130) (€)", min_value=0.0)
            total = cau + m303 + m130

        metodo = st.radio("Método", ["Banco", "Efectivo"])

        if st.form_submit_button("Guardar Registro"):
            c = conn.cursor()
            c.execute("INSERT INTO registros (referencia, fecha, categoria, concepto, base_imponible, iva_cuota, total_bruto, irpf, ss, extra_efectivo, m303, m111, m130, cuota_autonomo, metodo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (ref, fecha.strftime("%Y-%m-%d"), cat, concepto, base, iva, total, irpf, ss, extra, m303, m111, m130, cau, metodo))
            conn.commit()
            st.success("✅ Guardado correctamente")

elif menu == "Historial":
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    st.write("### Todos los movimientos")
    st.dataframe(df)
    
    st.divider()
    id_del = st.number_input("ID a eliminar", min_value=1, step=1)
    if st.button("Eliminar Registro"):
        conn.cursor().execute("DELETE FROM registros WHERE id_auto=?", (id_del,))
        conn.commit()
        st.rerun()

elif menu == "Impuestos y Beneficios":
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    if not df.empty:
        ingresos = df[df['categoria'] == "Venta"]['base_imponible'].sum()
        gastos = df[df['categoria'] != "Venta"]['total_bruto'].sum()
        
        st.metric("Beneficio Neto (Caja)", f"{ingresos - gastos:.2f}€")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("IVA Pagado", f"{df['m303'].sum():.2f}€")
        col2.metric("IRPF (130)", f"{df['m130'].sum():.2f}€")
        col3.metric("Autónomo", f"{df['cuota_autonomo'].sum():.2f}€")
