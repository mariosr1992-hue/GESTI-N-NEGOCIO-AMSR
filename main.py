import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px

# 1. SEGURIDAD: Configura tu contraseña aquí
PASSWORD = "mi_clave_secreta" # <--- CAMBIA ESTO

def login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        st.title("🔐 Acceso Privado")
        input_pass = st.text_input("Introduce la contraseña de tu negocio", type="password")
        if st.button("Entrar"):
            if input_pass == PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return False
    return True

if login():
    # --- LA APP EMPIEZA AQUÍ ---
    st.set_page_config(page_title="Gestor Pro", layout="wide")
    
    conn = sqlite3.connect('datos_negocio.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos
                 (fecha TEXT, tipo TEXT, concepto TEXT, total REAL, iva REAL, metodo TEXT, estado TEXT)''')
    conn.commit()

    st.title("📊 Panel de Control y Beneficio Real")

    # BARRA LATERAL
    with st.sidebar:
        st.header("📝 Nuevo Registro")
        with st.form("form_registro"):
            tipo = st.selectbox("Categoría", ["Factura Emitida (Venta)", "Factura Recibida (Gasto)", "Nómina", "Seguridad Social", "Impuestos"])
            concepto = st.text_input("Detalle")
            monto = st.number_input("Importe Total (€)", min_value=0.0)
            metodo = st.radio("Método", ["Banco", "Efectivo"])
            estado = st.selectbox("Estado", ["Abonado/Cobrado", "Pendiente"])
            
            # Lógica de IVA simplificada
            iva_opcion = st.selectbox("IVA %", [21, 10, 4, 0]) if "Factura" in tipo else 0
            
            if st.form_submit_button("Guardar"):
                base = monto / (1 + iva_opcion/100)
                iva_v = monto - base
                c.execute("INSERT INTO movimientos VALUES (?,?,?,?,?,?,?)",
                          (datetime.now().strftime("%Y-%m-%d"), tipo, concepto, monto, iva_v, metodo, estado))
                conn.commit()
                st.success("¡Registrado!")

    # CÁLCULOS Y GRÁFICOS
    df = pd.read_sql_query("SELECT * FROM movimientos", conn)

    if not df.empty:
        # KPIs Principales
        ingresos = df[df['tipo'] == "Factura Emitida (Venta)"]['total'].sum()
        gastos = df[df['tipo'] != "Factura Emitida (Venta)"]['total'].sum()
        beneficio = ingresos - gastos
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos Totales", f"{ingresos:,.2f}€")
        c2.metric("Gastos Totales", f"{gastos:,.2f}€")
        c3.metric("Beneficio Neto", f"{beneficio:,.2f}€", delta=f"{beneficio:,.2f}€")

        # NUEVO: Gráfico de Comparación
        st.write("### Visualización de Rendimiento")
        df_chart = pd.DataFrame({
            "Categoría": ["Ingresos", "Gastos"],
            "Monto": [ingresos, gastos]
        })
        fig = px.bar(df_chart, x="Categoría", y="Monto", color="Categoría", 
                     color_discrete_map={"Ingresos": "#2ecc71", "Gastos": "#e74c3c"})
        st.plotly_chart(fig, use_container_width=True)

        st.write("### Historial de Movimientos")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        
        if st.button("Cerrar Sesión"):
            st.session_state["authenticated"] = False
            st.rerun()
    else:
        st.info("Añade tu primer movimiento para ver las estadísticas.")
