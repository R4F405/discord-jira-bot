import os
import requests
from dotenv import load_dotenv
import discord
from flask import Flask, request, jsonify
import threading
import asyncio
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configuración del bot
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Autenticación básica para Jira
JIRA_AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)

# Intents necesarios para el bot
intents = discord.Intents.default()
intents.message_content = True

# Crear el cliente de Discord
client = discord.Client(intents=intents)

# Crear la aplicación Flask
app = Flask(__name__)


# Función para manejar el comando !jira info (Informacion de comandos)
async def handle_jira_info_command(message):
    info_message = (
        "**Comandos disponibles:**\n\n"
        "`!jira <ticket_id>` - Obtiene información detallada de un ticket de Jira.\n"
        "`!jira assigned <username>` - Lista los tickets asignados a un usuario específico.\n"
        "`!jira finished <username>` - Lista los tickets terminados o en QA por un usuario específico.\n"
        "`!jira dev <username>` - Lista los tickets en curso para un usuario específico.\n"
        "`!jira info` - Muestra información sobre los comandos disponibles y cómo usarlos.\n\n"
        "**Ejemplos de uso:**\n"
        "`!jira ABC-123` - Obtiene información del ticket ABC-123.\n"
        "`!jira assigned john_doe` - Lista los tickets asignados a john_doe.\n"
        "`!jira finished john_doe` - Lista los tickets terminados o en QA por john_doe.\n"
        "`!jira dev john_doe` - Lista los tickets en curso para john_doe.\n"
    )
    await message.reply(info_message)

# Función para manejar el comando !jira
async def handle_jira_command(message):
    parts = message.content.split()
    if len(parts) < 2:
        await message.reply("Por favor, proporciona el ID del ticket de Jira.")
        return

    ticket_key = parts[1]

    try:
        response = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/issue/{ticket_key}",
            auth=JIRA_AUTH,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            issue = response.json()

            # Extraer campos y manejar campos vacíos
            summary = issue["fields"].get("summary", "Sin resumen")
            status = issue["fields"]["status"].get("name", "Sin estado")

            creator = issue["fields"].get("creator")
            creator_name = creator.get("displayName", "Sin creador") if creator else "Sin creador"

            created_date = issue["fields"].get("created", "Sin fecha de creación")

            assignee = issue["fields"].get("assignee")
            assignee_name = assignee.get("displayName", "Sin asignar") if assignee else "Sin asignar"

            description = issue["fields"].get("description", "Sin descripción")

            # Procesar la descripción si está en formato estructurado
            if isinstance(description, dict) and "content" in description:
                try:
                    # Extraer el texto de la descripción
                    description_text = ""
                    for block in description["content"]:
                        if block["type"] == "paragraph":
                            for text_block in block["content"]:
                                if text_block["type"] == "text":
                                    description_text += text_block["text"] + "\n"
                    description = description_text.strip() or "Sin descripción"
                except Exception as e:
                    print(f"Error al procesar la descripción del ticket {ticket_key}: {e}")
                    description = "Sin descripción"

            # Formatear fecha para que sea legible
            if created_date != "Sin fecha de creación":
                created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y - %H:%M:%S")

            # Responder con información detallada del ticket
            await message.reply(
                f"**Ticket:** {ticket_key}\n"
                f"**Resumen:** {summary}\n"
                f"**Estado:** {status}\n"
                f"**Creado por:** {creator_name}\n"
                f"**Fecha de creación:** {created_date}\n"
                f"**Asignado a:** {assignee_name}\n"
                f"**Descripción:** {description}"
            )
        else:
            await message.reply("No se pudo encontrar el ticket de Jira. Verifica el ID o inténtalo más tarde.")

    except Exception as e:
        print(f"Excepción al consultar el ticket {ticket_key}: {e}")
        await message.reply("Ocurrió un error al consultar el ticket de Jira.")

# Función para manejar el comando !jira assigned usuario
async def handle_jira_assigned_command(message):
    parts = message.content.split(' ', 2)  # Dividir en máximo 3 partes
    if len(parts) < 3:
        await message.reply("Por favor, proporciona el nombre de usuario de Jira. Ejemplo: `!jira assigned username`")
        return

    username = parts[2]

    try:
        # Construir la consulta JQL para buscar tickets asignados al usuario
        # Usando operador '=' en lugar de '~' para mayor compatibilidad
        jql_query = f'assignee = "{username}" AND resolution = Unresolved ORDER BY updated DESC'

        # Hacer la solicitud a la API de Jira
        response = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/search",
            auth=JIRA_AUTH,
            params={"jql": jql_query, "maxResults": 10},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                await message.reply(f"No se encontraron tickets asignados a '{username}'.")
                return

            # Crear un resumen de los tickets encontrados
            response_message = f"**Tickets asignados a {username}:**\n\n"

            for issue in issues:
                key = issue.get("key")
                summary = issue["fields"].get("summary", "Sin resumen")
                status = issue["fields"]["status"].get("name", "Sin estado")

                response_message += f"**{key}** - {summary} (Estado: {status})\n"

            if len(issues) == 30:
                response_message += "\n*Se muestran los 30 tickets más recientes de " + username +". Puede haber más resultados.*"

            await message.reply(response_message)
        elif response.status_code == 400:
            # Posible error en la consulta JQL
            error_data = response.json()
            error_message = error_data.get("errorMessages", ["Error desconocido"])[0]
            await message.reply(f"Error en la consulta: {error_message}")
        else:
            await message.reply(f"No se pudo realizar la búsqueda. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Excepción al buscar tickets asignados a {username}: {e}")
        await message.reply("Ocurrió un error al consultar los tickets asignados.")

# Función para manejar el comando !jira finished usuario
async def handle_jira_finished_command(message):
    parts = message.content.split(' ', 2)  # Dividir en máximo 3 partes
    if len(parts) < 3:
        await message.reply("Por favor, proporciona el nombre de usuario de Jira. Ejemplo: `!jira finished username`")
        return

    username = parts[2]

    try:
        # Modificar la consulta JQL para incluir tickets en Done y en QA
        jql_query = f'assignee = "{username}" AND status IN ("Done", "QA") ORDER BY updated DESC'

        # Hacer la solicitud a la API de Jira
        response = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/search",
            auth=JIRA_AUTH,
            params={"jql": jql_query, "maxResults": 10},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                await message.reply(f"No se encontraron tickets terminados o en QA por '{username}'.")
                return

            # Crear un resumen de los tickets encontrados
            response_message = f"**Tickets terminados o en QA por {username}:**\n\n"

            for issue in issues:
                key = issue.get("key")
                summary = issue["fields"].get("summary", "Sin resumen")
                status = issue["fields"]["status"].get("name", "Sin estado")
                resolved_date = issue["fields"].get("resolutiondate", "Sin fecha")

                # Formatear fecha de resolución si existe
                if resolved_date and resolved_date != "Sin fecha":
                    try:
                        resolved_date = datetime.strptime(resolved_date, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y")
                        date_info = f" (Completado: {resolved_date})"
                    except:
                        date_info = ""
                else:
                    date_info = ""

                # Incluir estado en la respuesta para distinguir entre QA y Done
                response_message += f"**{key}** - {summary} (Estado: {status}){date_info}\n"

            if len(issues) == 10:
                response_message += "\n*Se muestran los 10 tickets más recientes terminados o en QA por " + username + ". Puede haber más resultados.*"

            await message.reply(response_message)
        elif response.status_code == 400:
            # Posible error en la consulta JQL
            error_data = response.json()
            error_message = error_data.get("errorMessages", ["Error desconocido"])[0]
            await message.reply(f"Error en la consulta: {error_message}")
        else:
            await message.reply(f"No se pudo realizar la búsqueda. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Excepción al buscar tickets terminados por {username}: {e}")
        await message.reply("Ocurrió un error al consultar los tickets terminados.")

# Función para manejar el comando !jira dev usuario
async def handle_jira_dev_command(message):
    parts = message.content.split(' ', 2)  # Dividir en máximo 3 partes
    if len(parts) < 3:
        await message.reply("Por favor, proporciona el nombre de usuario de Jira. Ejemplo: `!jira dev username`")
        return

    username = parts[2]

    try:
        # Construir la consulta JQL para buscar tickets en la columna "En curso" asignados al usuario
        jql_query = f'assignee = "{username}" AND status = "In Progress" ORDER BY updated DESC'

        # Hacer la solicitud a la API de Jira
        response = requests.get(
            f"{JIRA_BASE_URL}/rest/api/3/search",
            auth=JIRA_AUTH,
            params={"jql": jql_query, "maxResults": 10},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])

            if not issues:
                await message.reply(f"No se encontraron tickets en curso para '{username}'.")
                return

            # Crear un resumen de los tickets encontrados
            response_message = f"**Tickets en curso para {username}:**\n\n"

            for issue in issues:
                key = issue.get("key")
                summary = issue["fields"].get("summary", "Sin resumen")
                status = issue["fields"]["status"].get("name", "Sin estado")

                response_message += f"**{key}** - {summary} (Estado: {status})\n"

            if len(issues) == 10:
                response_message += "\n*Se muestran los 10 tickets más recientes en curso para " + username + ". Puede haber más resultados.*"

            await message.reply(response_message)
        elif response.status_code == 400:
            # Posible error en la consulta JQL
            error_data = response.json()
            error_message = error_data.get("errorMessages", ["Error desconocido"])[0]
            await message.reply(f"Error en la consulta: {error_message}")
        else:
            await message.reply(f"No se pudo realizar la búsqueda. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Excepción al buscar tickets en curso para {username}: {e}")
        await message.reply("Ocurrió un error al consultar los tickets en curso.")

# Función para enviar notificaciones a Discord
async def send_discord_notification(event_type, ticket_key, details=None):
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        if event_type == "created":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n🆕 **Nuevo ticket creado en Jira** 🆕\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "updated":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n🔄 **Ticket actualizado en Jira** 🔄\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "commented":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n💬 **Nuevo comentario en ticket de Jira** 💬\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "assigned":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n👤 **Asignación actualizada en ticket de Jira** 👤\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "description_updated":
            await channel.send(
                f"📝 **━━━━━━━━━━━━━━━━━━━━━━━━\nDescripción actualizada en ticket de Jira** 📝\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "summary_updated":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n📋 **Resumen actualizado en ticket de Jira** 📋\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "deleted":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n❌ **Ticket eliminado en Jira** ❌\n**Ticket:** {ticket_key}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "configured":
            await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n⚙️ **Ticket configurado en Jira** ⚙️\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "priority_updated":
            await channel.send(
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ **Prioridad actualizada en ticket de Jira** ⚠️\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
        elif event_type == "attachment_added":
            await channel.send(
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n📎 **Archivo adjunto añadido en ticket de Jira** 📎\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")


# Ruta para recibir notificaciones de Jira
@app.route("/webhook", methods=["POST"])
def jira_webhook():
    try:
        print("✅ Webhook recibido desde Jira")
        print(request.json)  # Esto te muestra el contenido completo

        data = request.json

        # Extraer información relevante del evento
        event_type = data.get("webhookEvent")
        issue_data = data.get("issue", {})
        ticket_key = issue_data.get("key")

        if not ticket_key:
            return jsonify({"status": "error", "message": "No se encontró la clave del ticket"}), 400

        # Obtener el usuario que realizó la acción
        user_name = data.get("user", {}).get("displayName", "Usuario desconocido")

        # Procesar eventos de comentarios
        if "comment_created" in event_type or "comment_updated" in event_type:
            comment = data.get("comment", {})
            comment_text = "Sin contenido"

            # Extraer el texto del comentario si está en formato estructurado
            if isinstance(comment.get("body"), dict) and "content" in comment["body"]:
                try:
                    comment_text = ""
                    for block in comment["body"]["content"]:
                        if block["type"] == "paragraph":
                            for text_block in block["content"]:
                                if text_block["type"] == "text":
                                    comment_text += text_block["text"] + "\n"
                    comment_text = comment_text.strip() or "Sin contenido"
                except Exception as e:
                    print(f"Error al procesar el comentario: {e}")
            else:
                comment_text = comment.get("body", "Sin contenido")

            details = f"**Comentado por:** {user_name}\n**Comentario:** {comment_text}"

            asyncio.run_coroutine_threadsafe(
                send_discord_notification("commented", ticket_key, details=details),
                client.loop
            )
            return jsonify({"status": "success"}), 200

        # Procesar eventos de actualización de tickets
        if "issue_updated" in event_type:
            changes = data.get("changelog", {}).get("items", [])

            # Si no hay cambios, salir
            if not changes:
                return jsonify({"status": "ignored", "reason": "No changes detected"}), 200

            # Procesar cada tipo de cambio
            for change in changes:
                field = change.get("field", "")
                from_value = change.get("fromString", "N/A")
                to_value = change.get("toString", "N/A")

                # Cambio de estado
                if field == "status":
                    details = f"**Estado cambiado por:** {user_name}\n**Cambio:** {from_value} → {to_value}"
                    asyncio.run_coroutine_threadsafe(
                        send_discord_notification("updated", ticket_key, details=details),
                        client.loop
                    )

                # Cambio de asignación
                elif field == "assignee":
                    details = f"**Asignación cambiada por:** {user_name}\n**Cambio:** {from_value} → {to_value}"
                    asyncio.run_coroutine_threadsafe(
                        send_discord_notification("assigned", ticket_key, details=details),
                        client.loop
                    )

                # Cambio de descripción
                elif field == "description":
                    details = f"**Descripción actualizada por:** {user_name}"
                    asyncio.run_coroutine_threadsafe(
                        send_discord_notification("description_updated", ticket_key, details=details),
                        client.loop
                    )

                # Cambio de resumen (título)
                elif field == "summary":
                    details = f"**Resumen actualizado por:** {user_name}\n**Cambio:** {from_value} → {to_value}"
                    asyncio.run_coroutine_threadsafe(
                        send_discord_notification("summary_updated", ticket_key, details=details),
                        client.loop
                    )

                # Cambio de prioridad
                elif field == "priority":
                    details = f"**Prioridad actualizada por:** {user_name}\n**Cambio:** {from_value} → {to_value}"
                    asyncio.run_coroutine_threadsafe(
                        send_discord_notification("priority_updated", ticket_key, details=details),
                        client.loop
                    )

                # Archivos adjuntos
                elif field == "Attachment":
                    details = f"**Archivo adjunto añadido por:** {user_name}\n**Archivo:** {to_value}"
                    asyncio.run_coroutine_threadsafe(
                        send_discord_notification("attachment_added", ticket_key, details=details),
                        client.loop
                    )

            return jsonify({"status": "success"}), 200

        # Muestra información cuando un ticket se crea
        if "issue_created" in event_type:
            issue = data.get("issue", {})
            fields = issue.get("fields", {})

            creador = fields.get("creator", {}).get("displayName", "Sin creador")

            # ⚠️ Aquí puede estar en None, así que hay que comprobarlo primero
            asignado_data = fields.get("assignee")
            asignado = asignado_data.get("displayName") if asignado_data else "Sin asignar"

            resumen = fields.get("summary", "Sin resumen")
            estado_data = fields.get("status")
            estado = estado_data.get("name") if estado_data else "Sin estado"

            ticket_key = issue.get("key", "Sin clave")

            detalles = (
                f"**Resumen:** {resumen}\n"
                f"**Estado inicial:** {estado}\n"
                f"**Creado por:** {creador}\n"
                f"**Asignado a:** {asignado}"
            )

            asyncio.run_coroutine_threadsafe(
                send_discord_notification("created", ticket_key, details=detalles),
                client.loop
            )
            return jsonify({"status": "success"}), 200

        # Muestra información cuando se borra un ticket
        if "issue_deleted" in event_type:
            issue = data.get("issue") or {}
            fields = issue.get("fields") or {}

            resumen = fields.get("summary", "Sin resumen")
            ticket_key = issue.get("key", "Sin clave")

            usuario = data.get("user", {}).get("displayName", "Usuario desconocido")

            detalles = (
                f"**Resumen:** {resumen}\n"
                f"**Eliminado por:** {usuario}"
            )

            asyncio.run_coroutine_threadsafe(
                send_discord_notification("deleted", ticket_key, details=detalles),
                client.loop
            )
            return jsonify({"status": "success"}), 200

        return jsonify({"status": "ignored"}), 200
    except Exception as e:
        print(f"Error al procesar el webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# Evento cuando el bot está listo
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')


# Evento para escuchar mensajes
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!jira info'):
        await handle_jira_info_command(message)

    elif message.content.startswith('!jira assigned'):
        await handle_jira_assigned_command(message)

    elif message.content.startswith('!jira finished'):
        await handle_jira_finished_command(message)

    elif message.content.startswith('!jira dev'):
        await handle_jira_dev_command(message)

    elif message.content.startswith('!jira '):
        await handle_jira_command(message)


# Iniciar el bot y el servidor Flask
if __name__ == "__main__":
    # Iniciar el bot de Discord en un hilo separado
    def run_discord_bot():
        client.run(DISCORD_TOKEN)


    # Iniciar el servidor Flask en un hilo separado
    def run_flask_app():
        app.run(port=8080)


    # Ejecutar ambos en hilos separados
    discord_thread = threading.Thread(target=run_discord_bot)
    flask_thread = threading.Thread(target=run_flask_app)

    discord_thread.start()
    flask_thread.start()

    # Esperar a que ambos hilos terminen
    discord_thread.join()
    flask_thread.join()