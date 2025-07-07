# app_desplumadora.py (con mejoras visuales y personalización azul claro)

import streamlit as st
import pandas as pd
from datetime import date
import json
from google.oauth2.service_account import Credentials
import gspread

# Leer credenciales desde secrets
service_account_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
client = gspread.authorize(creds)

# Google Sheet ID y hoja
SHEET_ID = "1288rxOwtZDI3A7kuLnR4AXaI-GKt6YizeZS_4ZvdTnQ"
SHEET_NAME = "Hoja 1"
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Vida útil por parte
VIDA_UTIL = {
    "Dedos de goma": 720,
    "Platos porta dedos": 2160,
    "Bucines": 1440,
    "Bandas planas": 2880,
    "Motores": 25920,
}

# =============================
# ESTILOS Y ENCABEZADO
# =============================
st.set_page_config(page_title="Desplumadora Predictiva", layout="wide")

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("""
    <h1 style='color:#1f77b4;'> Mantenimiento Predictivo - Desplumadora TEKPRO</h1>
    """, unsafe_allow_html=True)

with col2:
    st.image("https://pbs.twimg.com/profile_images/1487153447061368833/H5EKoCGk_400x400.jpg", width=100)  # logo desde URL

st.markdown("---")

# =============================
# FORMULARIO DE USO
# =============================
st.subheader("Ingreso diario de uso")

EMPRESAS = ["Paulandia", "Pollocoa", "Granja Azul", "Avícola Chone"]

with st.form("registro_form"):
    empresa = st.selectbox("Nombre de la empresa", EMPRESAS)
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", value=date.today())
    with col2:
        horas = st.number_input("Horas de uso", min_value=0.0, step=0.5)
    partes = st.multiselect("Partes cambiadas hoy", list(VIDA_UTIL.keys()))
    observaciones = st.text_area("Observaciones")

    enviar = st.form_submit_button("Guardar registro")
    if enviar:
        fila = [empresa, str(fecha), horas, ";".join(partes), observaciones]
        sheet.append_row(fila)
        st.success("✅ Registro guardado exitosamente.")

# =============================
# ESTADO DE COMPONENTES POR EMPRESA
# =============================
st.subheader(":factory: Estado actual por empresa")

empresa_seleccionada = st.selectbox("Selecciona una empresa para ver su estado", EMPRESAS)

# Cargar datos y filtrar por empresa seleccionada
data = pd.DataFrame(sheet.get_all_records())

estado_partes = {parte: 0 for parte in VIDA_UTIL}

if not data.empty and "empresa" in data.columns:
    data_empresa = data[data["empresa"] == empresa_seleccionada]

    for _, fila in data_empresa.iterrows():
        horas_dia = fila["Horas de uso"]
        cambiadas = fila["Partes cambiadas"].split(";") if fila["Partes cambiadas"] else []
        for parte in VIDA_UTIL:
            if parte in cambiadas:
                estado_partes[parte] = 0
            else:
                estado_partes[parte] += horas_dia
else:
    st.info(" No hay datos registrados aún. Mostrando horas en 0.")

# Mostrar estados por empresa
for parte, usadas in estado_partes.items():
    limite = VIDA_UTIL[parte]
    restantes = limite - usadas
    if restantes <= 24:
        color, estado = "⚠️", "Falla esperada"
    elif restantes <= 192:
        color, estado = "🔴", "Crítico"
    elif restantes <= 360:
        color, estado = "🟡", "Advertencia"
    else:
        color, estado = "🟢", "Bueno"
    st.markdown(f"{color} **{parte}**: {usadas:.1f} h | Estado: `{estado}`")

# =============================
# HISTORIAL FILTRADO
# =============================
with st.expander(" Ver historial de registros por empresa"):
    if not data.empty and "empresa" in data.columns:
        st.dataframe(data[data["empresa"] == empresa_seleccionada], use_container_width=True)
    else:
        st.write("No hay registros para mostrar.")
