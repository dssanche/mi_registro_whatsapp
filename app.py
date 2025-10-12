from flask import Flask, request, redirect, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACIÓN GOOGLE SHEETS ---
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "creds.json"
SPREADSHEET_ID = "1pLwMJlZpaUTwTaXBEZJK_9dGoUecP1UJt2b3ylDpZac"

creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

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
