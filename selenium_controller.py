from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import xml.etree.ElementTree as ET
from datetime import datetime
import os, socket, asyncio
import hashlib
import time

class SeleniumController:
    def __init__(self, nombre_script):
        if not isinstance(nombre_script, str):
            raise ValueError("El nombre del script debe ser una cadena")
        
        self.ruta_xml = 'DATA/resource/xml/'
        self.nombre_script = nombre_script
        self.puerto = self.convertir_nombre_a_puerto(nombre_script)
        self.driver = None
        self.running = False

        self.lista_chats = []

        self.mensajes_list = "//div[@class='x3psx0u xwib8y2 xkhd6sd xrmvbpv']"

        #iniciar funciones
        self.crear_archivos()

    async def iniciar(self):
        try:
            self.user_data_directory = os.path.join(self.get_executable_dir(), 'DATA', 'SCRIPTS', f'{self.nombre_script}')
            if not os.path.exists(self.user_data_directory):
                os.makedirs(self.user_data_directory)

            options = webdriver.ChromeOptions()
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

            loop = asyncio.get_event_loop()
            self.driver = await loop.run_in_executor(None, webdriver.Chrome, options)
            self.driver.get('https://web.whatsapp.com/')
            self.running = True

        except Exception as e:
            self.running = False
            print(f"Error: {e}")
        #inciar la funcon de accion
        await self.accion()

    async def accion(self):
        try:
            #esperar carga de mensajes
            self.esperar_carga_mensajes()

            self.ordenar_chats()

            time.sleep(0.5)
            
            #informe de chats
            self.informe_chats()

            print("Buscando chat no leido")
            #identificar chats no leidos
            self.selecionar_chat()
            #escritura de mensaje
            mensaje = "Hola, soy Sam un ChatBot de prueba, causa :v"
            self.escribir_chat(mensaje)
            time.sleep(0.5)
            #detectar nuevos mensajes:
            self.leer_mensaje()
            time.sleep(5)
            #precionar esc para cerrar el chat
            accion = ActionChains(self.driver)
            accion.send_keys(Keys.ESCAPE).perform()
            time.sleep(5)
        except Exception as e:
            print(f"Error en la función accion: {e}")

    def conversando(self,data):
        pass

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
                
    #-----------------------------------Funciones de HTML-----------------------------------
    #ordenar chats en el html
    def ordenar_chats(self):
        # Localizar la lista de chats
        chat_list = self.driver.find_element(By.XPATH, "//div[@aria-label='Lista de chats' and @role='grid']")
        
        # Inyectar y ejecutar el script JavaScript para ordenar los chats
        script = """
        const chatList = arguments[0];
        const chats = Array.from(chatList.children);
        chats.sort((a, b) => {
            const translateY_A = parseInt(a.style.transform.match(/translateY\\((\\d+)px\\)/)[1]);
            const translateY_B = parseInt(b.style.transform.match(/translateY\\((\\d+)px\\)/)[1]);
            return translateY_A - translateY_B;
        });
        chats.forEach(chat => chatList.appendChild(chat));
        """
        self.driver.execute_script(script, chat_list)

        print("Chats ordenados")
    
    #-----------------------------------Funciones de chat-----------------------------------

    #Informe de la lista de chats:
    def informe_chats(self):
        chat_list = self.driver.find_element(By.XPATH, "//div[@aria-label='Lista de chats' and @role='grid']")
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
            id_chat = hashlib.md5(chat.encode()).hexdigest()[:6]
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

    #procesar respuesta
    def procesar_respuesta(self):
        pass

    def selecionar_chat(self):
        # Abrir el primer chat no leido no leido con nombre q esta dentro de la lista de chats pero solo selecionar el primero sin leer de todos
        lista_chats_xpath = "//div[@aria-label='Lista de chats' and @role='grid']"
        chat_con_nombre_xpath = "//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and not(starts-with(text(), '+'))]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[(@aria-label='No leídos' or contains(@aria-label, 'no leídos'))]"
        chat_sin_nombre_xpath = "//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and starts-with(text(), '+')]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[(@aria-label='No leídos' or contains(@aria-label, 'no leídos'))]"

        # Esperar a que la lista de chats esté presente
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, lista_chats_xpath)))
        print("Lista de chats presente")

        #selecionar un chat sin nombre y si no hay sin nombre se selecionara el que tiene nombre
        try:
            # Encontrar todos los chats no leídos con nombre
            chats_no_leidos = self.driver.find_elements(By.XPATH, chat_sin_nombre_xpath)
        except NoSuchElementException:
            try:
                #en caso q no haya chats sin nombre se selecionara el que tiene nombre
                chats_no_leidos = self.driver.find_elements(By.XPATH, chat_con_nombre_xpath)
            except NoSuchElementException:
                print("No se encontraron chats no leídos")
                return

        if chats_no_leidos:
            # Seleccionar el primer chat no leído con nombre
            primer_chat_no_leido = chats_no_leidos[0]
            primer_chat_no_leido.click()
        else:
            print("No hay chats no leídos con nombre.")

    #funcion para leer el chat y ver el estatus de nuestro mensaje
    def leer_chat(self):
        #guiate de @readme para mas informacion de los xpath
        enviado = self.driver.find_element(By.XPATH, "//div[contains(@class, 'message-out')]//span[@aria-label=' Enviado ']")
        entregado = self.driver.find_element(By.XPATH, "//div[contains(@class, 'message-out')]//span[@aria-label=' Entregado ']")
        leido = self.driver.find_element(By.XPATH, "//div[contains(@class, 'message-out')]//span[@aria-label=' Leído ']")

    #mensaje de bienvenida
    def mensaje_bienvenida(self):
        pass

    def leer_mensaje(self):
        # imprimir nuevos mensajes
        print("leyendo mensajes")
        mensajes_lista = self.mensajes_list
        separador_mensajes_nuevos = "//div[@class='_agtb focusable-list-item' and @tabindex='-1']/span[@class='_agtk' and @aria-live='polite']"
        #agregar en una lista temporal los mensajes nuevos los cuales seran los q estan separados por el separador xq la lista de el html lo debe de leer desde abajo hacia arriba y parar hasta el separador
        mensajes_nuevos = []
        mensajes = self.driver.find_elements(By.XPATH, mensajes_lista)
        for mensaje in mensajes:
            if mensaje.get_attribute("aria-live") == "polite":
                break
            mensajes_nuevos.append(mensaje)
        #imprimir mensajes nuevos
        for mensaje in mensajes_nuevos:
            print(mensaje.text)

    #escribir excepciones
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
        # Esperar a que aparezca el botón de nuevo chat
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='button' and @aria-label='Nuevo chat']"))
        )
        print("whatsapp cargado")
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
        return os.path.dirname(os.path.abspath(__file__))
    
    def puerto_disponible(self, puerto):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', puerto)) != 0
    
    def convertir_nombre_a_puerto(self, nombre):
        puerto = 9222 + abs(hash(nombre)) % 1000
        while not self.puerto_disponible(puerto):
            puerto += 1
        return puerto
    
    async def detener(self):
        if self.driver:
            self.driver.quit()
            self.running = False


# Ejemplo de uso
if __name__ == "__main__":
    controller = SeleniumController("DATA1")
    asyncio.run(controller.iniciar())
    asyncio.run(controller.detener())

