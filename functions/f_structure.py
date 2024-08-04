import xml.etree.ElementTree as ET

def cargar_datos_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        mensajes = []
        for mensaje in root.findall('mensaje'):
            texto = mensaje.find('texto')
            opciones = mensaje.find('opciones')
            if texto is not None and opciones is not None:
                msg = {
                    'id': mensaje.get('id'),
                    'texto': texto.text,
                    'opciones': [(opcion.get('id'), opcion.text) for opcion in opciones.findall('opcion')]
                }
                mensajes.append(msg)
        print(f"Estructura de mensajes cargada: {[m['id'] for m in mensajes]}")
        return mensajes
    except Exception as e:
        print(f"Error al cargar la estructura de mensajes: {e}")
        return []