from discord.ext import commands
from supportfiles.functions import MainFunctions
from datetime import datetime

from discord import Interaction, Embed
from discord.app_commands import command, guild_only

class RahLink(commands.Cog):
    def __init__(self, bot, config):
        print("[Cog] rahlink has been initiated")
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.fun = MainFunctions(config=config)

    @command(name="linkids", description="Links a steam id to a discord id")
    @guild_only()
    async def linkids(self, interaction: Interaction, steam_id: str, discord_id: str):
        await interaction.response.defer(ephemeral=True)
        
        profiles = await self.fun.get_profiles(user_id=interaction.user.id, guildid=interaction.guild.id)
        if not profiles['user_profile'].approved:
            await interaction.followup.send("You are not authorized to use this command. Contact the staff at the official [RAH DISCORD](https://discord.gg/PrczhwME72) to learn more.")
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.followup.send("This guild isnt authorized.")
            return
        if profiles['blacklisted']:
            await interaction.followup.send("Blacklisted.")
            return
        
        await self.fun.store_logs(author_id=interaction.user.id,
                             author_name=interaction.user.name,
                             guild_name=interaction.guild.name,
                             guild_id=interaction.guild.id,
                             channel_id=interaction.channel.id,
                             channel_name=interaction.channel.name,
                             steam_id=steam_id,
                             command="linkids")
        if profiles['server_profile'].show_logs:
            guild = self.bot.get_guild(int(profiles['server_profile'].server_id))
            log_channel = guild.get_channel(int(profiles['server_profile'].log_channel))
            embed = Embed(title=f"LOGS!!",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x9b59b6", base=16))
            embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
            embed.add_field(name="Author Name and ID", value=f"```{interaction.user.name} - {interaction.user.id}```", inline=False)
            embed.add_field(name="Guild Name and ID", value=f"```{interaction.guild.name} - {interaction.guild.id}```", inline=False)
            embed.add_field(name="Channel Name and ID the command was used in", value=f"```{interaction.channel.name} - {interaction.channel.id}```", inline=False)
            embed.add_field(name="Command Used", value=f"```/linkids {steam_id} {discord_id}```")
            embed.add_field(name="Log Commands", value="Use the command `/get_all_logs` to retrieve all logs as a file.\nUse `/get_logs` to cycle through logs.", inline=False)
            try:
                await log_channel.send(embed=embed)
            except:
                pass
        
        player_ids = await self.fun.get_player_ids(steam_id)
        bmid = None
        confidence = 20
        if player_ids:
            bmid = player_ids.bmid
            if player_ids.discordid:
                for discordid in player_ids.discordid:
                    if discordid['discordid'] == discord_id:
                        if discordid['discordid'] == 100:
                            await interaction.followup.send(f"They are already linked with a confidence of 100%!", ephemeral=True)
                            return
                        confidence = discordid['confidence'] + 20

        if confidence >= 100:
            confidence = 100
        
        #check if the user has already submitted these two ids!
        rah_link_user = await self.fun.get_rah_link_by_user(user_id=interaction.user.id, discord_id=discord_id, steam_id=steam_id)
        rah_link_server = await self.fun.get_rah_link_by_server(server_id=interaction.guild.id, discord_id=discord_id, steam_id=steam_id)
        
        if rah_link_user:
            await interaction.followup.send("You've already submitted this pairing.", ephemeral=True)
            return
        elif rah_link_server:
            await interaction.followup.send("Another person from this server has already sent this pairing in. Thank you for still doing it. It means a lot <3", ephemeral=True)
            return
        
        await self.fun.add_ids(discord_id=discord_id, bmid=bmid, steam_id=steam_id, confidence=confidence, user_id=interaction.user.id, server_id=interaction.guild.id)
        if player_ids:
            await interaction.followup.send(f"Successfully submitted those two IDs! Confidence level for these IDs is at {confidence}%", ephemeral=True)
        else:
            await interaction.followup.send(f"Successfully submitted those two IDs! Confidence level for these IDs is at 20%", ephemeral=True)
