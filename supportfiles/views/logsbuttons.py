from discord import ui, ButtonStyle, Interaction, Embed, File
from supportfiles.functions import MainFunctions
import os, json, asyncio
from datetime import datetime
from supportfiles.embedfactory import EmbedFactory

class AdditionalInfoButtons(ui.View):
    def __init__(self, config):
        super().__init__()
        self.steam_id = None
        self.server_id = None
        self.player_name = None
        self.bmid = None
        self.config = config
        self.embed_factory = EmbedFactory(config=config, bot=self)
        self.fun = MainFunctions(config=config)
        
    @ui.button(label="View Combatlog", style=ButtonStyle.green, row=1)
    async def view_combatlog(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Retrieving combatlog information now..", ephemeral=True)
        combatlog = await self.fun.combatlog(server_id=self.server_id, steam_id=self.steam_id)
        if combatlog:
            if combatlog.get('errors'):
                embed = await self.embed_factory.error_embed(message=combatlog['errors'][0]['detail'])
                await interaction.followup.send(embed=embed, ephemeral=True)
            elif combatlog:
                embed = await self.embed_factory.set_combatlog_embed(combatlog=combatlog['data']['attributes']['result'], player_name=self.player_name, steam_id=self.steam_id)
                
                with open(f"combatlog_{self.steam_id}.txt", "w") as f:
                    f.write(combatlog['data']['attributes']['result'])
                    f.close()
                await interaction.followup.send(content=f"combatlog scan of <https://steamcommunity.com/profiles/{self.steam_id}>", file=File(f"combatlog_{self.steam_id}.txt"), embed=embed, ephemeral=True)
                os.remove(f"combatlog_{self.steam_id}.txt")
        else:
            await interaction.followup.send("There is no combatlog to display", ephemeral=True)
            
    @ui.button(label="View Teaminfo", style=ButtonStyle.green, row=1)
    async def view_teaminfo(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Retrieving team information now..", ephemeral=True)
        teaminfo = await self.fun.team_info(server_id=self.server_id, steam_id=self.steam_id)
        if teaminfo:
            if teaminfo.get('errors'):
                embed = Embed(title=f"Team information", color=int("0x9b59b6", base=16))
                embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
                embed.add_field(name=f"Forbidden", value=f"```{teaminfo['errors'][0]['detail']}\nRAH doesn't have access to every server.. Yet! One day..```", inline=False)
                await interaction.followup.send(embed=embed, ephemeral=True)
            elif teaminfo:
                embed = await self.embed_factory.set_teaminfo_embed(teaminfo=teaminfo['data']['attributes']['result'], player_name=self.player_name)
                with open(f"teaminfo_{self.steam_id}.txt", "w", encoding='utf-8') as f:
                    f.write(teaminfo['data']['attributes']['result'])
                    f.close()
                await interaction.followup.send(content=f"Teaminfo of <https://steamcommunity.com/profiles/{self.steam_id}>", file=File(f"teaminfo_{self.steam_id}.txt"), embed=embed, ephemeral=True)
                os.remove(f"teaminfo_{self.steam_id}.txt")
        else:
            await interaction.followup.send("There is no combatlog to display", ephemeral=True)
            

class LogButtons(ui.View):
    def __init__(self, config):
        super().__init__()
        self.page_number = 0
        self.logs = None
        self.config = config
        self.embed_factory = EmbedFactory(config=config, bot=self)
        
    @ui.button(label="Previous Log", style=ButtonStyle.red)
    async def previous_note(self, interaction: Interaction, button: ui.Button):
        if self.page_number == 0:
            self.page_number = len(self.logs) - 1
        else:
            self.page_number -= 1
        embed = await self.embed_factory.create_log_embed(self.logs[self.page_number])
        await interaction.response.edit_message(content=f"Viewing log {self.page_number + 1} of {len(self.logs)}", embed=embed, view=self)
        
    @ui.button(label="Send as File", style=ButtonStyle.gray)
    async def send_as_file(self, interaction: Interaction, button: ui.Button):
        log = {
            'author_id': self.logs[self.page_number]['author_id'],
            'author_name': self.logs[self.page_number]['author_name'],
            'guild_name': self.logs[self.page_number]['guild_name'],
            'guild_id': self.logs[self.page_number]['guild_id'],
            'channel_id': self.logs[self.page_number]['channel_id'],
            'channel_name': self.logs[self.page_number]['channel_name'],
            'steam_id': self.logs[self.page_number]['steam_id'],
            'command': self.logs[self.page_number]['command'],
            'time': self.logs[self.page_number]['time']
        }
        with open(f"{interaction.user.id}_logs_file.json", "w") as f:
            f.write(json.dumps(log, indent=4))
        await interaction.response.send_message(file=File(f"{interaction.user.id}_logs_file.json"), ephemeral=True)
        await asyncio.sleep(1)
        os.remove(f"{interaction.user.id}_logs_file.json")

    @ui.button(label="Next Log", style=ButtonStyle.green)
    async def next_note(self, interaction: Interaction, button: ui.Button):
        if self.page_number >= (len(self.logs) - 1):
            self.page_number = 0
        else:
            self.page_number += 1
        embed = await self.embed_factory.create_log_embed(self.logs[self.page_number])
        await interaction.response.edit_message(content=f"Viewing log {self.page_number + 1} of {len(self.logs)}", embed=embed, view=self)