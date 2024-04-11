import datetime as dt
from supportfiles.functions import MainFunctions
from datetime import datetime
from discord import Interaction, Embed
from discord.app_commands import guild_only, command

from discord.ext import commands

class Cheetos(commands.Cog):
    def __init__(self, bot:commands.Bot, config:dict):
        print("[Cog] Cheetos has been initiated")
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.fun = MainFunctions(config=config)
        
    @command(name="cheetos", description="Cheetos")
    @guild_only()
    async def cheetos(self, interaction: Interaction, discordid:str) -> None:
        await interaction.response.defer(ephemeral=True)
        profiles = await self.fun.get_profiles(user_id=interaction.user.id, guildid=interaction.guild.id)
        if not profiles['user_profile'].approved:
            await interaction.followup.send("You are not authorized to use this command. Contact the staff at the official [RAH DISCORD](https://gg/PrczhwME72) to learn more.")
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.followup.send("This guild isnt authorized.")
            return
        if profiles['blacklisted']:
            await interaction.followup.send("Blacklisted.")
            return
        cheet_cords = await self.fun.check_cheetos(discord_id=discordid)
        embed = Embed(title="Cheetos checker", description=f"Results for scanned discord id: {discordid}")
        if cheet_cords:
            cheetos_txt = None
            for cheet in cheet_cords:
                lastscan = str(
                    dt.datetime.fromtimestamp(cheet['LastGuildScan']))
                lastscan = lastscan[:10]
                added = str(dt.datetime.fromtimestamp(cheet['TimestampAdded']))
                added = added[:10]
                if not cheetos_txt:
                    cheetos_txt = f"➢**{cheet['Name']}** - Added: <t:{cheet['TimestampAdded']}:R> Last Scan: <t:{cheet['LastGuildScan']}:R>\nRoles: {cheet['Roles']}"
                else:
                    cheetos_txt += f"\n➢**{cheet['Name']}** - Added: <t:{cheet['TimestampAdded']}:R> Last Scan: <t:{cheet['LastGuildScan']}:R>\nRoles: {cheet['Roles']}"
                if len(cheetos_txt) > 500:
                    embed.add_field(
                        name="Cheetos",
                        value=f"Seen in {len(cheet_cords)} cheatcords\n{cheetos_txt}",
                        inline=False
                    )
                    cheetos_txt = None
            if cheetos_txt:
                embed.add_field(
                    name="Cheetos",
                    value=f"**Seen in {len(cheet_cords)} cheatcords**\n{cheetos_txt}",
                    inline=False
                )
        else:
            embed.add_field(
                name="Cheetos", value="```Seen in 0 cheatcords.```", inline=False)
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        await interaction.followup.send(embed=embed, ephemeral=True)

