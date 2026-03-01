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
    .result-box {
        background-color: #f1f8ff; padding: 20px; border-radius: 10px;
        border: 1px solid #c8e1ff; margin-bottom: 20px;
    }
    .verify-ok { color: #28a745; font-weight: bold; font-size: 1.2em; }
    .verify-fail { color: #dc3545; font-weight: bold; font-size: 1.2em; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado con Logo
if os.path.exists("Logo.png"):
    st.image("Logo.png", width=350)

st.title("🪟 Resistencia a Carga de Baranda (OGUC)")
st.caption("Verificación de Travesaños según Art. 4.2.7 | Proyectos Estructurales EIRL")

# =================================================================
# 2. PARÁMETROS DE ENTRADA (SIDEBAR)
# =================================================================
st.sidebar.header("📐 Geometría y Carga")
largo_travesano = st.sidebar.number_input("Largo de Travesaño (mm)", value=1500.0)
h_inferior = st.sidebar.number_input("Altura Inferior Ventana (mm)", value=500.0)
h_antepecho = st.sidebar.number_input("Altura de Antepecho (mm)", value=450.0)
carga_baranda = st.sidebar.radio("Carga de Baranda (kgf/m)", [50, 100], index=0)

material = st.sidebar.selectbox("Seleccione Material", [
    "Acero A270ES (Fy=270 MPa)",
    "Acero A240ES (Fy=240 MPa)",
    "Acero ASTM A36 (Fy=248 MPa)",
    "Aluminio AA6063-T6 (Fy=170 MPa)",
    "Aluminio AA6063-T5 (Fy=110 MPa)"
])

# =================================================================
# 3. MOTOR DE CÁLCULO
# =================================================================
if "Aluminio" in material:
    E = 7000000000.0 
    ny = 1.65
    Fy = 17000000.0 if "T6" in material else 11249113.3
else:
    E = 20394324259.6
    ny = 1.667
    if "A270" in material: Fy = 27000000.0
    elif "A240" in material: Fy = 24000000.0
    else: Fy = 25310504.9

Lt_m = largo_travesano / 1000
def_adm = (Lt_m / 240) + (6.35 / 1000) if Lt_m > 4.115 else (Lt_m / 175)
altura_total = h_inferior + h_antepecho
sometido = altura_total <= 950

Ixx_req = (5 / 384) * (carga_baranda * Lt_m**4) / (E * def_adm) * 10**8 if sometido else 0.0
Wxx_req = ((carga_baranda * Lt_m**2) / 8) / (Fy / ny) * 10**6 if sometido else 0.0

# =================================================================
# 4. DESPLIEGUE DE RESULTADOS E IMAGEN (FIX)
# =================================================================
col_datos, col_img = st.columns([1.5, 1])

with col_datos:
    st.subheader("🔍 Verificación del Perfil Propuesto")
    c1, c2 = st.columns(2)
    ixx_prop = c1.number_input("Inercia Propuesta Ixx (cm4)", value=2.0, format="%.3f")
    wxx_prop = c2.number_input("Módulo Propuesto Wxx (cm3)", value=1.5, format="%.3f")

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    if not sometido:
        st.warning("⚠️ No requiere verificar carga de baranda (> 950 mm).")
    else:
        st.write(f"**Requerimientos (Carga {carga_baranda} kgf/m):**")
        st.write(f"• Inercia Mínima: **{Ixx_req:.3f} cm⁴**")
        st.write(f"• Módulo Mínimo: **{Wxx_req:.3f} cm³**")
        
        cumple_i = ixx_prop >= Ixx_req
        cumple_w = wxx_prop >= Wxx_req
        
        st.divider()
        st.markdown(f"Validación Inercia: <span class='{'verify-ok' if cumple_i else 'verify-fail'}'>{'✅ CUMPLE' if cumple_i else '❌ NO CUMPLE'}</span>", unsafe_allow_html=True)
        st.markdown(f"Validación Módulo: <span class='{'verify-ok' if cumple_w else 'verify-fail'}'>{'✅ CUMPLE' if cumple_w else '❌ NO CUMPLE'}</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_img:
    # AQUÍ SE CARGA LA IMAGEN AL FINAL DE LOS RESULTADOS
    if os.path.exists("Ventana.png"):
        st.image("Ventana.png", caption="Esquema de Carga en Travesaño", width=300)
    else:
        st.error("Archivo 'Ventana.png' no encontrado en el repositorio.")

# =================================================================
# 5. GENERACIÓN DE PDF
# =================================================================
def generar_pdf():
    pdf = FPDF(orientation='L', unit='mm', format='Letter')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "DECLARACIÓN DE RESISTENCIA DE TRAVESAÑOS", ln=True, align='C')
    if os.path.exists("Ventana.png"):
        pdf.image("Ventana.png", x=210, y=140, w=45)
    return pdf.output()

# Botón Sidebar
if st.sidebar.button("📄 Descargar Certificado PDF"):
    if ixx_prop >= Ixx_req and wxx_prop >= Wxx_req:
        pdf_bytes = generar_pdf()
        b64 = base64.b64encode(pdf_bytes).decode()
        st.sidebar.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Certificado.pdf" style="text-decoration:none;"><div style="background-color:#003366;color:white;padding:10px;border-radius:5px;text-align:center;">📥 OBTENER PDF</div></a>', unsafe_allow_html=True)
    else:
        st.sidebar.error("El perfil no cumple.")