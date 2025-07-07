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
    st.image("https://i0.wp.com/tekpro.com.co/wp-content/uploads/2023/12/cropped-logo-tekpro-main-retina.png?fit=522%2C145&ssl=1", width=100)  # logo desde URL

st.markdown("---")

# =============================
# FORMULARIO DE USO
# =============================
st.subheader(" Ingreso diario de uso")

with st.form("registro_form"):
    empresa = st.text_input("Nombre de la empresa")
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", value=date.today())
    with col2:
        horas = st.number_input("Horas de uso", min_value=0.0, step=0.5)
    partes = st.multiselect("Partes cambiadas hoy", list(VIDA_UTIL.keys()))
    observaciones = st.text_area("Observaciones")

    enviar = st.form_submit_button("Guardar registro")
    if enviar:
        if empresa.strip() == "":
            st.warning("⚠️ Por favor ingresa el nombre de la empresa.")
        else:
            fila = [empresa, str(fecha), horas, ";".join(partes), observaciones]
            sheet.append_row(fila)
            st.success("✅ Registro guardado exitosamente.")

# =============================
# ESTADO DE COMPONENTES
# =============================
st.subheader(":gear: Estado actual de las partes")

# Cargar datos
data = pd.DataFrame(sheet.get_all_records())
estado_partes = {parte: 0 for parte in VIDA_UTIL}

for _, fila in data.iterrows():
    horas_dia = fila["Horas de uso"]
    cambiadas = fila["Partes cambiadas"].split(";") if fila["Partes cambiadas"] else []
    for parte in VIDA_UTIL:
        if parte in cambiadas:
            estado_partes[parte] = 0
        else:
            estado_partes[parte] += horas_dia

# Mostrar estados
for parte, usadas in estado_partes.items():
    limite = VIDA_UTIL[parte]
    restantes = limite - usadas
    if restantes <= 24:
        color, estado = "⚠️", "Falla esperada"
    elif restantes <= 192:
        color, estado = "🔴", "Crítico"
    elif restantes <= 360:
        color, estado = "🔹", "Advertencia"
    else:
        color, estado = "🔵", "Bueno"
    st.markdown(f"{color} **{parte}**: {usadas:.1f} / {limite} h | Estado: `{estado}`")

# =============================
# HISTORIAL
# =============================
with st.expander(":scroll: Ver historial de registros"):
    st.dataframe(data, use_container_width=True)
