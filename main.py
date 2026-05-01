import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN Y SEGURIDAD ---
PASSWORD = "mi_clave_secreta"

def init_db():
    conn = sqlite3.connect('negocio_v3.db', check_same_thread=False)
    c = conn.cursor()
    # Nueva tabla con campos desglosados y ID único
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos
                 (id_ref TEXT PRIMARY KEY, fecha TEXT, tipo TEXT, concepto TEXT, 
                  base_imponible REAL, iva_porcentaje REAL, iva_cuota REAL, 
                  total_bruto REAL, liquido REAL, irpf REAL, ss REAL, 
                  extra_cash REAL, metodo TEXT, estado TEXT)''')
    conn.commit()
    return conn

conn = init_db()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Acceso Privado")
    if st.text_input("Contraseña", type="password") == PASSWORD:
        if st.button("Entrar"):
            st.session_state["authenticated"] = True
            st.rerun()
    st.stop()

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 Gestión de Negocio V3.0")

menu = st.sidebar.selectbox("Acciones", ["Registrar Movimiento", "Historial y Edición", "Análisis de Beneficio"])

if menu == "Registrar Movimiento":
    st.header("📝 Nueva Entrada")
    
    tipo = st.selectbox("Tipo de Registro", ["Venta (Factura Emitida)", "Gasto (Factura Recibida)", "Nómina Empleado"])
    
    with st.form("form_v3"):
        id_ref = st.text_input("ID / Nº Factura (Único)", help="No se puede repetir")
        concepto = st.text_input("Concepto / Nombre")
        fecha = st.date_input("Fecha", datetime.now())
        
        # LÓGICA DE FACTURAS
        if "Factura" in tipo:
            col1, col2 = st.columns(2)
            base = col1.number_input("Base Imponible (€)", min_value=0.0, format="%.2f")
            iva_p = col2.selectbox("IVA %", [21, 10, 4, 0])
            
            cuota_iva = base * (iva_p / 100)
            total = base + cuota_iva
            st.info(f"Cálculo: IVA {cuota_iva:.2f}€ | Total Bruto: {total:.2f}€")
            
            # Campos de nómina vacíos
            liq, irpf, ss, extra = 0.0, 0.0, 0.0, 0.0
            
        # LÓGICA DE NÓMINAS
        else:
            col1, col2 = st.columns(2)
            liq = col1.number_input("Líquido a percibir (€)", min_value=0.0)
            irpf = col2.number_input("Retención IRPF (€)", min_value=0.0)
            ss = col1.number_input("Seguridad Social (€)", min_value=0.0)
            extra = col2.number_input("Extra en Efectivo (€)", min_value=0.0)
            
            total = liq + irpf + ss + extra
            base, iva_p, cuota_iva = 0.0, 0, 0.0
            st.warning(f"Coste Total para el negocio: {total:.2f}€")

        metodo = st.radio("Método de Pago", ["Banco", "Efectivo"])
        estado = st.selectbox("Estado", ["Completado", "Pendiente"])
        archivo = st.file_uploader("Subir foto/recibo (Simulación)", type=["jpg", "png", "pdf"])

        if st.form_submit_button("Guardar Registro"):
            try:
                c = conn.cursor()
                c.execute("INSERT INTO movimientos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (id_ref, fecha.strftime("%Y-%m-%d"), tipo, concepto, base, iva_p, cuota_iva, total, liq, irpf, ss, extra, metodo, estado))
                conn.commit()
                st.success("✅ Guardado con éxito")
            except sqlite3.IntegrityError:
                st.error("❌ ERROR: El ID / Nº de Factura ya existe. No se permiten duplicados.")

elif menu == "Historial y Edición":
    st.header("📋 Listado de Movimientos")
    df = pd.read_sql_query("SELECT * FROM movimientos", conn)
    
    if not df.empty:
        st.dataframe(df)
        
        st.subheader("🛠 Editar Registro")
        id_edit = st.selectbox("Selecciona el ID para modificar", df['id_ref'].tolist())
        if st.button("Eliminar Registro"):
            conn.cursor().execute("DELETE FROM movimientos WHERE id_ref=?", (id_edit,))
            conn.commit()
            st.rerun()
    else:
        st.info("No hay datos registrados.")

elif menu == "Análisis de Beneficio":
    df = pd.read_sql_query("SELECT * FROM movimientos", conn)
    if not df.empty:
        ingresos = df[df['tipo'] == "Venta (Factura Emitida)"]['total_bruto'].sum()
        gastos = df[df['tipo'] != "Venta (Factura Emitida)"]['total_bruto'].sum()
        
        st.metric("Beneficio Bruto", f"{ingresos - gastos:,.2f}€")
        # Aquí podrías añadir los gráficos de Plotly que vimos antes
    else:
        st.info("Sin datos para analizar.")
