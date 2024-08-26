import requests

# Leer el contenido del archivo mensaje.txt
with open('mensaje.txt', 'r', encoding='utf-8') as file:
    mensaje_usuario = file.read()

url = "http://localhost:1234/v1/chat/completions"
headers = {
    "Content-Type": "application/json"
}
data = {
    "messages": [
        {"role": "system", "content": "Tu tarea es realizar modificaciones sutiles y ligeras a los mensajes relacionados con cursos que recibas. Sigue estas reglas: Mantén el tema y la intención original del mensaje. Haz cambios ligeros usando sinónimos y reformulando frases de manera sutil para mejorar el mensaje sin alterarlo drásticamente. Incorpora algunos emojis relevantes para destacar puntos clave, sin exagerar su uso. Respeta y mantén intactos los enlaces, fechas y horas proporcionados. Mantén la estructura del mensaje, incluyendo saltos de línea. No agregues información nueva ni promociones adicionales. Mejora ligeramente el llamado a la acción final para hacerlo más atractivo, sin cambiar su esencia. Responde únicamente con el mensaje modificado, sin comentarios adicionales. Asegúrate de que el mensaje completo esté en español. Evita cambios exagerados; las modificaciones deben ser leves y naturales. Cada respuesta que des debe de ser diferente."},
        {"role": "user", "content": mensaje_usuario}
    ],
    "temperature": 0.7,
    "max_tokens": 100
}

response = requests.post(url, headers=headers, json=data)

# Extraer y mostrar solo la respuesta de la IA
mensaje_modificado = response.json()['choices'][0]['message']['content']
print(mensaje_modificado)