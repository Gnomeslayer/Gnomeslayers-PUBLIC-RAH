from discord.ext import commands
from difflib import SequenceMatcher

from discord import Interaction, Message, Role
from discord.app_commands import command, guild_only
from discord.app_commands.checks import has_permissions
from discord.app_commands.errors import MissingPermissions

from supportfiles.embedfactory import EmbedFactory
from supportfiles.views.monitorbuttons import MonitorButtons
import supportfiles.model as model
from supportfiles.functions import MainFunctions
from datetime import timedelta


class ChatModerator(commands.Cog):
    def __init__(self, bot:commands.Bot, config:dict):
        print("[Cog] ChatModerator has been initiated")
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.fun = MainFunctions(config=config)
        self.embed_factory = EmbedFactory(config=config, bot=bot)
        self.ignored_roles = {}
        self.monitor_info = {}
    
    async def load_settings(self, guild_id):
        self.ignored_roles[guild_id] = await self.fun.get_monitor_ignore_role(guild_id=guild_id)
        self.monitor_info[guild_id] = await self.fun.get_monitor_info(guild_id=guild_id)
          
    @command(name="monitor", description="Adds a new phrase to monitor in your guild")
    @guild_only()
    @has_permissions(administrator=True)
    async def monitor(self, interaction: Interaction, phrase:str, match_strength_percent:int=100) -> None:
        await interaction.response.defer(ephemeral=True)
        actions = MonitorButtons(config=self.config, phrase=phrase, guild_id=interaction.guild.id, match_strength_percent=match_strength_percent)
        settings = model.MonitorSettings(phrase=phrase, guild_id=interaction.guild.id, match_strength_percent=match_strength_percent)
        embed = await self.embed_factory.create_settings_embed(settings)
        await interaction.followup.send(embed=embed, view=actions)
        
        
    @command(name="monitor_ignore_role", description="Monitor will ignore this role")
    @guild_only()
    @has_permissions(administrator=True)
    async def ignore_role(self, interaction: Interaction, role:Role) -> None:
        await interaction.response.defer(ephemeral=True)
        await self.fun.add_monitor_ignore_role(guild_id=interaction.guild.id, role_id=role.id)
        await interaction.followup.send(content="RAH Monitor will now ignore that role on this server!", ephemeral=True)
        
    
    @monitor.error
    async def monitor_handler(self, ctx:Interaction, error):
        if isinstance(error, MissingPermissions):
            await ctx.response.send_message(error, ephemeral=True)
            
    @monitor.error
    async def ignore_role_handler(self, ctx:Interaction, error):
        if isinstance(error, MissingPermissions):
            await ctx.response.send_message(error, ephemeral=True)
    
    @guild_only()
    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return
        await self.load_settings(message.guild.id)
        if self.monitor_info[message.guild.id]:
            for info in self.monitor_info[message.guild.id]:
                info:model.Monitor = info
                ratio = SequenceMatcher(None, info.phrase.lower(), message.content.lower()).ratio() * 100
                if ratio >= info.match_strength_percent:
                    if any(role.id in self.ignored_roles[message.guild.id] for role in message.author.roles):
                        return
                    await self.process_monitor_actions(message, info)
                    
    async def process_monitor_actions(self, message, info):
        if info.delete:
            await message.delete()
        if info.warn:
            try:
                await message.author.send(f"# WARNING\n```{info.warn_message}```")
            except:
                await message.channel.send(f"# WARNING FOR {message.author.mention}\n```{info.warn_message}```")
        if info.timeout_user:
            try:
                duration = timedelta(minutes=int(info.timeout_time))
                await message.author.timeout(duration, reason="Auto Moderatored")
            except:
                print("Unable to time out user...?")
        if info.ban:
            try:
                await message.author.ban(delete_message_days=7, delete_message_seconds=604800, reason="Auto Moderatored")
            except:
                print("Unable to ban user?")
        if info.respond:
            await message.channel.send(f"{message.author.mention}```{info.response_message}``` _This is an automatic response_")
        
        if info.alert_staff:
            await message.channel.send(f"AAHHH")
        return