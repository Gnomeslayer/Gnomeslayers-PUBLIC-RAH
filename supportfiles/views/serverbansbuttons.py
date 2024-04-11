from discord import ui, Interaction, ButtonStyle, File
from supportfiles.embedfactory import EmbedFactory
import supportfiles.model as model
import os, json

class ServerBansButtons(ui.View):
    def __init__(self, config):
        super().__init__()
        self.serverbans = None
        self.page_number = 0
        self.embed_factory = EmbedFactory(config=config, bot=self)

    @ui.button(label="Previous Ban", style=ButtonStyle.red)
    async def previous_ban(self, interaction: Interaction, button: ui.Button):
        if self.page_number == 0:
            self.page_number = len(self.serverbans) - 1
        else:
            self.page_number -= 1
        
        button.label = f"View Ban {self.page_number}/{len(self.serverbans)}"
        self.next_ban.label = f"View Ban {self.page_number + 1}/{len(self.serverbans)}"
                
        embed = await self.embed_factory.create_ban_embed(self.serverbans[self.page_number])
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Send as file", style=ButtonStyle.blurple)
    async def send_file(self, interaction: Interaction, button: ui.Button):
        theban:model.Serverbans = self.serverbans[self.page_number]
        theban = {
            "bmid": theban.bmid,
            "steamid": theban.steamid,
            "bandate": theban.bandate,
            "expires": theban.expires,
            "banid": theban.banid,
            "serverid": theban.serverid,
            "servername": theban.servername,
            "banner": theban.banner,
            "banreason": theban.banreason,
            "uuid": theban.uuid,
            "bannote": theban.bannote
        }

        with open(f"{interaction.user.id}_serverbans_file.json", "w") as f:
            f.write(json.dumps(theban, indent=4))
        await interaction.response.send_message(file=File(f"{interaction.user.id}_serverbans_file.json"), ephemeral=True)
        os.remove(f"{interaction.user.id}_serverbans_file.json")

    @ui.button(label="Next Ban", style=ButtonStyle.green)
    async def next_ban(self, interaction: Interaction, button: ui.Button):
        if self.page_number >= (len(self.serverbans) - 1):
            self.page_number = 0
        else:
            self.page_number += 1
        
        button.label = f"View Ban {self.page_number}/{len(self.serverbans)}"
        self.previous_ban.label = f"View Ban {self.page_number - 1}/{len(self.serverbans)}"

        embed = await self.embed_factory.create_ban_embed(self.serverbans[self.page_number])
        await interaction.response.edit_message(embed=embed, view=self)