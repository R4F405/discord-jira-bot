import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from web.webhook_server import create_webhook_app
import waitress

load_dotenv()

from web.webhook_server import create_webhook_app

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
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

async def run_flask_app():
    """Ejecuta Flask en el executor de asyncio para no bloquear el hilo principal."""
    try:
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
        await asyncio.gather(
            bot.start(DISCORD_TOKEN),
            run_flask_app()
        )
    except KeyboardInterrupt:
        print("\nCerrando bot...")
    finally:
        if not bot.is_closed():
            await bot.close()
        print("Bot desconectado. Saliendo.")

if __name__ == "__main__":
    asyncio.run(main())