import sqlite3,datetime

def conectar():
    """Establece la conexión con la base de datos SQLite y asegura que las tablas existan."""
    conn = sqlite3.connect('sql/scripts.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scripts
                      (id TEXT PRIMARY KEY, nombre TEXT, estado BOOLEAN)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS acciones
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, id_xml TEXT, id_persona TEXT, fecha_hora TEXT, id_opcion TEXT, nombre_opcion TEXT)''')
    conn.commit()
    return conn

def insertar_script(id,nombre):
    """Inserta un nuevo script en la base de datos con un ID aleatorio y unico de letras y numeros."""
    nombre = str(nombre)
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO scripts (id,nombre, estado) VALUES (?, ?, ?)', (id,nombre, False))
    conn.commit()
    conn.close()

def consultar_scripts():
    """Consulta todos los ids y nombres de los scripts almacenados en la base de datos."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT id,nombre FROM scripts')
    scripts = cursor.fetchall()
    conn.close()
    return [{'id': script[0], 'nombre': script[1]} for script in scripts]

def eliminar_script(id):
    """Elimina un script de la base de datos por su nombre."""
    conn = conectar()
    cursor = conn.cursor()
    #eliminar todos los datos de el script de la tabla
    cursor.execute('DELETE FROM scripts WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def Iniciar_script_bd(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('Update scripts set estado = False where id = ?', (id,))
    scripts = cursor.fetchall()
    conn.close()
    return [script[0] for script in scripts]

def Detener_script_bd(id):
    conn = conectar()
    cursor = conn.cursor()
    #consulta para detener el script mediante el nombre
    cursor.execute('Update scripts set estado = True where id = ?', (id,))
    scripts = cursor.fetchall()
    conn.close()
    return [script[0] for script in scripts]

def buscar_script(nombre):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scripts WHERE nombre = ?', (nombre,))
    script = cursor.fetchone()
    conn.close()
    return script

def registrar_accion(id_xml, id_persona, id_opcion, nombre_opcion):
    """Registra una acción en la base de datos."""
    conn = conectar()
    cursor = conn.cursor()
    fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO acciones (id_xml, id_persona, fecha_hora, id_opcion, nombre_opcion) VALUES (?, ?, ?, ?, ?)',
                   (id_xml, id_persona, fecha_hora, id_opcion, nombre_opcion))
    conn.commit()
    conn.close()