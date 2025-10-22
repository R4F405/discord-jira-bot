import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from web.webhook_server import create_webhook_app
import waitress

# --- Cargar configuración ---
load_dotenv()

# Importa el creador de la app Flask desde nuestro módulo web
from web.webhook_server import create_webhook_app

# --- Configuración del Bot ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN no encontrado. Asegúrate de tener un .env válido.")
    exit()

# Definimos los 'intents' (intenciones) básicos.
intents = discord.Intents.default()

# ¡OJO! Ya no necesitamos 'intents.message_content = True'
# porque estamos usando Slash Commands. Esto es mucho mejor
# para la privacidad y cumple con las políticas de Discord.

# Usamos commands.Bot, que es una subclase de discord.Client
# pero con soporte para comandos.
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Servidor Web (Flask) ---
# Creamos la instancia de Flask y le pasamos el 'bot'
# para que pueda enviar mensajes desde los webhooks.
flask_app = create_webhook_app(bot)

@bot.event
async def on_ready():
    """Se ejecuta cuando el bot se conecta exitosamente a Discord."""
    print(f'Bot conectado como {bot.user}')
    print("-----------------------------------------")
    print("✅ Bot de Discord listo.")
    print(f"✅ Servidor de Webhooks (Flask) corriendo en segundo plano.")
    print("-----------------------------------------")

async def setup_hook():
    """
    Este hook se ejecuta después del login pero antes de 'on_ready'.
    Es el lugar ideal para cargar extensiones (Cogs) y sincronizar
    nuestro árbol de comandos de aplicación (Slash Commands).
    """
    print("Ejecutando setup_hook...")
    
    # 1. Cargar el Cog que contiene nuestros comandos
    try:
        await bot.load_extension("cogs.jira_commands")
        print("Módulo (Cog) 'jira_commands' cargado exitosamente.")
    except Exception as e:
        print(f"Error al cargar el Cog 'jira_commands': {e}")
        return

    # 2. Sincronizar el árbol de comandos
    # Esto registra los comandos "/" en Discord.
    try:
        # 'synced' contendrá la lista de comandos registrados
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos de aplicación.")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")

# Adjuntamos el hook al bot
bot.setup_hook = setup_hook

async def run_flask_app():
    """
    Ejecuta la app de Flask (que es síncrona) en el 'executor' de
    asyncio para no bloquear el hilo principal del bot.
    """
    try:
        # Usamos waitress.serve en lugar de flask_app.run para producción
        await bot.loop.run_in_executor(
            None, 
            lambda: waitress.serve(flask_app, host='0.0.0.0', port=8080)
        )
    except Exception as e:
        print(f"Error al iniciar el servidor Flask: {e}")

async def main():
    """Función principal para arrancar el bot y el servidor web."""
    if not DISCORD_TOKEN:
        print("El token de Discord no está configurado. Saliendo.")
        return
        
    try:
        # asyncio.gather nos permite ejecutar ambas tareas concurrentemente
        await asyncio.gather(
            bot.start(DISCORD_TOKEN), # Tarea 1: Conectar el bot a Discord
            run_flask_app()            # Tarea 2: Iniciar el servidor Flask
        )
    except KeyboardInterrupt:
        print("\nCerrando bot...")
    finally:
        if not bot.is_closed():
            await bot.close()
        print("Bot desconectado. Saliendo.")

if __name__ == "__main__":
    # asyncio.run() es la forma moderna de iniciar
    # un programa asíncrono en Python.
    asyncio.run(main())