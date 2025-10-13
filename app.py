from flask import Flask, request, redirect, render_template, send_file
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import qrcode
from io import BytesIO
import os
import re
import requests

app = Flask(__name__)

# --- CONFIGURACIÓN MÍNIMA DE GOOGLE SHEETS ---
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    try:
        import json
        creds_json = os.environ.get('GCP_CREDENTIALS_JSON', '')
        if not creds_json:
            print("❌ No se encontró GCP_CREDENTIALS_JSON")
            return None

        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)
        return client.open_by_key("1pLwMJlZpaUTwTaXBEZJK_9dGoUecP1UJt2b3ylDpZac").sheet1
    except Exception as e:
        print(f"Error Sheets: {e}")
        return None


sheet = get_sheet()

# --- ENLACE AL GRUPO DE WHATSAPP ---
WHATSAPP_GROUP_LINK = "https://chat.whatsapp.com/BlXfChwXszFHroaBEUDnw8"

# --- LISTA DE LÍDERES ---
LIDERES = {
    "david": "David",
    "susana": "Susana",
    "alejo": "Alejo",
    "andres": "Andrés"
}


# --- LOCALIDADES DE BOGOTÁ ---
LOCALIDADES_BOGOTA = [
    "Usaquen", "Chapinero", "Santa Fe", "San Cristobal", "Usme",
    "Tunjuelito", "Bosa", "Kennedy", "Fontibon", "Engativa",
    "Suba", "Barrios Unidos", "Teusaquillo", "Los Martires",
    "Antonio Nariño", "Puente Aranda", "La Candelaria", "Rafael Uribe",
    "Ciudad Bolivar", "Sumapaz", "Otra localidad"
]

# --- FUNCIONES UTILITARIAS ---
def calcular_edad(fecha_nacimiento):
    """Calcula la edad a partir de la fecha de nacimiento"""
    try:
        nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        hoy = datetime.now()
        edad = hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
        return edad
    except:
        return None

def limpiar_texto(texto):
    """Limpia tildes, caracteres especiales y normaliza texto"""
    if not texto:
        return texto
    
    # Diccionario de reemplazo para tildes
    tildes = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ü': 'u', 'Ü': 'U', 'ñ': 'n', 'Ñ': 'N'
    }
    
    # Reemplazar tildes
    for tilde, sin_tilde in tildes.items():
        texto = texto.replace(tilde, sin_tilde)
    
    # Eliminar caracteres especiales y normalizar
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    return texto.strip().title()

def limpiar_telefono(telefono):
    """Limpia y formatea números de teléfono"""
    if not telefono:
        return telefono
    
    # Remover todo excepto números
    telefono_limpio = re.sub(r'[^\d]', '', telefono)
    
    # Si empieza con 57 (Colombia), asegurar formato
    if telefono_limpio.startswith('57') and len(telefono_limpio) > 10:
        return telefono_limpio
    elif len(telefono_limpio) == 10:  # Número colombiano sin 57
        return '57' + telefono_limpio
    else:
        return telefono_limpio

def inferir_sexo_por_nombre(nombre):
    """
    Infiere el sexo basado en el nombre usando base de datos local
    """
    if not nombre:
        return "No especificado"
    
    nombre_limpio = limpiar_texto(nombre).split()[0]  # Solo primer nombre
    
    # Base de datos local de nombres colombianos comunes
    nombres_femeninos = {
        'maria', 'luz', 'ana', 'carolina', 'andrea', 'laura', 'paula', 
        'diana', 'claudia', 'sandra', 'patricia', 'elena', 'isabel',
        'carmen', 'juliana', 'natalia', 'vanessa', 'katherine', 'gabriela',
        'susana', 'fernanda', 'valentina', 'sofia', 'camila', 'valeria',
        'daniela', 'mariana', 'alejandra', 'lina', 'monica', 'liliana',
        'catalina', 'johanna', 'yesica', 'kelly', 'wendy', 'xiomara'
    }
    
    nombres_masculinos = {
        'juan', 'carlos', 'andres', 'alejandro', 'david', 'jose', 'luis',
        'miguel', 'antonio', 'jorge', 'ricardo', 'fernando', 'daniel',
        'pablo', 'santiago', 'esteban', 'felipe', 'oscar', 'manuel',
        'alberto', 'rafael', 'eduardo', 'rodrigo', 'mario', 'victor',
        'alejo', 'camilo', 'sebastian', 'nicolas', 'christian', 'wilson',
        'alexander', 'brayan', 'cristian', 'jeison', 'jherson', 'jhon'
    }
    
    nombre_lower = nombre_limpio.lower()
    
    if nombre_lower in nombres_femeninos:
        return "Femenino"
    elif nombre_lower in nombres_masculinos:
        return "Masculino"
    else:
        return "No determinado"

def generar_mensaje_bienvenida(nombre, sexo, localidad):
    """Genera mensaje de bienvenida personalizado"""
    if sexo == "Femenino":
        saludo = f"¡Bienvenida {nombre}!"
    elif sexo == "Masculino":
        saludo = f"¡Bienvenido {nombre}!"
    else:
        saludo = f"¡Bienvenid@ {nombre}!"
    
    return f"{saludo} Nos alegra tener alguien más de {localidad} en nuestra comunidad 🎯"

# URL base - se actualizará automáticamente en producción
def get_base_url():
    if 'RENDER_EXTERNAL_URL' in os.environ:
        return os.environ['RENDER_EXTERNAL_URL']
    else:
        return request.url_root.rstrip('/')
# --- RUTAS ---
@app.route('/')
def index():
    lider_param = request.args.get('lider')
    return render_template('registro.html', 
                         lideres=LIDERES, 
                         localidades=LOCALIDADES_BOGOTA,
                         lider_seleccionado=lider_param)

@app.route('/registro', methods=['POST'])
def registro():
    if not sheet:
        return "Error: No se pudo conectar a la base de datos", 500

    # Obtener y limpiar datos
    nombre = limpiar_texto(request.form.get('nombre'))
    telefono = limpiar_telefono(request.form.get('telefono'))
    fecha_nacimiento = request.form.get('nacimiento')
    localidad = limpiar_texto(request.form.get('localidad'))
    lider = request.form.get('lider')
    
    # Validaciones básicas
    if not all([nombre, telefono, fecha_nacimiento, localidad, lider]):
        return "Por favor completa todos los campos requeridos", 400
    
    # Calcular edad automáticamente
    edad_calculada = calcular_edad(fecha_nacimiento)
    
    # INFERIR SEXO POR NOMBRE
    sexo_inferido = inferir_sexo_por_nombre(nombre)
    
    # Generar mensaje de bienvenida
    mensaje_bienvenida = generar_mensaje_bienvenida(nombre, sexo_inferido, localidad)
    
    fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Preparar fila para Google Sheets
    fila = [
        nombre, 
        telefono, 
        edad_calculada if edad_calculada else "N/A", 
        fecha_nacimiento,
        localidad,
        lider, 
        sexo_inferido,
        mensaje_bienvenida,
        fecha_registro
    ]
    
    try:
        sheet.append_row(fila, value_input_option="USER_ENTERED")
        print(f"Registro exitoso: {nombre} - {sexo_inferido} - {localidad}")
    except Exception as e:
        print(f"Error guardando en Google Sheets: {e}")
        return "Error al guardar el registro", 500

    return redirect(WHATSAPP_GROUP_LINK)

@app.route('/qr/<lider_id>')
def generar_qr(lider_id):
    if lider_id not in LIDERES:
        return "Líder no encontrado", 404
    
    base_url = get_base_url()
    url_formulario = f"{base_url}/?lider={lider_id}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=12,
        border=4,
    )
    qr.add_data(url_formulario)
    qr.make(fit=True)
    
    # QR con color morado del camello
    img = qr.make_image(fill_color="#9C27B0", back_color="white")
    
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return send_file(img_buffer, mimetype='image/png', as_attachment=False, download_name=f'qr_{lider_id}.png')

@app.route('/qr-todos')
def ver_todos_qr():
    qr_links = {}
    base_url = get_base_url()
    
    for lider_id in LIDERES:
        qr_links[lider_id] = {
            'nombre': LIDERES[lider_id],
            'qr_url': f"/qr/{lider_id}",
            'form_url': f"{base_url}/?lider={lider_id}",
            'short_url': f"{base_url}/?lider={lider_id}"
        }
    return render_template('todos_qr.html', qr_links=qr_links)

@app.route('/compartir/<lider_id>')
def compartir_link(lider_id):
    lider_id_normalizado = lider_id.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    lideres_normalizados = {k.lower(): v for k, v in LIDERES.items()}

    lider_nombre = lideres_normalizados.get(lider_id_normalizado)
    if not lider_nombre:
        return f"Líder '{lider_id}' no encontrado", 404

    base_url = get_base_url()
    url_formulario = f"{base_url}/?lider={lider_id_normalizado}"
    qr_url = f"/qr/{lider_id_normalizado}"

    return render_template(
        'compartir.html',
        lider_nombre=lider_nombre,
        url_formulario=url_formulario,
        qr_url=qr_url
    )


# Nueva ruta para estadísticas básicas
@app.route('/estadisticas')
def mostrar_estadisticas():
    try:
        # Obtener todos los registros
        registros = sheet.get_all_records()
        
        # Cálculos básicos
        total_registros = len(registros)
        generos = {}
        localidades = {}
        
        for registro in registros:
            # Conteo por género
            genero = registro.get('Sexo', 'No especificado')
            generos[genero] = generos.get(genero, 0) + 1
            
            # Conteo por localidad
            localidad = registro.get('Localidad', 'No especificada')
            localidades[localidad] = localidades.get(localidad, 0) + 1
        
        return render_template('estadisticas.html',
                            total_registros=total_registros,
                            generos=generos,
                            localidades=localidades)
    
    except Exception as e:
        return f"Error obteniendo estadísticas: {e}", 500

if __name__ == '__main__':
    if 'RENDER' in os.environ:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)

##if __name__ == '__main__':
  ##  app.run(debug=True, host='0.0.0.0', port=5000)
