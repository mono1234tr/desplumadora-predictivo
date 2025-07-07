import streamlit as st
import pandas as pd
from datetime import date
import gspread
import json
from google.oauth2.service_account import Credentials

# ID de la hoja de Google Sheets
SHEET_ID = "1288rxOwtZDI3A7kuLnR4AXaI-GKt6YizeZS_4ZvdTnQ"
SHEET_NAME = "Hoja 1"  # Asegúrate que la hoja se llame así o cámbialo aquí

# Autenticación con Google Sheets
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
service_account_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    
# Definir vida útil por parte (en horas)
VIDA_UTIL = {
    "Dedos de goma": 720,
    "Platos porta dedos": 2160,
    "Bucines": 1440,
    "Bandas planas": 2880,
    "Motores": 25920,
}

# Título
st.title(" Mantenimiento Predictivo - Desplumadora TEKPRO")

# ======================
# Ingreso de datos
# ======================
st.header(" Ingreso diario de uso")

empresa = st.text_input("Nombre de la empresa")
fecha = st.date_input("Fecha", value=date.today())
horas = st.number_input("Horas de uso", min_value=0.0, step=0.5)
partes = st.multiselect("Partes cambiadas hoy", list(VIDA_UTIL.keys()))
observaciones = st.text_area("Observaciones")

if st.button("Guardar registro"):
    if empresa.strip() == "":
        st.warning("⚠️ Por favor ingresa el nombre de la empresa antes de guardar.")
    else:
        fila = [empresa, str(fecha), horas, ";".join(partes), observaciones]
        sheet.append_row(fila)
        st.success("✅ Registro guardado exitosamente.")

# ======================
# Estado de componentes
# ======================
st.header("🔧 Estado actual de las partes")

# Leer todos los registros desde la hoja
data = pd.DataFrame(sheet.get_all_records())

# Inicializar horas acumuladas
estado_partes = {parte: 0 for parte in VIDA_UTIL}

# Procesar historial para calcular uso acumulado
for _, fila in data.iterrows():
    horas_dia = fila["Horas de uso"]
    cambiadas = fila["Partes cambiadas"].split(";") if fila["Partes cambiadas"] else []
    for parte in VIDA_UTIL:
        if parte in cambiadas:
            estado_partes[parte] = 0  # Reiniciar contador si fue cambiada
        else:
            estado_partes[parte] += horas_dia


# Mostrar estado de cada componente
# Mostrar estado de cada componente basado en horas restantes
for parte, usadas in estado_partes.items():
    limite = VIDA_UTIL[parte]
    horas_restantes = limite - usadas

    if horas_restantes <= 0:
        color = "🔴"
        estado = "Falla esperada"
    elif horas_restantes <= 192:
        color = "🔴"
        estado = "Crítico"
    elif horas_restantes <= 360:
        color = "🟡"
        estado = "Advertencia"
    else:
        color = "🟢"
        estado = "Bueno"

    st.write(f"{color} **{parte}** — {usadas:.1f} / {limite} horas  | Estado: {estado}")


# ======================
# Historial completo
# ======================
with st.expander("📜 Ver historial de registros"):
    st.dataframe(data)
