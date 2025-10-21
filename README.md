# Discord-Jira Bot 🤖

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![discord.py](https://img.shields.io/badge/discord.py-library-7289DA.svg)](https://github.com/Rapptz/discord.py)

Un bot de integración para Discord y Jira que permite consultar información de tickets 🎫 desde Discord y enviar notificaciones de eventos de Jira a canales de Discord.

## ✨ Características

- **💻 Comandos de Aplicación (Slash Commands)**:
  - `/jira info`: Muestra información sobre los comandos disponibles.
  - `/jira ver <ticket_id>`: Obtiene información detallada de un ticket de Jira (ej. `ABC-123`).
  - `/jira pendientes <usuario>`: Lista tickets en 'BACKLOG' o 'SELECCIONADO PARA DESARROLLO'.
  - `/jira encurso <usuario>`: Lista los tickets que están 'EN CURSO'.
  - `/jira bloqueados <usuario>`: Lista los tickets en estado 'BLOCK'.
  - `/jira finalizados <usuario>`: Lista tickets en 'CODE REVIEW', 'QA' o 'LISTO'.

- **🔔 Notificaciones de Jira a Discord**:
  - Creación de nuevos tickets
  - Actualizaciones de tickets (cambios de estado, resumen, prioridad)
  - Comentarios en tickets
  - Cambios de asignación
  - Actualizaciones de descripción
  - Archivos adjuntos
  - Eliminación de tickets

## ✅ Requisitos

- Python 3.8+
- Una cuenta de Discord
- Una cuenta de Jira
- Un servidor de Discord donde tengas permisos para añadir bots

## 🔗 Dependencias

- `discord.py`
- `flask`
- `python-dotenv`
- `httpx`

## 🚀 Instalación

1.  Clona este repositorio:
    ```bash
    git clone [https://github.com/R4F405/discord-jira-bot.git](https://github.com/R4F405/discord-jira-bot.git)
    cd discord-jira-bot
    ```

2.  Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Linux/MacOS
    source .venv/bin/activate

    pip install -r requirements.txt
    ```

3.  Configura las variables de entorno (consulta la sección "⚙️ Configuración").

4.  Ejecuta el bot:
    ```bash
    python bot.py
    ```
    Deberías ver un mensaje indicando que tanto el bot como el servidor de webhooks están listos.

## ⚙️ Configuración

### 1. 📄 Crear un archivo .env

Crea un archivo `.env` en la raíz del proyecto (puedes copiar `.env.example`) con el siguiente contenido:

```
DISCORD_TOKEN=your_discord_token
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your_email@example.com
JIRA_API_TOKEN=your_jira_api_token
DISCORD_CHANNEL_ID=discord_channel_id
```

### 2. 🔑 Obtener Token de Discord

1.  Ve al [Portal de Desarrolladores de Discord](https://discord.com/developers/applications).
2.  Haz clic en "New Application" y dale un nombre.
3.  Navega a la sección "Bot" en el panel lateral.
4.  Haz clic en "Add Bot".
5.  Bajo el nombre del bot, haz clic en "Reset Token" y copia el token generado.
6.  **Importante**: Gracias al uso de Comandos de Aplicación (Slash Commands), **ya no necesitas habilitar los "Privileged Gateway Intents"** (como Message Content o Server Members) para la funcionalidad de los comandos.

### 3. 📨 Invitar el Bot a tu Servidor

1.  En el [Portal de Desarrolladores de Discord](https://discord.com/developers/applications), selecciona tu aplicación.
2.  Ve a "OAuth2" → "URL Generator".
3.  Selecciona los siguientes permisos:
    -   En "SCOPES": `bot` y `applications.commands`.
    -   En "BOT PERMISSIONS": `Send Messages` y `Read Message History` (para que pueda enviar notificaciones y leer comandos).
4.  Copia la URL generada, pégala en tu navegador y selecciona el servidor donde quieres añadir el bot.

### 4. 🔑 Configurar Tokens de Jira

Para obtener el token de API de Jira:

1.  Inicia sesión en [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens).
2.  Ve a "Security" → "API token".
3.  Haz clic en "Create API token".
4.  Dale un nombre descriptivo (ej. "Discord Bot") y haz clic en "Create".
5.  Copia el token generado.

### 5. 🆔 Obtener ID del Canal de Discord

1.  En Discord, ve a "Ajustes de Usuario" → "Avanzado".
2.  Habilita el "Modo de desarrollador".
3.  Haz clic derecho en el canal donde quieres recibir las notificaciones y selecciona "Copiar ID".

### 6. 🎣 Configurar Webhooks de Jira

Para que Jira envíe notificaciones a tu bot:

1.  En Jira, ve a "Settings" (engranaje) → "System" → "Webhooks" (bajo "Advanced").
2.  Haz clic en "Create a Webhook".
3.  Configura lo siguiente:
    -   **Name**: Discord Bot
    -   **URL**: `http://tu-servidor-publico:8080/webhook`. (Necesitarás exponer tu servidor a internet).
    -   **Events**: Selecciona los eventos que quieres que activen notificaciones (Issue created, Comment created, etc.).

### 7. 🧪 Configurar ngrok para Pruebas Locales

Para pruebas locales, puedes usar [ngrok](https://ngrok.com/download) para exponer tu servidor Flask (que se ejecuta en el puerto 8080) a internet:

1.  Descarga e instala ngrok.
2.  Autentica tu cliente de ngrok (solo se hace una vez):
    ```bash
    ngrok config add-authtoken TU_TOKEN_DE_NGROK
    ```
3.  Inicia tu bot (`python bot.py`) para que el servidor Flask esté corriendo en el puerto 8080.
4.  En otra terminal, ejecuta ngrok para exponer el puerto 8080:
    ```bash
    ngrok http 8080
    ```
5.  Ngrok te dará una URL pública (ej. `https://abc123.ngrok.io`).
6.  Usa esta URL en la configuración de tu Webhook de Jira:
    `https://abc123.ngrok.io/webhook`

**Nota**: Cada vez que reinicies ngrok, la URL cambiará, por lo que deberás actualizarla en Jira.

## 🏗️ Arquitectura

El bot opera con dos componentes principales que se ejecutan concurrentemente usando `asyncio`:

1.  **Bot de Discord (discord.py)**: Se conecta a Discord, carga el Cog de comandos (`cogs/jira_commands.py`) y sincroniza los Comandos de Aplicación (/).
2.  **Servidor Web (Flask)**: Recibe los webhooks de Jira en la ruta `/webhook`. Utiliza `asyncio.run_coroutine_threadsafe` para enviar notificaciones al canal de Discord de forma segura desde el hilo de Flask.

El archivo principal `bot.py` se encarga de iniciar y gestionar ambas tareas.

## 🛠️ Troubleshooting

-   **Bot no responde a comandos (/)**: Asegúrate de haber invitado al bot con los scopes `bot` y `applications.commands`.
-   **No se reciben notificaciones de Jira**:
    -   Verifica que la URL del webhook en Jira sea correcta y esté accesible desde internet (puedes usar ngrok para probar).
    -   Asegúrate de que `DISCORD_CHANNEL_ID` en tu `.env` sea correcto.
-   **Error de autenticación con Jira**: Verifica que `JIRA_BASE_URL`, `JIRA_EMAIL` y `JIRA_API_TOKEN` en tu `.env` sean correctos.

## 🔒 Seguridad

El archivo `.env` contiene información sensible y no debe ser compartido ni subido a repositorios públicos. Está incluido en `.gitignore` por defecto.

## 📜 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.