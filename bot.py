import os
import sys
import asyncio
import threading
import discord
from discord.ext import commands
from dotenv import load_dotenv
import waitress

load_dotenv()

from web.webhook_server import create_webhook_app

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", 8080))
if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN no encontrado. Asegúrate de tener un .env válido.")
    exit()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
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
    Hook ejecutado después del login pero antes de 'on_ready'.
    Carga extensiones y sincroniza comandos de aplicación.
    """
    print("Ejecutando setup_hook...")
    
    try:
        await bot.load_extension("cogs.jira_commands")
        print("Módulo (Cog) 'jira_commands' cargado exitosamente.")
    except Exception as e:
        print(f"Error al cargar el Cog 'jira_commands': {e}")
        return

    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos de aplicación.")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")

bot.setup_hook = setup_hook

def run_flask_app():
    """Ejecuta el servidor de webhooks (Waitress) en un hilo en segundo plano."""
    try:
        waitress.serve(flask_app, host='0.0.0.0', port=PORT)
    except Exception as e:
        print(f"Error al iniciar el servidor Flask: {e}")

async def main():
    """Función principal para arrancar el bot y el servidor web."""
    # Hilo daemon: si el bot de Discord se cae, el proceso termina y el
    # contenedor se reinicia en vez de quedarse vivo solo con el servidor web.
    threading.Thread(target=run_flask_app, daemon=True).start()

    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Error en la conexión con Discord: {type(e).__name__}: {e}")
        raise
    finally:
        if not bot.is_closed():
            await bot.close()
        print("Bot desconectado. Saliendo.")

if __name__ == "__main__":
    discord.utils.setup_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCerrando bot...")
    except Exception:
        sys.exit(1)
