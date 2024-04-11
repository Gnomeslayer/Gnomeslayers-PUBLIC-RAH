from discord import ui, ButtonStyle, Interaction
from supportfiles.embedfactory import EmbedFactory

class RelatedButtons(ui.View):
    def __init__(self, config):
        super().__init__()
        self.page_number = 0
        self.related_players = None
        self.original_player = None
        self.embed_factory = EmbedFactory(config=config, bot=self)
        
    @ui.button(label="Previous player", style=ButtonStyle.red)
    async def previous(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.edit_message(message_id=interaction.message.id, content="Retrieving player profile now. Give me a moment!", embed=None, view=None)
        if self.page_number == 0:
            self.page_number = len(self.related_players) - 1
            
        else:
            self.page_number -= 1
            
        button.label = f"View Related {self.page_number}/{len(self.related_players)}"
        self.next.label = f"View Related {self.page_number + 1}/{len(self.related_players)}"
        embed = await self.embed_factory.create_related_profile_embed(original_player=self.original_player, related_player=self.related_players[self.page_number], guild_id=interaction.guild.id)
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=self)
        
    @ui.button(label="Next player", style=ButtonStyle.green)
    async def next(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.edit_message(message_id=interaction.message.id, content="Retrieving player profile now. Give me a moment!", embed=None, view=None)
        if self.page_number >= (len(self.related_players) - 1):
            self.page_number = 0
        else:
            self.page_number += 1
        button.label = f"View Related {self.page_number}/{len(self.related_players)}"
        self.previous.label = f"View Related {self.page_number - 1}/{len(self.related_players)}"
        embed = await self.embed_factory.create_related_profile_embed(original_player=self.original_player, related_player=self.related_players[self.page_number], guild_id=interaction.guild.id)
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=self)