from flask import Flask, request, redirect, render_template, send_file
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import qrcode
from io import BytesIO
import os
import json

app = Flask(__name__)

# --- CONFIGURACIÓN GOOGLE SHEETS ---
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
SPREADSHEET_ID = "1pLwMJlZpaUTwTaXBEZJK_9dGoUecP1UJt2b3ylDpZac"

# CONFIGURACIÓN SEGURA - Sin archivo creds.json
def get_google_credentials():
    # Opción 1: Variables de entorno (para producción)
    if all(key in os.environ for key in ['GCP_TYPE', 'GCP_PROJECT_ID', 'GCP_PRIVATE_KEY']):
        service_account_info = {
            "type": os.environ['GCP_TYPE'],
            "project_id": os.environ['GCP_PROJECT_ID'],
            "private_key_id": os.environ['GCP_PRIVATE_KEY_ID'],
            "private_key": os.environ['GCP_PRIVATE_KEY'].replace('\\n', '\n'),
            "client_email": os.environ['GCP_CLIENT_EMAIL'],
            "client_id": os.environ['GCP_CLIENT_ID'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ['GCP_CLIENT_X509_CERT_URL'],
            "universe_domain": "googleapis.com"
        }
        return ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, SCOPE)
    
    # Opción 2: Archivo local (solo desarrollo)
    elif os.path.exists("creds.json"):
        return ServiceAccountCredentials.from_json_keyfile_name("creds.json", SCOPE)
    
    else:
        raise Exception("No se encontraron credenciales de Google Cloud")

# Inicializar cliente de Google Sheets
try:
    creds = get_google_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
except Exception as e:
    print(f"Error inicializando Google Sheets: {e}")
    sheet = None

WHATSAPP_GROUP_LINK = "https://chat.whatsapp.com/BlXfChwXszFHroaBEUDnw8"


@app.route('/')
def index():
    return render_template('registro.html')

@app.route('/registro', methods=['POST'])
def registro():
    nombre = request.form.get('nombre')
    telefono = request.form.get('telefono')
    edad = request.form.get('edad')
    nacimiento = request.form.get('nacimiento')
    lider = request.form.get('lider')
    fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fila = [nombre, telefono, edad, nacimiento, lider, fecha_registro]
    sheet.append_row(fila, value_input_option="USER_ENTERED")

    return redirect(WHATSAPP_GROUP_LINK)

if __name__ == '__main__':
    app.run(debug=True)
