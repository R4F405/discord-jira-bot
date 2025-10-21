import os
import asyncio
from flask import Flask, request, jsonify
from datetime import datetime
import discord # Necesario para type hinting (discord.Client)

# --- Configuración del Canal (cargada desde el entorno) ---
DISCORD_CHANNEL_ID_STR = os.getenv("DISCORD_CHANNEL_ID")
DISCORD_CHANNEL_ID = 0
if DISCORD_CHANNEL_ID_STR:
    try:
        DISCORD_CHANNEL_ID = int(DISCORD_CHANNEL_ID_STR)
    except ValueError:
        print("Error: DISCORD_CHANNEL_ID no es un número válido.")
else:
    print("Error: DISCORD_CHANNEL_ID no está configurado en .env")


def create_webhook_app(bot: discord.Client):
    """
    Crea y configura la aplicación Flask, inyectando el cliente del bot.
    """
    app = Flask(__name__)
    
    # Almacenamos la referencia al bot.
    # NO almacenamos el loop aquí, porque el bot aún no se ha iniciado
    # y su loop (bot.loop) todavía no es válido.
    app.bot_client = bot
    # app.async_loop = bot.loop # <-- ESTA LÍNEA SE ELIMINA

    # --- Función para enviar notificaciones (Portado de BotJira.py) ---
    async def send_discord_notification(event_type, ticket_key, details=None):
        if not DISCORD_CHANNEL_ID:
            print("Error al notificar: DISCORD_CHANNEL_ID no es válido.")
            return

        channel = app.bot_client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            try:
                # Aquí está toda tu lógica de formato de mensajes original
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
                    await channel.send(f"━━━━━━━━━━━━━━━━━━━━━━━━\n❌ **Ticket eliminado en Jira** ❌\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
                elif event_type == "priority_updated":
                    await channel.send(
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ **Prioridad actualizada en ticket de Jira** ⚠️\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
                elif event_type == "attachment_added":
                    await channel.send(
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n📎 **Archivo adjunto añadido en ticket de Jira** 📎\n**Ticket:** {ticket_key}\n{details}\n━━━━━━━━━━━━━━━━━━━━━━━━")
                else:
                    # Fallback para eventos no manejados explícitamente
                    await channel.send(f"🔔 **Evento de Jira ({event_type})**\n**Ticket:** {ticket_key}\n{details}")
            except Exception as e:
                print(f"Error al enviar mensaje a Discord: {e}")
        else:
            print(f"Error: No se pudo encontrar el canal con ID {DISCORD_CHANNEL_ID}")

    # --- Ruta para recibir notificaciones (Portado de BotJira.py) ---
    @app.route("/webhook", methods=["POST"])
    def jira_webhook():
        try:
            print("✅ Webhook recibido desde Jira")
            data = request.json

            # --- OBTENER EL LOOP VÁLIDO ---
            # Obtenemos el loop del bot *ahora*, que ya está en ejecución
            # (a diferencia de cuando se creó la app).
            valid_loop = app.bot_client.loop

            # Extraer información relevante del evento
            event_type = data.get("webhookEvent")
            issue_data = data.get("issue", {})
            ticket_key = issue_data.get("key")

            if not ticket_key:
                # A veces, los webhooks son sobre proyectos, no issues
                print("Webhook ignorado (sin clave de issue)")
                return jsonify({"status": "ignored", "message": "No issue key found"}), 200

            user_name = data.get("user", {}).get("displayName", "Usuario desconocido")

            # --- Procesar eventos de comentarios ---
            if "comment_created" in event_type or "comment_updated" in event_type:
                comment = data.get("comment", {})
                comment_text = "Sin contenido"

                # Extraer el texto del comentario si está en formato estructurado
                if isinstance(comment.get("body"), dict) and "content" in comment["body"]:
                    try:
                        comment_text = ""
                        for block in comment["body"]["content"]:
                            if block["type"] == "paragraph":
                                for text_block in block.get("content", []):
                                    if text_block.get("type") == "text":
                                        comment_text += text_block.get("text", "") + "\n"
                        comment_text = comment_text.strip() or "Sin contenido"
                    except Exception as e:
                        print(f"Error al procesar el comentario: {e}")
                else:
                    comment_text = comment.get("body", "Sin contenido")

                details = f"**Comentado por:** {user_name}\n**Comentario:** {comment_text}"
                
                # ¡IMPORTANTE! Usamos 'run_coroutine_threadsafe' para llamar a
                # nuestra función async desde este hilo síncrono de Flask.
                asyncio.run_coroutine_threadsafe(
                    send_discord_notification("commented", ticket_key, details=details),
                    valid_loop # <-- USAR EL LOOP VÁLIDO
                )
                return jsonify({"status": "success"}), 200

            # --- Procesar eventos de actualización de tickets ---
            if "issue_updated" in event_type:
                changes = data.get("changelog", {}).get("items", [])
                if not changes:
                    return jsonify({"status": "ignored", "reason": "No changes detected"}), 200

                for change in changes:
                    field = change.get("field", "").lower()
                    from_value = change.get("fromString", "N/A")
                    to_value = change.get("toString", "N/A")

                    details = f"**Actualizado por:** {user_name}\n**Cambio:** {from_value} → {to_value}"
                    
                    event_map = {
                        "status": "updated",
                        "assignee": "assigned",
                        "description": "description_updated",
                        "summary": "summary_updated",
                        "priority": "priority_updated",
                        "attachment": "attachment_added"
                    }
                    
                    # Usamos 'get' para manejar campos que no mapeamos
                    mapped_event = event_map.get(field)
                    
                    if mapped_event:
                        # Si es un campo especial, ajustamos los detalles
                        if field == "description":
                            details = f"**Descripción actualizada por:** {user_name}"
                        elif field == "attachment":
                            details = f"**Archivo adjunto añadido por:** {user_name}\n**Archivo:** {to_value}"
                        
                        asyncio.run_coroutine_threadsafe(
                            send_discord_notification(mapped_event, ticket_key, details=details),
                            valid_loop # <-- USAR EL LOOP VÁLIDO
                        )

                return jsonify({"status": "success"}), 200

            # --- Muestra información cuando un ticket se crea ---
            if "issue_created" in event_type:
                issue = data.get("issue", {})
                fields = issue.get("fields", {})
                creador = fields.get("creator", {}).get("displayName", "Sin creador")
                asignado_data = fields.get("assignee")
                asignado = asignado_data.get("displayName") if asignado_data else "Sin asignar"
                resumen = fields.get("summary", "Sin resumen")
                estado = fields.get("status", {}).get("name", "Sin estado")

                detalles = (
                    f"**Resumen:** {resumen}\n"
                    f"**Estado inicial:** {estado}\n"
                    f"**Creado por:** {creador}\n"
                    f"**Asignado a:** {asignado}"
                )

                asyncio.run_coroutine_threadsafe(
                    send_discord_notification("created", ticket_key, details=detalles),
                    valid_loop # <-- USAR EL LOOP VÁLIDO
                )
                return jsonify({"status": "success"}), 200

            # --- Muestra información cuando se borra un ticket ---
            if "issue_deleted" in event_type:
                usuario = data.get("user", {}).get("displayName", "Usuario desconocido")
                # El issue completo no suele venir en 'deleted', así que somos genéricos
                detalles = f"**Eliminado por:** {usuario}"

                asyncio.run_coroutine_threadsafe(
                    send_discord_notification("deleted", ticket_key, details=detalles),
                    valid_loop # <-- USAR EL LOOP VÁLIDO
                )
                return jsonify({"status": "success"}), 200
            
            # Si llegamos aquí, es un evento que no manejamos
            print(f"Webhook ignorado (tipo de evento no manejado: {event_type})")
            return jsonify({"status": "ignored", "event": event_type}), 200
        
        except Exception as e:
            print(f"Error fatal al procesar el webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    return app