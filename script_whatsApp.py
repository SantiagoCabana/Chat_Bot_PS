import os, sys,cv2,json, numpy as np
import socket,re,requests
import hashlib
import asyncio
from PyQt5.QtCore import QRunnable, pyqtSignal, pyqtSlot, QObject, QTimer
from PyQt5.QtGui import QImage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
import time, pickle
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def get_available_port(start_port):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

class SeleniumWorker(QRunnable):
    class Signals(QObject):
        finished = pyqtSignal()
        error = pyqtSignal(str)
        result = pyqtSignal(str)
        frame_ready = pyqtSignal(QImage)  # Cambiado a QImage

    def __init__(self, nombre_script):
        super().__init__()
        self.nombre_script = str(nombre_script)
        self.signals = self.Signals()
        self.stop_thread = threading.Event()
        self.driver = None
        self.running = False
        self.ruta_xml = os.path.join(self.get_executable_dir(),'DATA', 'resource','xml')
        self.ruta_json = os.path.join(self.get_executable_dir(),'DATA', 'resource', 'json')
        self.user_data_file = os.path.join(self.get_executable_dir(),'DATA', 'resource', 'json', 'Z_USERS_DATA.json')
        self.user_data_directory = None
        self.ruta_token = None
        self.user_data = None
        self.puerto = self.convertir_nombre_a_puerto(nombre_script)
        self.interval_id = None
        self.lista_chats = []
        self.lista_xpath = '//div[@aria-label="Lista de chats" and @role="grid" and contains(@class, "x1y332i5") and contains(@class, "x1n2onr6")]'
        self.capture_timer = None
        self.use_gui = False
        self.mensajes_list = '//div[@aria-label="Lista de chats" and @role="grid" and contains(@class, "x1y332i5") and contains(@class, "x1n2onr6")]'
        self.load_user_data()
        self.crear_archivos()

    @pyqtSlot()
    def run(self):
        if not self.ruta_token:
            self.signals.error.emit("No se ha configurado la ruta del token de inicio de sesión.")
        try:
            self.conectarse_lmStudio()  # Conectar a lmStudio al inicio
            self.iniciar()
            while not self.stop_thread.is_set():
                self.load_user_data()
                if self.nombre_script not in self.user_data or not self.user_data[self.nombre_script]["running"]:
                    self.stop()
                    break
                self.accion()
                asyncio.run(asyncio.sleep(0.1))
        except Exception as e:
            self.signals.error.emit(str(e))
            print(f"Error en el script: {str(e)}")
        finally:
            self.stop()
            self.signals.finished.emit()

    @pyqtSlot()
    def stop_script(self):
        self.user_data[self.nombre_script]["running"] = False
        self.save_user_data()
        self.stop_thread.set()
        if self.driver:
            self.signals.result.emit(f"Deteniendo instancia {self.nombre_script}")
            self.driver.quit()
        self.signals.finished.emit()

    def stop(self):
        self.running = False
        self.stop_thread.set()
        if self.driver:
            self.signals.result.emit(f"Deteniendo instancia {self.nombre_script}")
            self.driver.quit()
        self.signals.finished.emit()

    def load_user_data(self):
        if os.path.exists(self.user_data_file):
            with open(self.user_data_file, 'r') as f:
                user_data = json.load(f)
                if self.nombre_script in user_data:
                    self.user_data = user_data
                else:
                    self.user_data = {self.nombre_script: {"running": False}}
        else:
            self.user_data = {self.nombre_script: {"running": False}}
    
    def cargar_flujo_xml(self):
        ruta_flujo = os.path.join(self.ruta_xml, f'flujo_{self.nombre_script}.xml')
        if not os.path.exists(ruta_flujo):
            print(f"El archivo de flujo {ruta_flujo} no existe.")
            return None
        
        try:
            tree = ET.parse(ruta_flujo)
            return tree.getroot()
        except ET.ParseError:
            print(f"Error al analizar el archivo XML de flujo: {ruta_flujo}")
            return None

    def cargar_datos_usuario(self):
        if os.path.exists(self.user_data_file):
            with open(self.user_data_file, 'r') as f:
                datos = json.load(f)
                self.ruta_token = datos.get('ruta_token', '')

    def save_user_data(self):
        with open(self.user_data_file, 'w') as f:
            json.dump(self.user_data, f, indent=4)

    def iniciar(self):
        try:
            self.user_data_directory = os.path.join(self.get_executable_dir(), 'DATA', 'SCRIPTS', f'{self.nombre_script}')
            print(f"Nombre del script: {self.nombre_script}")  # Depuración
            if not os.path.exists(self.user_data_directory):
                os.makedirs(self.user_data_directory)
            print(f"{self.user_data_directory} creado")

            options = webdriver.ChromeOptions()
            if not self.use_gui:
                options.add_argument("--headless")
            options.add_argument(f"user-data-dir={self.user_data_directory}")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            options.add_argument("--disable-component-extensions-with-background-pages")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--lang=es")
            options.add_argument(f"--remote-debugging-port={self.puerto}")

            self.driver = webdriver.Chrome(options=options)
            self.driver.get('https://web.whatsapp.com/')

            # Iniciar la captura de pantalla
            self.capture_timer = QTimer()
            self.capture_timer.timeout.connect(self.capture_screen)
            self.capture_timer.start(40)  # 25 FPS (1000ms / 25 = 40ms)

            self.signals.result.emit(f"WhatsApp Web iniciado para {self.nombre_script}")

        except Exception as e:
            self.signals.error.emit(f"Error al iniciar: {str(e)}")

    def accion(self):
        try:
            self.esperar_carga_mensajes()
            print("Buscando chat no leído")
            time.sleep(5)
            self.ordenar_chats()
            time.sleep(0.5)
            self.signals.result.emit("Buscando chat no leído")
            self.selecionar_chat()
            time.sleep(5)
            self.leer_mensaje()
            accion = ActionChains(self.driver)
            accion.send_keys(Keys.ESCAPE).perform()
            time.sleep(5)
        except Exception as e:
            self.signals.error.emit(f"Error en la función acción: {str(e)}")

    def capture_screen(self):
        if self.driver:
            # Capturar la pantalla
            screenshot = self.driver.get_screenshot_as_png()
            nparr = np.frombuffer(screenshot, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convertir la imagen a formato QImage
            height, width, channel = img.shape
            bytes_per_line = 3 * width
            q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Emitir la señal con la imagen capturada
            self.signals.frame_ready.emit(q_img)

    def set_use_gui(self, use_gui):
        self.use_gui = use_gui



    #-----------------------------------Funciones Test-----------------------------------
    #crear achivos si no existen
    def crear_archivos(self):
        xml = [f"informes_{self.nombre_script}.xml"]
        for archivo in xml:
            filename = os.path.join(self.ruta_xml, archivo)
            if not os.path.exists(filename):
                #crear el archivo xml vacio osea 100% blanco
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write("")

    def añadir_tag(self, chat, tag):
        print(f"Añadiendo etiqueta '{tag}' al chat: {chat}")
        try:
            chat_element = self.driver.find_element(By.XPATH, f"//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and text()='{chat}']/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']")
            
            # Hacer clic derecho en el chat
            ActionChains(self.driver).context_click(chat_element).perform()
            time.sleep(0.1)
    
            # Encontrar y hacer clic en la opción de etiquetar
            etiquetar = self.driver.find_element(By.XPATH, "//li[@tabindex='0' and @data-animate-dropdown-item='true' and contains(@class, '_aj-r') and .//div[@role='button' and @aria-label='Etiquetar chat']]")
            etiquetar.click()
            time.sleep(0.1)
    
            # Seleccionar la etiqueta
            checkbox_etiqueta = self.driver.find_element(By.XPATH, f"//span[@title='{tag}']/ancestor::div[contains(@class, 'x10l6tqk') and @role='listitem']//button[@title='Añadir etiqueta']")
            checkbox_etiqueta.click()
            time.sleep(0.1)
    
            # Guardar la etiqueta
            guardar = self.driver.find_element(By.XPATH, "//button[not(@aria-disabled='true')]//div[text()='Guardar']")
            guardar.click()
            print(f"Etiqueta '{tag}' añadida con éxito al chat: {chat}")
        except Exception as e:
            print(f"Error al añadir la etiqueta '{tag}' al chat {chat}: {str(e)}")

    #-----------------------------------Funciones de HTML-----------------------------------
    # Ordenar chats en el HTML
    def ordenar_chats(self):
        # Localizar la lista de chats
        chat_list = self.driver.find_element(By.XPATH, self.lista_xpath)
        
        # Inyectar y ejecutar el script JavaScript para ordenar los chats cada 0.5 segundos y almacenar el ID del intervalo
        script = """
        const chatList = arguments[0];
        function ordenarChats() {
            const chats = Array.from(chatList.children);
            chats.sort((a, b) => {
                const translateY_A = parseInt(a.style.transform.match(/translateY\\((\\d+)px\\)/)[1]);
                const translateY_B = parseInt(b.style.transform.match(/translateY\\((\\d+)px\\)/)[1]);
                return translateY_A - translateY_B;
            });
            chats.forEach(chat => chatList.appendChild(chat));
        }
        const intervalId = setInterval(ordenarChats, 500); // Ejecutar cada 0.5 segundos
        return intervalId;  // Devolver el ID del intervalo
        """
        interval_id = self.driver.execute_script(script, chat_list)
        self.interval_id = interval_id  # Almacenar el ID del intervalo en la instancia
        
        print("Script de ordenación de chats iniciado con ID:", self.interval_id)

    # Remover el bucle de script de ordenación de chats específico
    def remover_orden_chats(self):
        if hasattr(self, 'interval_id') and self.interval_id is not None:
            # Inyectar y ejecutar el script JavaScript para detener el intervalo específico
            script = f"""
            clearInterval({self.interval_id});
            console.log('Intervalo con ID {self.interval_id} detenido');
            """
            self.driver.execute_script(script)
            print(f"Script de ordenación de chats removido con ID: {self.interval_id}")
            self.interval_id = None
        else:
            print("No hay un script de ordenación de chats en ejecución.")


    #-----------------------------------Funciones de chat-----------------------------------

    def generar_id_fijo(self, valor):
        # Crear un objeto hash SHA-256
        hash_obj = hashlib.sha256()
        # Actualizar el objeto hash con el valor codificado en bytes
        hash_obj.update(valor.encode('utf-8'))
        # Obtener el hash en formato hexadecimal
        hash_hex = hash_obj.hexdigest()
        # Convertir el hash hexadecimal a un número entero
        hash_int = int(hash_hex, 16)
        # Tomar los primeros 6 dígitos del número entero como el ID fijo
        return str(hash_int)[:6]

    #procesar respuesta
    def procesar_respuesta(self, nombre_formateado, tipo_chat):
        flujo = self.cargar_flujo_xml()
        if flujo is None:
            print("No se pudo cargar el flujo XML")
            return

        if tipo_chat == "nuevo":
            mensaje_bienvenida = flujo.find('welcomeMessage')
            if mensaje_bienvenida is None:
                print("No se encontró el mensaje de bienvenida en el XML")
                return
            mensaje_bienvenida = mensaje_bienvenida.text.strip()
            print(f"Mensaje de bienvenida original: {mensaje_bienvenida}")
            mensaje_modificado = self.generar_mensaje_lmStudio(mensaje_bienvenida)
            if mensaje_modificado:
                print(f"Mensaje modificado por lmStudio: {mensaje_modificado}")
                self.escribir_chat(mensaje_modificado)
            else:
                print("No se pudo modificar el mensaje, enviando el original")
                self.escribir_chat(mensaje_bienvenida)
        else:
            ultimo_mensaje = self.obtener_ultimo_mensaje(nombre_formateado)
            
            if ultimo_mensaje:
                respuesta = self.buscar_respuesta(flujo, ultimo_mensaje)
                if respuesta:
                    mensaje_modificado = self.generar_mensaje_lmStudio(respuesta)
                    if mensaje_modificado:
                        self.escribir_chat(mensaje_modificado)
                    else:
                        self.escribir_chat(respuesta)
                else:
                    respuesta_default = flujo.find('defaultResponse').text.strip()
                    mensaje_modificado = self.generar_mensaje_lmStudio(respuesta_default)
                    if mensaje_modificado:
                        self.escribir_chat(mensaje_modificado)
                    else:
                        self.escribir_chat(respuesta_default)
            else:
                print("No se pudo obtener el último mensaje del chat.")

    def conectarse_lmStudio(self):
        print("Conectando a lmStudio...")
        self.lmstudio_url = "http://localhost:1234/v1/chat/completions"
        self.lmstudio_headers = {
            "Content-Type": "application/json"
        }

    def generar_mensaje_lmStudio(self, mensaje_usuario):
        data = {
            "messages": [
                {"role": "system", "content": "Tu tarea es realizar modificaciones sutiles y ligeras a los mensajes relacionados con cursos que recibas. Sigue estas reglas: Mantén el tema y la intención original del mensaje. Haz cambios ligeros usando sinónimos y reformulando frases de manera sutil para mejorar el mensaje sin alterarlo drásticamente. Incorpora algunos emojis relevantes para destacar puntos clave, sin exagerar su uso. Respeta y mantén intactos los enlaces, fechas y horas proporcionados. Mantén la estructura del mensaje, incluyendo saltos de línea. No agregues información nueva ni promociones adicionales. Mejora ligeramente el llamado a la acción final para hacerlo más atractivo, sin cambiar su esencia. Responde únicamente con el mensaje modificado, sin comentarios adicionales. Asegúrate de que el mensaje completo esté en español. Evita cambios exagerados; las modificaciones deben ser leves y naturales. Cada respuesta que des debe de ser diferente."},
                {"role": "user", "content": mensaje_usuario}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        try:
            response = requests.post(self.lmstudio_url, headers=self.lmstudio_headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.RequestException as e:
            print(f"Error al conectar con lmStudio: {e}")
            return None

    def obtener_ultimo_mensaje(self, nombre_formateado):
        ruta_chat = os.path.join(self.get_executable_dir(), 'DATA', 'history', 'chats', f'{nombre_formateado}.xml')
        if not os.path.exists(ruta_chat):
            return None
        
        try:
            tree = ET.parse(ruta_chat)
            root = tree.getroot()
            mensajes = root.findall(".//mensaje[@tipo='el']")
            if mensajes:
                return mensajes[-1].text
        except ET.ParseError:
            print(f"Error al analizar el archivo XML del chat: {ruta_chat}")
        
        return None

    def buscar_respuesta(self, flujo, mensaje):
        for response in flujo.findall('.//response'):
            keyword = response.find('keyword').text.strip().lower()
            if re.search(r'\b' + re.escape(keyword) + r'\b', mensaje.lower()):
                return response.find('message').text.strip()
        return None

    def selecionar_chat(self):
        # Abrir el primer chat no leido no leido con nombre q esta dentro de la lista de chats pero solo selecionar el primero sin leer de todos
        lista_chats_xpath = self.lista_xpath
        chat_sin_nombre_xpath_no_tag ="//div[@class='x10l6tqk xh8yej3 x1g42fcv' and not(descendant::div[contains(@class, '_aj_l')]//div[contains(@class, 'x1rg5ohu') and contains(@class, 'x2lah0s') and contains(@class, 'x16dsc37')])]//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and starts-with(text(), '+')]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[(@aria-label='No leídos' or contains(@aria-label, 'mensaje no leído') or contains(@aria-label, 'no leídos'))]"
        # Esperar a que la lista de chats esté presente
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, lista_chats_xpath)))
        print("Lista de chats presente")

        self.remover_orden_chats()
        # Intentar encontrar todos los chats no leídos sin nombre
        chats_no_leidos = self.driver.find_elements(By.XPATH, chat_sin_nombre_xpath_no_tag)

        if chats_no_leidos:
            try:
                # Seleccionar el primer chat no leído sin nombre
                primer_chat_no_leido = chats_no_leidos[0]
                primer_chat_no_leido.click()
                print("Chat no leído seleccionado")
            except:
                print("No se pudo seleccionar el chat no leído")
        else:
            print("No se encontraron chats no leídos")
    
    def agendar_contacto_api_contacts_google(self, id, numero):
        nombre = f'{self.nombre_script}_{id}'
        
        # Cargar el token de inicio de sesión desde el archivo JSON
        token_path = self.ruta_token
        with open(token_path, 'r') as token_file:
            token_data = json.load(token_file)
            creds = Credentials.from_authorized_user_info(token_data)
        
        # Crear el servicio de la API
        service = build('people', 'v1', credentials=creds)
        
        # Crear el cuerpo del contacto
        contact_body = {
            'names': [{'givenName': nombre}],
            'phoneNumbers': [{'value': numero}]
        }
        
        try:
            contact = service.people().createContact(body=contact_body).execute()
            print(f'Contacto creado: {contact.get("names")[0].get("displayName")}')
            return nombre
        except Exception as e:
            print(f'Error al crear el contacto: {e}')
            return None
        
    def save_contact_list(self, nombre):
        print(f"Guardando contacto en XML: {nombre}")
        self.ruta = os.path.join(self.get_executable_dir(), 'DATA', 'history', 'registro_general_contacts.xml')
        
        # Verificar si el archivo XML existe
        if not os.path.exists(self.ruta):
            root = ET.Element("contacts")
            tree = ET.ElementTree(root)
            tree.write(self.ruta, encoding='utf-8', xml_declaration=True)
        
        try:
            tree = ET.parse(self.ruta)
            root = tree.getroot()
        except ET.ParseError:
            root = ET.Element("contacts")
            tree = ET.ElementTree(root)
            tree.write(self.ruta, encoding='utf-8', xml_declaration=True)
            tree = ET.parse(self.ruta)
            root = tree.getroot()
        
        # Generar un ID único fijo
        id = self.generar_id_fijo(nombre)
        # Formatear el numero sin espacios para guardar en la API
        nombre_formateado = nombre.replace(' ', '')
        nombre_sin_plus = self.formatear_numero(nombre)
        
        # Verificar si ya existe un contacto con el mismo ID y nombre o contact
        for contacto in root.findall("chat"):
            if (contacto.get("id") == id and contacto.get("contact") == nombre_formateado) or \
               (contacto.get("id") == id and contacto.get("nombre") == nombre_sin_plus):
                print(f"El contacto {nombre_formateado} ya existe con el mismo ID.")
                return id, nombre_sin_plus
            
        # Agendar el contacto usando la API de Google Contacts
        nombre_contacto = self.agendar_contacto_api_contacts_google(id, nombre_formateado)
        
        # Agregar el nuevo contacto
        contacto = ET.Element("chat", nombre=nombre_sin_plus, id=id, contact=nombre_contacto)
        root.append(contacto)
        tree.write(self.ruta, encoding='utf-8', xml_declaration=True)
    
        return id, nombre_sin_plus

    def save_chat_in_xml(self, nombre,id, chat):
        print(f"Guardando chat en XML: {nombre}")
        self.ruta = os.path.join(self.get_executable_dir(), 'DATA', 'history', 'chats', f'{nombre}_{id}.xml')
        
        # Verificar si el archivo XML existe
        if not os.path.exists(self.ruta):
            root = ET.Element("chats")
            chat_node = ET.SubElement(root, "chat")
            tree = ET.ElementTree(root)
            tree.write(self.ruta, encoding='utf-8', xml_declaration=True)
        else:
            try:
                tree = ET.parse(self.ruta)
                root = tree.getroot()
            except ET.ParseError:
                # Si el archivo está vacío o mal formado, crear un nuevo archivo XML
                root = ET.Element("chats")
                chat_node = ET.SubElement(root, "chat")
                tree = ET.ElementTree(root)
                tree.write(self.ruta, encoding='utf-8', xml_declaration=True)
                tree = ET.parse(self.ruta)
                root = tree.getroot()
        
        # Buscar el nodo `chat`
        chat_node = root.find("chat")
        
        if chat_node is None:
            raise ValueError("No se encontró el nodo <chat>")
        
        # Recopilar todos los mensajes después de los últimos 3 separadores
        mensajes_existentes = []
        separadores_encontrados = 0
        for elem in reversed(chat_node):
            if elem.tag == "separator":
                separadores_encontrados += 1
                if separadores_encontrados == 3:
                    break
            if elem.tag == "mensaje":
                mensajes_existentes.append((elem.get("tipo"), elem.text, elem.get("hora")))
        
        # Invertir la lista para mantener el orden original
        mensajes_existentes.reverse()
        
        # Filtrar los mensajes nuevos para evitar duplicados y mensajes eliminados
        mensajes_filtrados = []
        for mensaje in chat:
            # Extraer la hora y el texto del mensaje
            hora = mensaje["texto"][-5:].strip()
            texto = mensaje["texto"][:-5].strip()
            
            # Asegurarse de que la hora tenga el formato correcto
            if len(hora) == 4:  # Caso donde la hora es de un solo dígito (e.g., "6:08")
                hora = "0" + hora
            
            # Verificar si el mensaje ya existe (comparando tipo, texto y hora)
            if (mensaje["tipo"], texto, hora) not in mensajes_existentes:
                mensajes_filtrados.append({
                    "tipo": mensaje["tipo"],
                    "texto": texto,
                    "hora": hora
                })
        
        # Añadir una etiqueta separadora solo si hay mensajes nuevos
        if mensajes_filtrados:
            separator = ET.Element("separator")
            chat_node.append(separator)
            
            # Agregar los nuevos mensajes filtrados
            for mensaje in mensajes_filtrados:
                if mensaje["texto"]:  # Verificar que el texto no esté vacío
                    mensaje_elem = ET.Element("mensaje", tipo=mensaje["tipo"], hora=mensaje["hora"])
                    mensaje_elem.text = mensaje["texto"]
                    chat_node.append(mensaje_elem)
        
        tree.write(self.ruta, encoding='utf-8', xml_declaration=True)
    
    def leer_mensaje(self):
        print("leyendo mensajes")
        mensajes_lista = self.mensajes_list
        
        self.nombre = "//*[@id='main']/header/div[2]/div[1]/div/div/span[1]"
        nombre_chat = self.driver.find_element(By.XPATH, self.nombre).text
        print(f"Chat: {nombre_chat}")
        
        # Guardar el contacto y obtener el ID
        id, nombre_formateado = self.save_contact_list(nombre_chat)
        
        mensajes_nuevos = []
        
        # XPath para capturar todos los mensajes en el orden en que aparecen
        xpath = "//div[contains(@class, 'message-in') or contains(@class, 'message-out')]"
        
        mensajes = self.driver.find_elements(By.XPATH, xpath)
        for mensaje in mensajes:
            if mensaje.get_attribute("aria-live") == "polite":
                break
            tipo = "mio" if "message-out" in mensaje.get_attribute("class") else "el"
            try:
                hora_element = mensaje.find_element(By.XPATH, ".//span[contains(@class, 'copyable-text')]")
                hora = hora_element.get_attribute("data-pre-plain-text").split('] ')[0][1:]
            except:
                hora = ""
            mensajes_nuevos.append({"tipo": tipo, "texto": mensaje.text, "hora": hora})
        
        for mensaje in mensajes_nuevos:
            print(mensaje["texto"])
        
        self.save_chat_in_xml(nombre_formateado, id, mensajes_nuevos)
        
        print(f"Enviando mensaje de bienvenida a {nombre_chat}")
        self.procesar_respuesta(nombre_formateado, "nuevo")
        time.sleep(2)  # Esperar un poco antes de añadir la etiqueta
        print(f"Añadiendo etiqueta al chat: {nombre_chat}")
        self.añadir_tag(nombre_chat, "Bienvenida Enviada")

    # Formatear el número dependiendo del país
    def formatear_numero(self, numero):
        # Eliminar el símbolo '+' y los espacios
        numero_formateado = numero.replace('+', '').replace(' ', '')
        return numero_formateado
    
    #formatear uuid para q este sin guiones
    def formatear_uuid(self, uuid):
        return uuid.replace('-', '')
    
    #-----------------------------------Acciones de chat-----------------------------------
    
    def escribir_excepcion(self, caso, excepcion):
        print(f"Escribiendo excepción en el chat: {caso}")
        input_element = self.seleccionar_input()
        #Escribir el mensaje con saltos de linea y JavaScript
        for linea in excepcion.split("\n"):
            if linea == "{null}":
                self.driver.execute_script("arguments[0].appendChild(document.createElement('br'));", input_element)
            else:
                JS_ADD_TEXT_TO_INPUT = """
                var elm = arguments[0], txt = arguments[1];
                elm.focus();
                document.execCommand('insertText', false, txt);
                """
                self.driver.execute_script(JS_ADD_TEXT_TO_INPUT, input_element, linea)
            self.driver.execute_script("arguments[0].appendChild(document.createElement('br'));", input_element)
            time.sleep(0.5)
            input_element.send_keys(Keys.SHIFT + Keys.ENTER)
        #enviar el mensaje
        self.enviar_mensaje()
    
    def escribir_chat(self, mensaje):
        print(f"Escribiendo mensaje en el chat")
        #escribir usando js para ingresar el texto
        input_element = self.seleccionar_input()
        #esperar 0.5 segundos
        time.sleep(0.5)
        #Escribir el mensaje con saltos de linea y JavaScript
        for linea in mensaje.split("\n"):
            if linea == "{null}":
                self.driver.execute_script("arguments[0].appendChild(document.createElement('br'));", input_element)
            else:
                JS_ADD_TEXT_TO_INPUT = """
                var elm = arguments[0], txt = arguments[1];
                elm.focus();
                document.execCommand('insertText', false, txt);
                """
                self.driver.execute_script(JS_ADD_TEXT_TO_INPUT, input_element, linea)
            self.driver.execute_script("arguments[0].appendChild(document.createElement('br'));", input_element)
            time.sleep(0.5)
            input_element.send_keys(Keys.SHIFT + Keys.ENTER)
        #enviar el mensaje
        self.enviar_mensaje()

    def enviar_mensaje(self):
        print("Enviando mensaje")
        # Enviar el mensaje
        send_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
        )
        send_button.click()

        #selecionar el input para escribir el mensaje, limpiarlo
    def seleccionar_input(self):
        print("Seleccionando input")
        # Esperar hasta que el elemento esté presente
        input_element = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @aria-placeholder="Escribe un mensaje"]'))
        )
        # Limpiar el input con ctrl a y suprimir
        input_element.send_keys(Keys.CONTROL + 'a')
        input_element.send_keys(Keys.DELETE)
        print("Input seleccionado y limpiado")
        # Retornar el input
        return input_element
    
    #esperar a que cargue todos los mensages
    def esperar_carga_mensajes(self):
        while True:
            try:
                # Esperar a que aparezca el botón de nuevo chat
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='button' and @aria-label='Nuevo chat']"))
                )
                print("whatsapp cargado")
                time.sleep(2)
                break
            except:
                print("Esperando a que cargue WhatsApp")
                time.sleep(2)

    #-----------------------------------Funciones auxiliares-----------------------------------

    def get_executable_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))
    
    def puerto_disponible(self, puerto):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', puerto)) != 0
    
    def convertir_nombre_a_puerto(self, nombre):
        puerto = 9222 + abs(hash(nombre)) % 1000
        while not self.puerto_disponible(puerto):
            puerto += 1
        return puerto
    
    def conectarse_lmStudio(self):
        print("Conectando a lmStudio...")

# Ejemplo de uso
if __name__ == "__main__":
    worker = SeleniumWorker("DATA1")
    worker.set_use_gui(True)
    worker.run()