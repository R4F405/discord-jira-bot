import os
import httpx
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    print("Error: Variables de entorno de Jira no configuradas. Los comandos fallarán.")

jira_client = httpx.AsyncClient(
    auth=JIRA_AUTH,
    headers={"Content-Type": "application/json"}
)

class JiraCommands(commands.Cog):
    """Cog que agrupa todos los comandos de aplicación relacionados con Jira."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog 'JiraCommands' inicializado.")

    jira = app_commands.Group(
        name="jira",
        description="Comandos para interactuar con Jira"
    )

    @jira.command(name="info", description="Muestra información sobre los comandos disponibles.")
    async def jira_info(self, interaction: discord.Interaction):
        """Muestra un mensaje de ayuda con todos los comandos."""
        embed = discord.Embed(
            title="🤖 Ayuda del Bot de Jira",
            description="Aquí están los comandos que puedes usar:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="`/jira ver <ticket_id>`",
            value="Obtiene información detallada de un ticket de Jira (ej. `ABC-123`).",
            inline=False
        )
        embed.add_field(
            name="`/jira pendientes <usuario>`",
            value="Lista tickets en 'BACKLOG' o 'SELECCIONADO PARA DESARROLLO'.",
            inline=False
        )
        embed.add_field(
            name="`/jira encurso <usuario>`",
            value="Lista los tickets que están 'EN CURSO'.",
            inline=False
        )
        embed.add_field(
            name="`/jira bloqueados <usuario>`",
            value="Lista los tickets en estado 'BLOCK'.",
            inline=False
        )
        embed.add_field(
            name="`/jira finalizados <usuario>`",
            value="Lista tickets en 'CODE REVIEW', 'QA' o 'LISTO'.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @jira.command(name="ver", description="Obtiene información detallada de un ticket de Jira.")
    @app_commands.describe(ticket_id="El ID del ticket (ej. ABC-123)")
    async def jira_ver(self, interaction: discord.Interaction, ticket_id: str):
        """Obtiene y muestra los detalles de un ticket de Jira específico."""
        await interaction.response.defer()

        try:
            response = await jira_client.get(
                f"{JIRA_BASE_URL}/rest/api/3/issue/{ticket_id.upper()}"
            )

            if response.status_code == 200:
                issue = response.json()
                embed = self._create_ticket_embed(issue, ticket_id)
                await interaction.followup.send(embed=embed)
            
            elif response.status_code == 404:
                await interaction.followup.send(f"❌ No se pudo encontrar el ticket **{ticket_id.upper()}**.")
            
            else:
                await interaction.followup.send(f"Error del servidor de Jira: {response.status_code}")

        except httpx.RequestError as e:
            print(f"Error de HTTPX al consultar el ticket {ticket_id}: {e}")
            await interaction.followup.send("Ocurrió un error de red al consultar el ticket de Jira.")
        except Exception as e:
            print(f"Excepción en 'jira_ver' ({ticket_id}): {e}")
            await interaction.followup.send("Ocurrió un error inesperado al procesar la solicitud.")

    @jira.command(name="pendientes", description="Lista tickets en BACKLOG o SELECCIONADO PARA DESARROLLO.")
    @app_commands.describe(usuario="El 'username' o 'displayName' del usuario en Jira")
    async def jira_pendientes(self, interaction: discord.Interaction, usuario: str):
        """Lista tickets pendientes del usuario especificado."""
        await interaction.response.defer()
        
        jql_query = f'assignee = "{usuario}" AND status IN ("BACKLOG", "SELECTED FOR DEVELOPMENT") ORDER BY updated DESC'
        
        await self._perform_jql_search(
            interaction,
            jql_query,
            f"Tickets Pendientes de {usuario}",
            f"No se encontraron tickets pendientes para '{usuario}'."
        )

    @jira.command(name="encurso", description="Lista tickets en estado 'EN CURSO'.")
    @app_commands.describe(usuario="El 'username' o 'displayName' del usuario en Jira")
    async def jira_encurso(self, interaction: discord.Interaction, usuario: str):
        """Lista tickets en curso del usuario especificado."""
        await interaction.response.defer()
        
        jql_query = f'assignee = "{usuario}" AND status = "En curso" ORDER BY updated DESC'
        
        await self._perform_jql_search(
            interaction,
            jql_query,
            f"Tickets EN CURSO de {usuario}",
            f"No se encontraron tickets EN CURSO para '{usuario}'."
        )
            
    @jira.command(name="bloqueados", description="Lista tickets en estado 'BLOCK'.")
    @app_commands.describe(usuario="El 'username' o 'displayName' del usuario en Jira")
    async def jira_bloqueados(self, interaction: discord.Interaction, usuario: str):
        """Lista tickets bloqueados del usuario especificado."""
        await interaction.response.defer()
        
        jql_query = f'assignee = "{usuario}" AND status = "BLOCK" ORDER BY updated DESC'
        
        await self._perform_jql_search(
            interaction,
            jql_query,
            f"Tickets Bloqueados de {usuario}",
            f"No se encontraron tickets bloqueados para '{usuario}'."
        )

    @jira.command(name="finalizados", description="Lista tickets en CODE REVIEW, QA o LISTO.")
    @app_commands.describe(usuario="El 'username' o 'displayName' del usuario en Jira")
    async def jira_finalizados(self, interaction: discord.Interaction, usuario: str):
        """Lista tickets finalizados del usuario especificado."""
        await interaction.response.defer()
        
        jql_query = f'assignee = "{usuario}" AND status IN ("CODE REVIEW", "QA", "Listo") ORDER BY updated DESC'
        
        await self._perform_jql_search(
            interaction,
            jql_query,
            f"Tickets Finalizados de {usuario}",
            f"No se encontraron tickets finalizados para '{usuario}'."
        )

    async def _perform_jql_search(self, interaction: discord.Interaction, jql_query: str, title: str, no_results_message: str):
        """
        Ejecuta una búsqueda JQL y envía un Embed con los resultados.
        """
        try:
            request_url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
            request_payload = {
                "jql": jql_query,
                "maxResults": 30,
                "fields": ["summary", "status"]
            }

            response = await jira_client.post(request_url, json=request_payload)

            if response.status_code == 200:
                data = response.json()
                issues = data.get("issues", [])

                if not issues:
                    await interaction.followup.send(f"ℹ️ {no_results_message}")
                    return

                embed = self._create_issue_list_embed(issues, title)
                await interaction.followup.send(embed=embed)
            
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("errorMessages", ["Error desconocido"])[0]
                await interaction.followup.send(f"Error en la consulta JQL: {error_message}")
            
            else:
                print(f"[LOG] Error en búsqueda JQL (no 200/400): {response.text}")
                await interaction.followup.send(f"No se pudo realizar la búsqueda. Código de estado: {response.status_code}")

        except httpx.RequestError as e:
            print(f"Error de HTTPX en '_perform_jql_search': {e}")
            await interaction.followup.send("Ocurrió un error de red al consultar a Jira.")
        except Exception as e:
            print(f"Excepción en '_perform_jql_search': {e}")
            await interaction.followup.send("Ocurrió un error inesperado al procesar la búsqueda.")

    def _create_issue_list_embed(self, issues: list, title: str) -> discord.Embed:
        """Formatea una lista de issues en un Embed."""
        embed = discord.Embed(
            title=f"🔎 {title}",
            color=discord.Color.green()
        )
        
        description = []
        for issue in issues:
            key = issue.get("key", "SIN-CLAVE")
            fields = issue.get("fields", {})
            summary = fields.get("summary", "Sin resumen")
            status_obj = fields.get("status")
            status = status_obj.get("name", "Sin estado") if status_obj else "Sin estado"
            
            ticket_url = f"{JIRA_BASE_URL}/browse/{key}"
            
            description.append(
                f"**[{key}]({ticket_url})**: {summary}\n"
                f"*(Estado: {status})*"
            )
        
        embed.description = "\n\n".join(description)
        
        if len(issues) == 30:
            embed.set_footer(text="Se muestran los 30 tickets más recientes. Puede haber más resultados.")
            
        return embed

    def _create_ticket_embed(self, issue: dict, ticket_key: str) -> discord.Embed:
        """Formatea el JSON de un issue en un Embed detallado."""
        fields = issue.get("fields", {})
        
        summary = fields.get("summary", "Sin resumen")
        status = fields.get("status", {}).get("name", "Sin estado")
        creator_name = fields.get("creator", {}).get("displayName", "Sin creador")
        assignee_name = fields.get("assignee", {}).get("displayName", "Sin asignar")
        created_date_str = fields.get("created", "Sin fecha de creación")
        
        created_date = created_date_str
        if created_date_str != "Sin fecha de creación":
            try:
                created_date = datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%d/%m/%Y - %H:%M:%S")
            except ValueError:
                pass

        description = "Sin descripción"
        desc_obj = fields.get("description")
        
        if isinstance(desc_obj, dict) and "content" in desc_obj:
            try:
                description_text = ""
                for block in desc_obj["content"]:
                    if block["type"] == "paragraph":
                        for text_block in block.get("content", []):
                            if text_block.get("type") == "text":
                                description_text += text_block.get("text", "") + "\n"
                description = description_text.strip() or "Sin descripción"
            except Exception:
                description = "Error al parsear la descripción estructurada."
        elif isinstance(desc_obj, str):
            description = desc_obj

        if len(description) > 1024:
            description = description[:1021] + "..."

        ticket_url = f"{JIRA_BASE_URL}/browse/{ticket_key.upper()}"
        
        embed = discord.Embed(
            title=f"Ticket: [{ticket_key.upper()}] {summary}",
            url=ticket_url,
            color=discord.Color.blurple()
        )
        
        embed.add_field(name="Estado", value=status, inline=True)
        embed.add_field(name="Asignado a", value=assignee_name, inline=True)
        embed.add_field(name="Creado por", value=creator_name, inline=True)
        embed.add_field(name="Fecha de Creación", value=created_date, inline=True)
        
        embed.add_field(name="Descripción", value=description, inline=False)
        
        return embed

async def setup(bot: commands.Bot):
    """Setup requerido por discord.py para cargar el Cog."""
    await bot.add_cog(JiraCommands(bot))