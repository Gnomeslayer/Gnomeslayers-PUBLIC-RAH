from discord import ui, ButtonStyle, Interaction
from supportfiles.embedfactory import EmbedFactory

class ArkanButtons(ui.View):
    def __init__(self, config):
        super().__init__()
        self.page_number = 0
        self.arkans = None
        self.embed_factory = EmbedFactory(config=config, bot=self)
        
    @ui.button(label="Previous Arkan", style=ButtonStyle.red)
    async def previous(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.edit_message(message_id=interaction.message.id, content="Retrieving Arkan info. Give me a moment!", embed=None, view=None)
        if self.page_number == 0:
            self.page_number = len(self.arkans) - 1
            
        else:
            self.page_number -= 1
            
        embed = await self.embed_factory.arkan_embed(self.arkans[self.page_number])
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=self)
        
    @ui.button(label="Next Arkan", style=ButtonStyle.green)
    async def next(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.edit_message(message_id=interaction.message.id, content="Retrieving Arkan info. Give me a moment!", embed=None, view=None)
        if self.page_number >= (len(self.arkans) - 1):
            self.page_number = 0
        else:
            self.page_number += 1
            
        embed = await self.embed_factory.arkan_embed(self.arkans[self.page_number])
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=self)