# Discord-Jira Bot

Un bot de integración entre Discord y Jira que permite consultar información de tickets desde Discord y enviar notificaciones de eventos de Jira a canales de Discord.

## Características

- **Comandos de Discord**:
  - `!jira info`: Muestra información sobre los comandos disponibles
  - `!jira <ticket_id>`: Obtiene información detallada de un ticket específico
  - `!jira assigned <usuario>`: Lista los tickets asignados a un usuario específico
  - `!jira finished <usuario>`: Lista los tickets terminados o en QA por un usuario específico
  - `!jira dev <usuario>`: Lista los tickets en curso para un usuario específico

- **Notificaciones de Jira a Discord**:
  - Creación de tickets nuevos
  - Actualizaciones de tickets (cambios de estado, resumen, prioridad)
  - Comentarios en tickets
  - Cambios de asignación
  - Actualizaciones de descripción
  - Archivos adjuntos
  - Eliminación de tickets

## Requisitos

- Python 3.8+
- Una cuenta de Discord
- Una cuenta de Jira
- Un servidor Discord donde tengas permisos para añadir bots

## Dependencias

- discord.py
- requests
- flask
- python-dotenv

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/tu-usuario/discord-jira-bot.git
cd discord-jira-bot
```

2. Crea un entorno virtual e instala las dependencias:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/MacOS
source .venv/bin/activate

pip install -r requirements.txt
```

3. Configura las variables de entorno (ver sección "Configuración")

4. Ejecuta el bot:
```bash
python BotJira.py
```

## Configuración

### 1. Crear un archivo .env

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
DISCORD_TOKEN=tu_token_de_discord
JIRA_BASE_URL=https://tu-dominio.atlassian.net
JIRA_EMAIL=tu_email@ejemplo.com
JIRA_API_TOKEN=tu_token_api_jira
DISCORD_CHANNEL_ID=id_del_canal_discord
```

### 2. Obtener token de Discord

Para obtener el token de Discord:

1. Ve a [Discord Developer Portal](https://discord.com/developers/applications)
2. Haz clic en "New Application" y dale un nombre
3. Ve a la sección "Bot" en el panel lateral
4. Haz clic en "Add Bot"
5. Bajo el nombre del bot, haz clic en "Reset Token" y copia el token que se genera
6. Asegúrate de activar los "Privileged Gateway Intents":
   - MESSAGE CONTENT INTENT
   - PRESENCE INTENT
   - SERVER MEMBERS INTENT

### 3. Invitar el bot a tu servidor

1. En el [Discord Developer Portal](https://discord.com/developers/applications), selecciona tu aplicación
2. Ve a "OAuth2" → "URL Generator"
3. Selecciona los siguientes permisos:
   - En "SCOPES": bot
   - En "BOT PERMISSIONS": Send Messages, Read Message History, etc. (o simplemente "Administrator" para pruebas)
4. Copia la URL generada, pégala en tu navegador y selecciona el servidor donde quieres añadir el bot

### 4. Configurar tokens de Jira

Para obtener el token de API de Jira:

1. Inicia sesión en [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Ve a "Security" → "API token"
3. Haz clic en "Create API token"
4. Dale un nombre descriptivo (por ejemplo, "Discord Bot") y haz clic en "Create"
5. Copia el token generado

### 5. Obtener ID del canal de Discord

1. En Discord, ve a "Configuración de usuario" → "Avanzado"
2. Activa "Modo desarrollador"
3. Haz clic derecho en el canal donde quieres recibir las notificaciones y selecciona "Copiar ID"

### 6. Configurar Webhooks de Jira

Para que Jira envíe notificaciones a tu bot:

1. En Jira, ve a "Configuración" → "Sistema" → "Webhooks"
2. Haz clic en "Crear webhook"
3. Configura lo siguiente:
   - **Nombre**: Discord Bot
   - **URL**: `http://tu-servidor:8080/webhook` (necesitarás exponer tu servidor a internet o usar ngrok para pruebas)
   - **Eventos**: Selecciona los eventos que quieres que activen notificaciones (Creación de tickets, Comentarios, etc.)

### 7. Configurar ngrok para pruebas locales

Para pruebas locales, puedes usar ngrok para exponer tu servidor Flask a Internet y permitir que Jira envíe webhooks a tu aplicación:

1. Descarga e instala [ngrok](https://ngrok.com/download)
2. Crea una cuenta gratuita en ngrok y sigue las instrucciones para obtener tu token de autenticación
3. Autentica tu instalación de ngrok (solo necesitas hacerlo una vez):
   ```bash
   ngrok config add-authtoken TU_TOKEN_DE_NGROK
   ```
4. Inicia tu bot para que el servidor Flask esté ejecutándose en el puerto 8080
5. En otra terminal, ejecuta ngrok para exponer el puerto 8080:
   ```bash
   ngrok http 8080
   ```
6. Ngrok te proporcionará una URL pública (por ejemplo, `https://abc123.ngrok.io`)
7. Usa esta URL en la configuración del webhook de Jira:
   `https://abc123.ngrok.io/webhook`

**Nota**: Cada vez que inicies ngrok obtendrás una URL diferente, así que necesitarás actualizar la URL en la configuración del webhook de Jira si reinicias ngrok.

Para un entorno de producción, necesitarás un servidor con una IP pública o un servicio en la nube como Heroku, AWS, etc.

## Arquitectura

El bot funciona con dos componentes principales:

1. **Bot de Discord**: Escucha comandos en Discord y responde con información de Jira
2. **Servidor Flask**: Recibe webhooks de Jira y envía notificaciones a Discord

Ambos componentes se ejecutan concurrentemente utilizando hilos de Python.

## Personalización

Puedes personalizar:

- Los mensajes de respuesta en Discord
- El formato de las notificaciones 
- Los tipos de eventos que desencadenan notificaciones

## Solución de problemas

- **El bot no responde**: Verifica que el token de Discord sea correcto y que el bot tenga los permisos necesarios
- **No se reciben notificaciones de Jira**: Verifica que la URL del webhook sea accesible desde internet
- **Error de autenticación con Jira**: Verifica que el email y token de API sean correctos

## Seguridad

El archivo `.env` contiene información sensible y no debe ser compartido ni subido a repositorios públicos. Está incluido en `.gitignore` por defecto.

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## Contribuir

Las contribuciones son bienvenidas. Por favor, envía un pull request o abre un issue para discutir los cambios propuestos. 