#f_structure.py
from PyQt5.QtWidgets import QMessageBox
import xml.etree.ElementTree as ET
from PyQt5.QtGui import QColor

# Convertir QColor a cadena hexadecimal
def color_to_hex(color):
    return color.name()

def guardar_pos_flujo(file_path, widgets, connections, confirmacion=True):
    if confirmacion:
        msg = QMessageBox()
        msg.setWindowTitle("Guardar")
        msg.setText("¿Estás seguro de guardar los cambios?")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        respuesta = msg.exec_()
        if respuesta == QMessageBox.No:
            return
    try:
        root_flujo = ET.Element('posiciones')
        for widget in widgets:
            if not hasattr(widget, 'widget_id'):
                raise AttributeError(f"El widget no tiene el atributo 'widget_id': {widget}")
            color_hex = color_to_hex(widget.color)
            widget_element = ET.SubElement(root_flujo, 'widget', 
                id=str(widget.widget_id), 
                x=str(widget.pos().x()), 
                y=str(widget.pos().y()), 
                color=color_hex,
                can_delete=str(widget.can_delete).lower())
            for opcion in widget.opciones:
                opcion_element = ET.SubElement(widget_element, 'opcion', 
                    id=opcion[0], 
                    x=str(opcion[1].x()), 
                    y=str(opcion[1].y()))
        
        root_conexiones = ET.Element('conexiones')
        for widget in widgets:
            if not hasattr(widget, 'widget_id'):
                raise AttributeError(f"El widget no tiene el atributo 'widget_id': {widget}")
            widget_element = ET.SubElement(root_conexiones, 'widget', id=str(widget.widget_id))
            for conexion in widget.connections:
                conexion_element = ET.SubElement(widget_element, 'conexion', id=str(conexion))
        
        root = ET.Element('flujo')
        root.append(root_flujo)
        root.append(root_conexiones)
        
        tree = ET.ElementTree(root)
        tree.write(file_path)

    except Exception as e:
        print(f"Error al guardar las posiciones de flujo: {e}")


def cargar_pos_flujo(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        widgets = []

        # Cargar posiciones de los widgets
        for widget in root.find('posiciones').findall('widget'):
            try:
                widget_id = int(widget.get('id'))
            except:
                widget_id = None
            x = float(widget.get('x'))
            y = float(widget.get('y'))
            color = widget.get('color')
            can_delete = widget.get('can_delete', 'true').lower() == 'true'
            nombre = widget.get('nombre', '')  # Cargar el nombre del widget
            opciones = [(opcion.get('id'), (float(opcion.get('x')), float(opcion.get('y')))) 
                        for opcion in widget.findall('opcion')]
            widgets.append({
                'id': widget_id, 
                'x': x, 
                'y': y, 
                'color': color, 
                'can_delete': can_delete, 
                'nombre': nombre,  # Agregar el nombre del widget
                'opciones': opciones,
                'connections': []  # Inicializar conexiones vacías
            })

        # Crear un diccionario para mapear los IDs de los widgets
        widget_map = {widget['id']: widget for widget in widgets}

        # Cargar conexiones de los widgets
        for widget in root.find('conexiones').findall('widget'):
            widget_id = int(widget.get('id')) if widget.get('id') != 'None' else None
            if widget_id in widget_map:
                for conexion in widget.findall('conexion'):
                    conexion_id = int(conexion.get('id')) if conexion.get('id') != 'None' else None
                    conexion_nombre = conexion.get('nombre', '')  # Cargar el nombre del widget conectado
                    widget_map[widget_id]['connections'].append({
                        'id': conexion_id,
                        'nombre': conexion_nombre  # Agregar el nombre del widget conectado
                    })

        print(f"Posiciones y conexiones de flujo cargadas: {[w['id'] for w in widgets]}")
        return widgets
    except Exception as e:
        print(f"Error al cargar las posiciones y conexiones de flujo: {e}")
        return []

def guardar_datos_xml(file_path, widgets):
    try:
        root = ET.Element('mensajes')
        for widget in widgets:
            mensaje = ET.SubElement(root, 'mensaje', id=str(widget.widget_id))
            texto = ET.SubElement(mensaje, 'texto')
            texto.text = getattr(widget, 'text', '')  # Manejar si el widget no tiene el atributo 'text'
            opciones = ET.SubElement(mensaje, 'opciones')
            for opcion in widget.opciones:
                opcion_element = ET.SubElement(opciones, 'opcion', id=opcion[0])
                opcion_element.text = opcion[1]
        tree = ET.ElementTree(root)
        tree.write(file_path)
        print(f"Datos guardados en XML: {file_path}")
    except Exception as e:
        print(f"Error al guardar los datos en XML: {e}")

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