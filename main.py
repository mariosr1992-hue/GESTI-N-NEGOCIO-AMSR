import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Gestor de Negocio", layout="wide")

# Conexión a Base de Datos
conn = sqlite3.connect('datos_negocio.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS movimientos
             (fecha TEXT, tipo TEXT, concepto TEXT, total REAL, iva REAL, metodo TEXT, estado TEXT)''')
conn.commit()

st.title("📊 Control de Beneficios Reales")

# BARRA LATERAL - ENTRADA DE DATOS
with st.sidebar:
    st.header("📝 Registrar Nuevo Dato")
    with st.form("formulario"):
        tipo = st.selectbox("Categoría", ["Factura Emitida (Venta)", "Factura Recibida (Gasto)", "Nómina", "Seguridad Social", "Impuestos (Trimestre)"])
        concepto = st.text_input("Detalle (Ej: Cliente X, Alquiler, IRPF)")
        monto = st.number_input("Importe Total (€)", min_value=0.0, step=0.01)
        metodo = st.radio("Método", ["Banco", "Efectivo (Metálico)"])
        estado = st.selectbox("Estado", ["Abonado/Cobrado", "Pendiente"])
        
        # Lógica de IVA
        if "Factura" in tipo:
            iva_opcion = st.selectbox("IVA Aplicado", [21, 10, 4, 0])
            base_imponible = monto / (1 + iva_opcion/100)
            iva_valor = monto - base_imponible
        else:
            iva_valor = 0.0 # Nóminas e impuestos no llevan IVA desglosado aquí
            
        enviado = st.form_submit_button("Guardar en la Nube")
        
        if enviado:
            c.execute("INSERT INTO movimientos VALUES (?,?,?,?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d"), tipo, concepto, monto, iva_valor, metodo, estado))
            conn.commit()
            st.success("¡Guardado!")

# CUERPO PRINCIPAL - CÁLCULOS
df = pd.read_sql_query("SELECT * FROM movimientos", conn)

if not df.empty:
    # Cálculos Inteligentes
    ventas_cobradas = df[(df['tipo'] == "Factura Emitida (Venta)") & (df['estado'] == "Abonado/Cobrado")]['total'].sum()
    iva_repercutido = df[df['tipo'] == "Factura Emitida (Venta)"]['iva'].sum()
    iva_soportado = df[df['tipo'] == "Factura Recibida (Gasto)"]['iva'].sum()
    
    gastos_totales = df[df['tipo'] != "Factura Emitida (Venta)"]['total'].sum()
    
    beneficio_real = ventas_cobradas - gastos_totales - (iva_repercutido - iva_soportado)

    # Visualización de KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas Cobradas", f"{ventas_cobradas:,.2f}€")
    c2.metric("Gastos (con Nóminas)", f"{gastos_totales:,.2f}€")
    c3.metric("IVA a Liquidar", f"{(iva_repercutido - iva_soportado):,.2f}€", delta_color="inverse")
    c4.metric("BENEFICIO REAL NETO", f"{beneficio_real:,.2f}€")

    st.write("### Historial Completo")
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
else:
    st.info("La base de datos está vacía. Empieza registrando algo en el menú de la izquierda.")
