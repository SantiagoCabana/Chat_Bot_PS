import os, sys,cv2,json, numpy as np
import socket
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
        self.user_data = None
        self.puerto = self.convertir_nombre_a_puerto(nombre_script)
        self.interval_id = None
        self.lista_chats = []
        self.lista_xpath = None
        self.capture_timer = None
        self.use_gui = False
        self.mensajes_list = "//div[@class='x3psx0u xwib8y2 xkhd6sd xrmvbpv']"
        self.load_user_data()
        self.crear_archivos()

    @pyqtSlot()
    def run(self):
        try:
            self.iniciar()
            while not self.stop_thread.is_set():
                self.load_user_data()  # Recargar datos para verificar el estado actual
                if self.nombre_script not in self.user_data or not self.user_data[self.nombre_script]["running"]:
                    self.stop()
                    break
                self.accion()
                asyncio.run(asyncio.sleep(0.1))  # Dormir por 100ms para evitar uso excesivo de CPU
        except Exception as e:
            self.signals.error.emit(str(e))
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

    def stop_running(self):
        self.user_data[self.nombre_script]["running"] = False
        self.save_user_data()
        self.stop_thread.set()
        
    def detect_stop(self):
        while not self.stop_thread.is_set():
            if not self.running:
                self.signals.result.emit("Se detectó la detención del script. Deteniendo...")
                self.stop()
                break
            time.sleep(0.1)  # Revisar cada 100 ms

    def stop(self):
        self.running = False
        self.stop_thread.set()
        if self.driver:
            self.signals.result.emit(f"Deteniendo instancia {self.nombre_script}")
            self.driver.quit()
        self.signals.finished.emit()

    #-----------------------------------Funciones Test-----------------------------------
    def extraer_html_de_chat(self):
        xpath = "//div[@class='x3psx0u xwib8y2 xkhd6sd xrmvbpv']"
        filename = os.path.join(self.ruta_xml, f"chat_{self.nombre_script}.html")
        try:
            element = self.driver.find_element(By.XPATH,xpath)
            inner_html = element.get_attribute('innerHTML')
            
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(inner_html)
        except NoSuchElementException:
            print("No se pudo encontrar el elemento.")

    #crear achivos si no existen
    def crear_archivos(self):
        xml = [f"informes_{self.nombre_script}.xml"]
        for archivo in xml:
            filename = os.path.join(self.ruta_xml, archivo)
            if not os.path.exists(filename):
                #crear el archivo xml vacio osea 100% blanco
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write("")

    def boton_filtro(self):
        #selecionar el boton de filtro de busqueda de chats pero verificar si esta activado o desactivado
        try:
            filtro = self.driver.find_element(By.XPATH, "//button[@data-tab='4' and @aria-label='Menú de filtros de chats' and @aria-pressed='false']")
            filtro.click() #activar filtro
            print("Boton filtro encontrado y activado")
        except NoSuchElementException:
            #llamar el desacrivador de filtro
            print("No se pudo encontrar el boton filtro, verificando si esta activado y luego activarlo")
            self.deselect_filtro()
            time.sleep(0.5)
            self.boton_filtro()

    def deselect_filtro(self,open=False):
        try:
            if open:
                filtro = self.driver.find_element(By.XPATH, "//button[@data-tab='4' and @aria-label='Menú de filtros de chats' and @aria-pressed='false']")
                filtro.click()
                print("Boton filtro encontrado y activado")
                return
            filtro = self.driver.find_element(By.XPATH, "//button[@data-tab='4' and @aria-label='Menú de filtros de chats' and @aria-pressed='true']")
            filtro.click()
            print("Boton filtro encontrado y desactivado")
            #precionar esc para cerrar el filtro y el  chat
            accion = ActionChains(self.driver)
            accion.send_keys(Keys.ESCAPE).perform()
            print("Boton filtro encontrado y desactivado")
        except NoSuchElementException:
            print("No se pudo encontrar el boton filtro")

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

    #Informe de la lista de chats:
    def informe_chats(self):
        chat_list = self.driver.find_element(By.XPATH, self.lista_xpath)
        # Continuar con el procesamiento de los chats ordenados
        all_chats = chat_list.find_elements(By.XPATH, ".//div[contains(@class, '_aou8')]")
        count_con_nombre = 0
        chats_con_nombre = []
        count_sin_nombre = 0
        chats_sin_nombre = []

        chat_list_no_read = []
        #escanear los chats y guardar un informe en un archivo generarn un id para cada chat mediante su nombre en un xml o json
        for chat in all_chats:
            try:
                # Intentar encontrar el nombre del chat
                nombre = chat.find_element(By.XPATH, ".//span[contains(@class, 'x1iyjqo2') and string-length(text()) > 0 and not(starts-with(text(), '+'))]")
                count_con_nombre += 1
                chats_con_nombre.append(nombre.text)
                nombre_no_leido = chat.find_element(By.XPATH, "//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and string-length(text()) > 0 and not(starts-with(text(), '+'))]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[(@aria-label='No leídos' or contains(@aria-label, 'no leídos'))]")
                chat_list_no_read.append(nombre_no_leido.text)
            except:
                # Si no se encuentra el nombre, verificar si es un número sin nombre
                try:
                    numero = chat.find_element(By.XPATH, ".//span[contains(@class, 'x1iyjqo2') and starts-with(text(), '+')]")
                    count_sin_nombre += 1
                    chats_sin_nombre.append(numero.text)

                except:
                    # Si no se encuentra ni nombre ni número, ignorar este chat
                    pass
        #fucionar listas y guardar informe
        informe = chats_con_nombre + chats_sin_nombre

        self.guardar_informe(informe, "chat_list")

        # Imprimir resultados
        print(f"Cantidad total de chats: {len(all_chats)}")
        print(f"Cantidad de chats sin nombre: {count_sin_nombre}")
        print(f"Cantidad de chats con nombre: {count_con_nombre}")

        print("Chats sin nombre en el orden en que se encontraron:")
        for chat in chats_sin_nombre:
            print(chat)

    def guardar_informe(self, informacion, tipo):
        if tipo == "chat_list":
            self.guardar_informe_chat_list(informacion)
    
    def guardar_informe_chat_list(self, informacion):
        filename = os.path.join(self.ruta_xml, f"informes_{self.nombre_script}.xml")
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            try:
                tree = ET.parse(filename)
                root = tree.getroot()
            except ET.ParseError:
                # Si el archivo está malformado, lo tratamos como si no existiera
                root = ET.Element("informes")
        else:
            root = ET.Element("informes")
        # Buscamos o creamos el elemento "chat_list"
        chat_list_element = root.find("chat_list_no_read")
        if chat_list_element is None:
            chat_list_element = ET.SubElement(root, "chat_list_no_read")
        # Añadimos o actualizamos la información con fecha y hora
        for chat in informacion:
            id_chat = self.generar_id_fijo(chat)
            fecha = datetime.now().strftime("%d/%m/%Y")
            hora = datetime.now().strftime("%H:%M:%S")
            # Buscamos si ya existe un chat con el mismo id
            existing_chat_element = chat_list_element.find(f"./chat[@id='{id_chat}']")
            if existing_chat_element is not None:
                # Si existe, actualizamos el contenido y los atributos
                existing_chat_element.set('fecha', fecha)
                existing_chat_element.set('hora', hora)
                existing_chat_element.text = chat
            else:
                # Si no existe, creamos un nuevo elemento
                chat_element = ET.SubElement(chat_list_element, "chat", id=id_chat, fecha=fecha, hora=hora)
                chat_element.text = chat
        # Guardamos el archivo
        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

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
    def procesar_respuesta(self):
        pass

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
            print("No hay chats no leídos con nombre.")
            try:
                print("No se encontraron chats no leídos sin nombre\n aplicando filtro")
                # Si no se encuentran chats no leídos, deseleccionar el filtro
                self.deselect_filtro(open=True)
                name_tag = "Video Explicativo 40%"
                print(f"seleccionando la etiqueta: {name_tag}") 
                # Construir el XPath para el nuevo filtro basado en la etiqueta
                etiqueta = f"//li[contains(@class, '_aj-r') and contains(@class, '_aj-q') and contains(@class, '_aj-_')]//button[contains(@class, 'x9f619')]//div[contains(@class, 'x3nfvp2')]//div[contains(@class, 'x78zum5')]//svg[contains(@class, 'x1rg5ohu')]//span[contains(@class, 'x1f6kntn')]//span[@class='_ao3e' and text()='{name_tag}']"
                # Intentar encontrar el elemento del filtro y hacer clic en él
                filtro = self.driver.find_element(By.XPATH, etiqueta)
                filtro.click()
            except NoSuchElementException:
                # Si no se encuentra el filtro, imprimir un mensaje y retornar
                print("No se encontraron chats no leídos")

    #funcion para leer el chat y ver el estatus de nuestro mensaje
    def leer_chat(self):
        #guiate de @readme para mas informacion de los xpath
        enviado = self.driver.find_element(By.XPATH, "//div[contains(@class, 'message-out')]//span[@aria-label=' Enviado ']")
        entregado = self.driver.find_element(By.XPATH, "//div[contains(@class, 'message-out')]//span[@aria-label=' Entregado ']")
        leido = self.driver.find_element(By.XPATH, "//div[contains(@class, 'message-out')]//span[@aria-label=' Leído ']")

    #mensaje de bienvenida
    def mensaje_bienvenida(self):
        pass

    
    def agendar_contacto_api_contacts_google(self, id, numero):
        nombre = f'{self.nombre_script}_{id}'
        
        # Cargar el token de inicio de sesión
        token_path = os.path.join(self.get_executable_dir(), 'DATA', 'tokens', 'pickle', 'token.pickle')
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        
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
        id,nombre_formateado = self.save_contact_list(nombre_chat)
        
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
        
        self.save_chat_in_xml(nombre_formateado,id, mensajes_nuevos)

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
    
    #escanear lista de chats
    def escanear_chats(self):
        #identificar los xpath de caa tipo de chat @readme para mas informacion
        chats = self.driver.find_elements(By.XPATH, "//div[@class='_1H6CJ']")
        for chat in chats:
            try:
                #identificar el nombre del chat
                nombre = chat.find_element(By.XPATH, ".//span[@title]")
                print(nombre.text)
            except:
                #si no tiene nombre, identificar el numero
                try:
                    numero = chat.find_element(By.XPATH, ".//span[@dir='ltr']")
                    print(numero.text)
                except:
                    #si no tiene nombre ni numero, ignorar el chat
                    pass
        #identicar grupos leidos y sin leer (leidos:"//div[@class='_ak8q']/span[contains(@class, 'x1iyjqo2') and not(starts-with(text(), '+'))]") no leidos
    

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

# Ejemplo de uso
if __name__ == "__main__":
    worker = SeleniumWorker("DATA1")
    worker.run()