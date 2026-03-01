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
        background-color: #f1f8ff; padding: 20px; border-radius: 10px;
        border: 1px solid #c8e1ff; margin-top: 20px;
    }
    .verify-ok { color: #28a745; font-weight: bold; font-size: 1.2em; }
    .verify-fail { color: #dc3545; font-weight: bold; font-size: 1.2em; }
    .stNumberInput input { color: #003366 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("Logo.png"):
    with open("Logo.png", "rb") as f:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" width="350"></div>', unsafe_allow_html=True)

st.title("🪟 Resistencia a Carga de Baranda (OGUC)")
st.caption("Verificación de Travesaños según Art. 4.2.7 | Proyectos Estructurales EIRL")

# =================================================================
# 2. PARÁMETROS DE ENTRADA (SIDEBAR)
# =================================================================
st.sidebar.header("📐 Geometría y Carga")
largo_travesano = st.sidebar.number_input("Largo de Travesaño (mm)", value=1500.0)
h_inferior = st.sidebar.number_input("Altura Inferior Ventana (mm)", value=500.0)
h_antepecho = st.sidebar.number_input("Altura de Antepecho (mm)", value=450.0)

# Carga por defecto en 50 kgf/m para asegurar cumplimiento inicial
carga_baranda = st.sidebar.radio("Carga de Baranda (kgf/m)", [50, 100], index=0)

st.sidebar.header("🛠️ Material del Perfil")
material = st.sidebar.selectbox("Seleccione Material", [
    "Acero A270ES (Fy=270 MPa)",
    "Acero A240ES (Fy=240 MPa)",
    "Acero ASTM A36 (Fy=248 MPa)",
    "Aluminio AA6063-T6 (Fy=170 MPa)",
    "Aluminio AA6063-T5 (Fy=110 MPa)"
])

# =================================================================
# 3. MOTOR DE CÁLCULO (Lógica OGUC + Materiales)
# =================================================================

# Propiedades de materiales
if "Aluminio" in material:
    E = 7000000000.0  # kgf/m2 aprox para Aluminio
    ny = 1.65
    Fy = 17000000.0 if "T6" in material else 11249113.3
else:
    E = 20394324259.6 # kgf/m2 (Acero)
    ny = 1.667
    if "A270" in material: Fy = 27000000.0
    elif "A240" in material: Fy = 24000000.0
    else: Fy = 25310504.9

# Cálculo de deflexión admisible (Criterio Veka)
Lt_m = largo_travesano / 1000
if Lt_m > 4.115:
    def_adm = (Lt_m / 240) + (6.35 / 1000)
    def_label = "L/240 + 6.35"
else:
    def_adm = (Lt_m / 175)
    def_label = "L/175"

# Verificación de zona de carga (OGUC: hasta 950 mm de altura total)
altura_total = h_inferior + h_antepecho
sometido_a_baranda = altura_total <= 950

if sometido_a_baranda:
    Ixx_req = (5 / 384) * (carga_baranda * Lt_m**4) / (E * def_adm) * 10**8
    Wxx_req = ((carga_baranda * Lt_m**2) / 8) / (Fy / ny) * 10**6
else:
    Ixx_req, Wxx_req = 0.0, 0.0

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS Y VERIFICACIÓN
# =================================================================
col_input, col_icon = st.columns([1.5, 1])

with col_input:
    st.subheader("🔍 Verificación del Perfil Propuesto")
    c1, c2 = st.columns(2)
    with c1:
        ixx_prop = st.number_input("Inercia Propuesta Ixx (cm4)", value=2.0, format="%.3f")
    with c2:
        wxx_prop = st.number_input("Módulo Propuesto Wxx (cm3)", value=1.5, format="%.3f")

    cumple_i = ixx_prop >= Ixx_req if sometido_a_baranda else True
    cumple_w = wxx_prop >= Wxx_req if sometido_a_baranda else True
    
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    if not sometido_a_baranda:
        st.warning("⚠️ Altura total > 950 mm. Según OGUC, no requiere verificar carga de baranda.")
    else:
        st.write(f"**Requerimientos Mecánicos (Carga {carga_baranda} kgf/m):**")
        st.write(f"• Inercia Mínima: **{Ixx_req:.3f} cm⁴**")
        st.write(f"• Módulo Mínimo: **{Wxx_req:.3f} cm³**")
        st.write(f"• Deflexión Máx: **{def_adm*1000:.2f} mm** ({def_label})")
        
        st.divider()
        res_i = "✅ CUMPLE" if cumple_i else "❌ NO CUMPLE"
        res_w = "✅ CUMPLE" if cumple_w else "❌ NO CUMPLE"
        st.markdown(f"Validación Inercia: <span class='{'verify-ok' if cumple_i else 'verify-fail'}'>{res_i}</span>", unsafe_allow_html=True)
        st.markdown(f"Validación Módulo: <span class='{'verify-ok' if cumple_w else 'verify-fail'}'>{res_w}</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_icon:
    # Carga del icono de ventana al final de los resultados
    if os.path.exists("Ventana.png"):
        st.image("Ventana.png", caption="Esquema de Carga Horizontal en Travesaño", use_column_width=True)

# =================================================================
# 5. GENERACIÓN DE CERTIFICADO PDF
# =================================================================
def generar_pdf():
    pdf = FPDF(orientation='L', unit='mm', format='Letter')
    pdf.add_page()
    pdf.set_font("Courier", 'B', 16)
    pdf.cell(0, 10, "DECLARACIÓN DE RESISTENCIA DE TRAVESAÑOS", ln=True, align='C')
    pdf.line(20, 25, 260, 25)
    pdf.ln(15)
    pdf.set_font("Courier", '', 12)
    pdf.multi_cell(0, 8, f"PROYECTO: {st.sidebar.text_input('Proyecto', 'Edificio Veka').upper()}\nVENTANA: {st.sidebar.text_input('Ventana', 'V01').upper()}")
    pdf.ln(10)
    
    dec_text = (f"Se certifica que el travesaño analizado resiste una sobrecarga horizontal de "
                f"{carga_baranda} kgf/m según lo dispuesto en la OGUC Art. 4.2.7.")
    pdf.multi_cell(0, 8, dec_text)
    
    if os.path.exists("Ventana.png"):
        pdf.image("Ventana.png", x=200, y=140, w=50)
    
    return pdf.output()

st.sidebar.markdown("---")
if cumple_i and cumple_w:
    if st.sidebar.button("📄 Descargar Certificado PDF"):
        pdf_bytes = generar_pdf()
        b64 = base64.b64encode(pdf_bytes).decode()
        st.sidebar.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Certificado_Baranda.pdf" class="main-btn">📥 OBTENER PDF</a>', unsafe_allow_html=True)
else:
    st.sidebar.error("⚠️ El perfil no cumple los requisitos mínimos.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Mauricio Riquelme | 'Programming is understanding'</div>", unsafe_allow_html=True)