from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, socket, asyncio

class SeleniumController:
    def __init__(self, nombre_script):
        if not isinstance(nombre_script, str):
            raise ValueError("El nombre del script debe ser una cadena")
        
        self.ruta_screenshot = 'DATA/resource/screenshot/'
        self.nombre_script = nombre_script
        self.puerto = self.convertir_nombre_a_puerto(nombre_script)
        self.driver = None
        self.running = False
        self.crear_directorio(self.ruta_screenshot)

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
            await self.driver.get('https://www.youtube.com/')
            self.running = True

            elemento = await WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]'))
            )
            elemento.screenshot(f'{self.ruta_screenshot}{self.nombre_script}screenshot.png')

        except Exception as e:
            self.running = False
            print(f"Error: {e}")

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
    
    def crear_directorio(self, ruta):
        if not os.path.exists(ruta):
            os.makedirs(ruta)

    async def detener(self):
        if self.driver:
            self.driver.quit()
            self.running = False