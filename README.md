# Chat_Bot_PS

# Separador de mensajes nuevos
```xpath
//div[@class='_agtb focusable-list-item' and @tabindex='-1']/span[@class='_agtk' and @aria-live='polite']
```

# General
### a) Números que tienen nombre:
```xpath
//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and string-length(text()) > 0 and not(starts-with(text(), '+'))]
```
### b) Números que no tienen nombre (solo número de teléfono):
```xpath
//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and starts-with(text(), '+')]
```
### c) Grupos:
```xpath
//div[@class='_ak8q']/span[contains(@class, 'x1iyjqo2') and not(starts-with(text(), '+'))]
```
### d) Otros elementos en la lista (por ejemplo, "Yo"):
```xpath
//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1rg5ohu') and text()='Yo']
```
### XPath general para todos los chats en la lista:
```xpath
//div[@class='x10l6tqk xh8yej3 x1g42fcv']
```

# No leidos
### a) Números que tienen nombre:
```xpath
//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and not(starts-with(text(), '+'))]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[(@aria-label='No leídos' or contains(@aria-label, 'no leídos'))]
```

### b) Números que no tienen nombre (solo número de teléfono):
```xpath
//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1iyjqo2') and starts-with(text(), '+')]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[(@aria-label="No leídos" or contains(@aria-label, "no leídos"))]
```

### c) Grupos:
```xpath
//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_ak8q']/span[contains(@class, 'x1iyjqo2') and not(starts-with(text(), '+'))]/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[@aria-label="No leídos"]
```

### d) Otros elementos en la lista (por ejemplo, "Yo"):
```xpath
//div[@class='x10l6tqk xh8yej3 x1g42fcv']//div[@class='_aou8 _aj_h']/span[contains(@class, 'x1rg5ohu') and text()='Yo']/ancestor::div[@class='x10l6tqk xh8yej3 x1g42fcv']//span[@aria-label="No leídos"]
```
# Mensajes dentro de el Chat:

### Mensajes de la otra persona (message-in):
```xpath
//div[contains(@class, 'message-in') or contains(@class, 'response')]
```
### Tus mensajes (message-out):
```xpath
//div[contains(@class, 'message-out') or contains(@class, 'response')]
```
### Mensajes en general (todos los mensajes):
```xpath
//div[contains(@class, 'message') or contains(@class, 'response')]
```
## Diferencias
1. **Mensaje de la otra persona (solo texto, sin el indicador de respuesta)**:
   ```xpath
   //div[contains(@class, 'message-in')]//div[contains(@class, '_amk4') and contains(@class, '_amkd') and contains(@class, '_amk5') and not(.//span[@aria-label='Tú:'])]
   ```

2. **Mensaje de la otra persona (con imagen, sin el indicador de respuesta)**:
   ```xpath
   //div[contains(@class, 'message-in')]//div[contains(@class, '_amk4') and contains(@class, '_amkt') and contains(@class, '_amk5') and not(.//span[@aria-label='Tú:'])]
   ```

3. **Mensaje mío (solo texto)**:
   ```xpath
   //div[contains(@class, 'message-out')]//div[contains(@class, '_amk4') and contains(@class, '_amkd') and not(contains(@class, '_amk5'))]
   ```

4. **Mensaje mío (respondiendo a un mensaje de la otra persona, con el indicador de respuesta)**:
   ```xpath
   //div[contains(@class, 'message-out')]//div[contains(@class, '_amk4') and contains(@class, '_amkd') and contains(@class, '_amk5')]//span[@aria-label='Tú:']
   ```

5. **Mensaje mío (con archivo)**:
   ```xpath
   //div[contains(@class, 'message-out')]//div[contains(@class, '_amk4') and contains(@class, '_amkm')]
   ```

6. **Mensaje mío (con imagen)**:
   ```xpath
   //div[contains(@class, 'message-out')]//div[contains(@class, '_amk4') and contains(@class, '_amkt')]
   ```

7. **Mensaje mío (con video)**:
   ```xpath
   //div[contains(@class, 'message-out')]//div[contains(@class, '_amk4') and contains(@class, '_amkv')]
   ```

8. **Mensaje mío (con sticker)**:
   ```xpath
   //div[contains(@class, 'message-out')]//div[contains(@class, '_amk4') and contains(@class, '_amk9')]
   ```

# Estado de mis Mensajes
### Mensaje enviado:
```xpath
//div[contains(@class, 'message-out')]//span[@aria-label=' Enviado ']
```
### Mensaje entregado:
```xpath
//div[contains(@class, 'message-out')]//span[@aria-label=' Entregado ']
```
### Mensaje leído:
```xpath
//div[contains(@class, 'message-out')]//span[@aria-label=' Leído ']
```