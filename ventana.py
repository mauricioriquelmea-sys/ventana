# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import base64
import os
from fpdf import FPDF
from datetime import datetime

# =================================================================
# 1. CONFIGURACIÓN Y ESTILO CORPORATIVO
# =================================================================
st.set_page_config(page_title="Carga de Baranda | Proyectos Estructurales", layout="wide")

st.markdown("""
    <style>
    .main-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: #003366; color: white !important; padding: 12px;
        text-decoration: none; border-radius: 8px; font-weight: bold; width: 100%;
    }
    .result-box {
        background-color: #f8f9fa; padding: 20px; border-radius: 10px;
        border-left: 5px solid #003366; margin-top: 20px;
    }
    .verify-ok { color: #28a745; font-weight: bold; }
    .verify-fail { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("Logo.png"):
    with open("Logo.png", "rb") as f:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" width="350"></div>', unsafe_allow_html=True)

st.title("🪟 Resistencia a Carga de Baranda (OGUC)")
st.caption("Verificación de Travesaños de Ventana | Proyectos Estructurales EIRL")

# =================================================================
# 2. PARÁMETROS DE ENTRADA (SIDEBAR)
# =================================================================
st.sidebar.header("⚙️ Configuración del Proyecto")
proyecto_txt = st.sidebar.text_input("Nombre del Proyecto", "Edificio Veka")
ventana_txt = st.sidebar.text_input("Código de Ventana", "V01")

st.sidebar.header("📐 Geometría y Carga")
largo_travesano = st.sidebar.number_input("Largo de Travesaño (mm)", value=1500.0)
h_inferior = st.sidebar.number_input("Altura Inferior Ventana (mm)", value=500.0)
h_antepecho = st.sidebar.number_input("Altura de Antepecho (mm)", value=450.0)

carga_baranda = st.sidebar.radio("Carga de Baranda (kgf/m)", [50, 100], index=1)

st.sidebar.header("🛠️ Material del Perfil")
material = st.sidebar.selectbox("Seleccione Material", [
    "Acero A270ES (Fy=270 MPa)",
    "Acero A240ES (Fy=240 MPa)",
    "Acero ASTM A36 (Fy=248 MPa)",
    "Aluminio AA6063-T5 (Fy=110 MPa)"
])

# =================================================================
# 3. MOTOR DE CÁLCULO (Lógica Veka portabilidad)
# =================================================================

# Propiedades de materiales (E, Fy, ny)
if "Aluminio" in material:
    E = 7138013490.8 / 10.197 * 10  # Ajuste a N/m2 -> kgf/m2
    Fy = 11249113.3
    ny = 1.65
else:
    E = 20394324259.6
    ny = 1.667
    if "A270" in material: Fy = 27000000.0
    elif "A240" in material: Fy = 24000000.0
    else: Fy = 25310504.9

# Cálculo de deflexión admisible (L/175 o L/240 + 6.35)
Lt_m = largo_travesano / 1000
if Lt_m > 4.115:
    def_adm = (Lt_m / 240) + (6.35 / 1000)
    def_label = "L/240 + 6.35"
else:
    def_adm = (Lt_m / 175)
    def_label = "L/175"

# Verificación de altura (OGUC especifica carga hasta 95cm de altura)
altura_total = h_inferior + h_antepecho
sometido_a_baranda = altura_total <= 950

if sometido_a_baranda:
    # Inercia Necesaria (Ixx) [cm4]
    Ixx_req = (5 / 384) * (carga_baranda * Lt_m**4) / (E * def_adm) * 10**8
    # Módulo Resistente (Wxx) [cm3]
    Wxx_req = ((carga_baranda * Lt_m**2) / 8) / (Fy / ny) * 10**6
else:
    Ixx_req = 0.0
    Wxx_req = 0.0

# Ingreso de propiedades del perfil real para verificar
st.subheader("🔍 Verificación de Perfil Propuesto")
col1, col2 = st.columns(2)
with col1:
    ixx_prop = st.number_input("Inercia Propuesta Ixx (cm4)", value=2.0, format="%.3f")
with col2:
    wxx_prop = st.number_input("Módulo Propuesto Wxx (cm3)", value=1.5, format="%.3f")

# Lógica de Validación
cumple_i = ixx_prop >= Ixx_req if sometido_a_baranda else True
cumple_w = wxx_prop >= Wxx_req if sometido_a_baranda else True
todo_ok = cumple_i and cumple_w

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS
# =================================================================
st.markdown('<div class="result-box">', unsafe_allow_html=True)
if not sometido_a_baranda:
    st.warning("⚠️ El travesaño no está sometido a carga de baranda (altura > 950 mm).")
else:
    st.write(f"**Requerimientos Mecánicos (Carga {carga_baranda} kgf/m):**")
    st.write(f"- Inercia Mínima ($I_{{xx}}$): **{Ixx_req:.3f} cm⁴**")
    st.write(f"- Módulo Mínimo ($W_{{xx}}$): **{Wxx_req:.3f} cm³**")
    st.write(f"- Deflexión Admisible: **{def_adm*1000:.2f} mm** ({def_label})")
    
    st.divider()
    res_i = "✅ CUMPLE" if cumple_i else "❌ NO CUMPLE"
    res_w = "✅ CUMPLE" if cumple_w else "❌ NO CUMPLE"
    st.markdown(f"Validación Inercia: <span class='{'verify-ok' if cumple_i else 'verify-fail'}'>{res_i}</span>", unsafe_allow_html=True)
    st.markdown(f"Validación Módulo: <span class='{'verify-ok' if cumple_w else 'verify-fail'}'>{res_w}</span>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# =================================================================
# 5. GENERACIÓN DE DECLARACIÓN PDF
# =================================================================
def generar_pdf_declaracion():
    pdf = FPDF(orientation='L', unit='mm', format='Letter')
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Courier", 'B', 16)
    pdf.cell(0, 10, "DECLARACION DE RESISTENCIA DE TRAVESAÑOS", ln=True, align='C')
    pdf.line(20, 25, 260, 25)
    pdf.ln(15)
    
    pdf.set_font("Courier", '', 12)
    pdf.multi_cell(0, 10, f"EMPRESA PROVEEDORA DE LAS VENTANAS SEGÚN LA SIGUIENTE REFERENCIA:\n\nPROYECTO: {proyecto_txt.upper()}\nVENTANA: {ventana_txt.upper()}")
    pdf.ln(10)
    
    tipo_zona = "PRIVADAS (50 kgf/m)" if carga_baranda == 50 else "PÚBLICAS (100 kgf/m)"
    texto_legal = (
        f"DECLARA QUE LOS TRAVESAÑOS DE LA VENTANA CUMPLEN CON LA SOBRECARGA DE BARANDAS "
        f"ESPECIFICADA EN EL ARTÍCULO 4.2.7 DE LA ORDENANZA GENERAL DE URBANISMO Y CONSTRUCCIONES "
        f"PARA ZONAS {tipo_zona}, ES DECIR, RESISTEN UNA SOBRECARGA HORIZONTAL APLICADA EN CUALQUIER "
        f"PUNTO DE SU ESTRUCTURA HASTA LOS 95 CM DE ALTURA."
    )
    pdf.multi_cell(0, 8, texto_legal)
    
    pdf.ln(20)
    pdf.set_font("Courier", 'I', 10)
    pdf.cell(0, 5, f"Documento elaborado por: {proyecto_txt}", ln=True)
    pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    
    return pdf.output()

st.sidebar.markdown("---")
if todo_ok:
    if st.sidebar.button("📄 Generar Declaración PDF"):
        pdf_bytes = generar_pdf_declaracion()
        b64 = base64.b64encode(pdf_bytes).decode()
        st.sidebar.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Declaracion_Baranda.pdf" class="main-btn">📥 Descargar Declaración</a>', unsafe_allow_html=True)
else:
    st.sidebar.error("⚠️ El perfil no cumple. No se puede generar declaración.")