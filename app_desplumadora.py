import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
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

# Lista de equipos con códigos, OPs y descripciones
EQUIPO_INFO = {
    "EF301": {"op": "7883 - 10", "descripcion": "LAVADORA DE POLLOS 0.6 MT 1 PASO"},
    "EF158": {"op": "7883 - 15", "descripcion": "CANAL DE SANGRADO DE 4.0 MT DE UN PASO"},
    "RF771": {"op": "7883 - 4", "descripcion": "BARRA ESTABILIZADORA EN SACRIFICIO DE 1MT"},
    "RF745": {"op": "7883 - 2", "descripcion": "ESQUINERO PISTA T INOX 180° ESCALDADORA RUEDA DENTADA"},
    "EF603": {"op": "7883 - 5", "descripcion": "BANDA TRANQUILIZADORA EN SACRIFICIO DE 8 MT"},
    "RF364": {"op": "7883 - 6", "descripcion": "BARRA ESTABILIZADORA DE GANCHOS CANAL EVISCERACION D"},
    "RF958": {"op": "7883 - 22", "descripcion": "ESQUINERO INOX 90 PISTA EN T RL DENTADA Z18"},
    "EF266": {"op": "7883 - 9", "descripcion": "CANAL DE EVISCERACION DE 7.0 MTS DE 1 PASO"},
    "EF083": {"op": "7883 - 11", "descripcion": "PELADORA MOLLEJAS 1 PUESTO 2 RODILLOS CON MESA"},
    "EF230": {"op": "7883 - 12", "descripcion": "DESCOLGADOR DE POLLOS A 180 GRADOS"},
    "EF360": {"op": "7883 - 23", "descripcion": "UNIDAD MOTRIZ A 180 EN PISTA EN T INOX CON PIÑON Z25"},
    "RF041": {"op": "7883 - 3", "descripcion": "CURVA DE ASCENSO Y DESCENSO PISTA T INOX"},
    "EF001": {"op": "7883 - 7", "descripcion": "ATURDIDOR DE FRECUENCIA VARIABLE DE 0.80MT SOPORTE A F"},
    "EF778": {"op": "7883 - 8", "descripcion": "DESPLUMADORA CENTRIFUGA DCT100"},
    "EF1013": {"op": "7883 - 13", "descripcion": "PRECHILLER DE ROTACION CON EVACUACION INDEPENDIENTE"},
    "EF1048": {"op": "7883 - 14", "descripcion": "ESTRUCTURA DE SOPORTE INOX PARA LOS TRANSPORTADORES"},
    "EF827": {"op": "7883 - 16", "descripcion": "CHILLER ESPIRAL MODELO CHS 311M EVACUACION INDEPENDIENTE"},
    "EF970": {"op": "7883 - 17", "descripcion": "ESCALDADORA CON QUEMADOR ACPM Y VAPOR DE DOS PASOS"},
    "RF797": {"op": "7883 - 21", "descripcion": "BARRA ESTABILIZADORA DE GANCHOS INOX EN COLGADO DE 1"},
    "EF1050": {"op": "7883 - 18", "descripcion": "MESA DE EMPAQUE CON 2 EMBUDOS DE 1.2MT LARGO X 0.8 MT"},
    "EF1051": {"op": "7883 - 19", "descripcion": "SISTEMA DE RECIRCULACION DE AGUA DE CHILLER A PRECHILL"},
    "RF915": {"op": "7883 - 20", "descripcion": "ESQUINERO 180 PISTA EN T INOX CON RL Z18"}
}

CODIGOS_EQUIPO = list(EQUIPO_INFO.keys())
EQUIPOS = {codigo: [f"Consumible A ({codigo})", f"Consumible B ({codigo})"] for codigo in CODIGOS_EQUIPO}
VIDA_UTIL = {consumible: 700 for sub in EQUIPOS.values() for consumible in sub}

st.set_page_config(page_title="Granja Azul - Mantenimiento Predictivo", layout="wide")

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("""
    <h1 style='color:#1f77b4;'> Mantenimiento Predictivo - Granja Azul</h1>
    """, unsafe_allow_html=True)

with col2:
    st.image("https://pbs.twimg.com/profile_images/1487153447061368833/H5EKoCGk_400x400.jpg", width=300)

st.markdown("---")

# HORAS DE TRABAJO GLOBALES
st.subheader("Configuración global de horas trabajadas")
colh1, colh2 = st.columns(2)
with colh1:
    hora_inicio_global = st.time_input("Hora de inicio global", value=datetime.strptime("08:00", "%H:%M").time(), key="inicio_global")
with colh2:
    hora_fin_global = st.time_input("Hora de finalización global", value=datetime.strptime("17:00", "%H:%M").time(), key="fin_global")

inicio_global = datetime.combine(date.today(), hora_inicio_global)
fin_global = datetime.combine(date.today(), hora_fin_global)
if fin_global < inicio_global:
    fin_global += timedelta(days=1)
HORAS_GLOBALES = (fin_global - inicio_global).total_seconds() / 3600

# SELECCIÓN DEL EQUIPO
st.subheader("Selecciona el código del equipo")
selector_visible = [f"{cod} - {info['descripcion']}" for cod, info in EQUIPO_INFO.items()]
selector_mapa = {f"{cod} - {info['descripcion']}": cod for cod, info in EQUIPO_INFO.items()}
seleccion = st.selectbox("Código del equipo - Descripción", selector_visible)
codigo = selector_mapa[seleccion]
info = EQUIPO_INFO[codigo]
consumibles_equipo = EQUIPOS[codigo]

# FORMULARIO
st.subheader(" Ingreso diario de uso")
EMPRESA = "Granja Azul"

with st.form("registro_form"):
    fecha = st.date_input("Fecha", value=date.today())
    op = st.text_input("Orden de producción (OP)", value=info["op"])
    partes = st.multiselect("Partes cambiadas hoy", consumibles_equipo)
    observaciones = st.text_area("Observaciones técnicas")

    if st.form_submit_button("Guardar registro"):
        fila = [EMPRESA, str(fecha), op, codigo, info["descripcion"], HORAS_GLOBALES, ";".join(partes), observaciones]
        sheet.append_row(fila)
        st.success(f"✅ Registro guardado exitosamente para equipo {codigo}. Total horas: {HORAS_GLOBALES:.2f}")

# ESTADO DE CONSUMIBLES
st.subheader(" Estado de consumibles por equipo")
data = pd.DataFrame(sheet.get_all_records())
data.columns = [col.lower().strip() for col in data.columns]  # normaliza nombres de columnas

data = data[data["empresa"] == EMPRESA] if "empresa" in data.columns else pd.DataFrame()
data_equipo = data[data["codigo"] == codigo] if "codigo" in data.columns else pd.DataFrame()

estado_partes = {parte: 0 for parte in EQUIPOS[codigo]}
for _, fila in data_equipo.iterrows():
    horas_dia = fila.get("hora de uso", fila.get("horas de uso", 0))

    partes_str = str(fila.get("parte cambiada", "")).strip()
    cambiadas = partes_str.split(";") if partes_str else []

    for parte in estado_partes:
        if parte in cambiadas:
            estado_partes[parte] = 0
        else:
            estado_partes[parte] += horas_dia

for parte, usadas in estado_partes.items():
    limite = VIDA_UTIL.get(parte, 700)
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

# HISTORIAL
with st.expander(" Ver historial de registros por equipo"):
    if not data_equipo.empty:
        st.dataframe(data_equipo, use_container_width=True)
    else:
        st.write("No hay registros para mostrar.")
