
from PyQt5.QtWidgets import QMessageBox
import xml.etree.ElementTree as ET
from PyQt5.QtGui import QColor

# Convertir QColor a cadena hexadecimal
def color_to_hex(color):
    return color.name()

def guardar_pos_flujo(file_path, widgets,confiramcion=True):
    if confiramcion:
        #alerta para confirmar guadado
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
        root = ET.Element('flujo')
        for widget in widgets:
            color_hex = color_to_hex(widget.color)
            widget_element = ET.SubElement(root, 'widget', 
                id=str(widget.widget_id), 
                x=str(widget.pos().x()), 
                y=str(widget.pos().y()), 
                color=color_hex,
                can_delete=str(widget.can_delete).lower())  # Añadimos can_delete
            for opcion in widget.opciones:
                opcion_element = ET.SubElement(widget_element, 'opcion', 
                    id=opcion[0], 
                    x=str(opcion[1].x()), 
                    y=str(opcion[1].y()))
        tree = ET.ElementTree(root)
        tree.write(file_path)
        print(f"Posiciones de flujo guardadas: {file_path}")
    except Exception as e:
        print(f"Error al guardar las posiciones de flujo: {e}")

def cargar_pos_flujo(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        widgets = []
        for widget in root.findall('widget'):
            try:
                widget_id = int(widget.get('id'))
            except:
                widget_id = None
            x = float(widget.get('x'))
            y = float(widget.get('y'))
            color = widget.get('color')
            can_delete = widget.get('can_delete', 'true').lower() == 'true'  # Añadimos can_delete
            opciones = [(opcion.get('id'), (float(opcion.get('x')), float(opcion.get('y')))) 
                        for opcion in widget.findall('opcion')]
            widgets.append({
                'id': widget_id, 
                'x': x, 
                'y': y, 
                'color': color, 
                'can_delete': can_delete,  # Incluimos can_delete en el diccionario
                'opciones': opciones
            })
        print(f"Posiciones de flujo cargadas: {[w['id'] for w in widgets]}")
        return widgets
    except Exception as e:
        print(f"Error al cargar las posiciones de flujo: {e}")
        return []

#guardar los datos de los widgets en un archivo XML
def guardar_datos_xml(file_path, widgets):
    try:
        root = ET.Element('mensajes')
        for widget in widgets:
            mensaje = ET.SubElement(root, 'mensaje', id=str(widget.widget_id))
            texto = ET.SubElement(mensaje, 'texto')
            texto.text = widget.text
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