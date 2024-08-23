import mysql.connector

# Conectar a la base de datos MySQL
conexion = mysql.connector.connect(
    host="0.tcp.ngrok.io",           # Dirección del túnel de ngrok
    port=12515,                      # Puerto del túnel de ngrok
    user="practis",                 # Usuario de MySQL
    password="aprendepracticando",  # Contraseña de MySQL
    database="prueba"               # Nombre de la base de datos
)

cursor = conexion.cursor()

# insertar datos en la tabla prueba
verificar = True
crear_tabla = True
if crear_tabla:
    #crear tabla
    cursor.execute("CREATE TABLE empleados (id INT AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(255), apellido VARCHAR(255), edad INT, salario FLOAT)")
    cursor.execute("INSERT INTO empleados (nombre, apellido, edad, salario) VALUES ('Juan', 'Pérez', 30, 30000)")
    cursor.execute("INSERT INTO empleados (nombre, apellido, edad, salario) VALUES ('María', 'González', 25, 25000)")
    cursor.execute("INSERT INTO empleados (nombre, apellido, edad, salario) VALUES ('Carlos', 'López', 35, 35000)")
    verificar = True
else:
    # 1. Consultar todos los registros de la tabla Autores
    cursor.execute("SELECT * FROM Autores")
    autores = cursor.fetchall()
    print("Autores:")
    for autor in autores:
        print(autor)

    # 2. Consultar todos los registros de la tabla Libros
    cursor.execute("SELECT * FROM Libros")
    libros = cursor.fetchall()
    print("\nLibros:")
    for libro in libros:
        print(libro)

    # 3. Consultar todos los registros de la tabla Ventas
    cursor.execute("SELECT * FROM Ventas")
    ventas = cursor.fetchall()
    print("\nVentas:")
    for venta in ventas:
        print(venta)

    # 4. Consultar los datos relacionados entre las tablas Autores, Libros, y Ventas
    cursor.execute("""
        SELECT
            Libros.titulo AS Título,
            Autores.nombre AS Autor,
            Ventas.cantidad AS Cantidad_Vendida,
            Ventas.fecha AS Fecha_Venta
        FROM
            Ventas
        INNER JOIN
            Libros ON Ventas.id_libro = Libros.id_libro
        INNER JOIN
            Autores ON Libros.id_autor = Autores.id_autor
    """)
    relacionados = cursor.fetchall()
    print("\nDatos Relacionados:")
    for fila in relacionados:
        print(fila)

if verificar:
    # Consultar los datos de la tabla para verificar
    cursor.execute("SELECT * FROM empleados")
    resultados = cursor.fetchall()
    # Imprimir los resultados
    for fila in resultados:
        print(fila)
else:
    # Consultar los datos de la tabla
    cursor.execute("SELECT * FROM usuarios")
    resultados = cursor.fetchall()
    # Imprimir los resultados
    for fila in resultados:
        print(fila)

# Confirmar los cambios
conexion.commit()

# Cerrar la conexión
cursor.close()
conexion.close()
