from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput

from supportfiles.embedfactory import EmbedFactory
from supportfiles.model import MonitorSettings


class TimeoutTime(Modal, title='Timeout Duration'):
    def __init__(self, config, original_interaction, view, settings:MonitorSettings):
        super().__init__()
        self.config = config
        self.embed_factory = EmbedFactory(config=config, bot=self)
        self.original_interaction:Interaction = original_interaction
        self.view = view
        self.settings = settings

    timeout_time = TextInput(
        label='Timeout Time (minutes)',
        style=TextStyle.short,
        placeholder="100",
        required=True,
    )
    
    async def on_submit(self, interaction: Interaction):
        self.settings.timeout_time = self.timeout_time.value
        embed = await self.embed_factory.create_settings_embed(self.settings)
        await self.original_interaction.edit_original_response(embed=embed, view=self.view)
        await interaction.response.send_message(f"Set timeout time to be: {self.timeout_time.value}", ephemeral=True)
        
        
class WarnMessage(Modal, title='Warn Message'):
    def __init__(self, config, original_interaction, view, settings:MonitorSettings):
        super().__init__()
        self.config = config
        self.embed_factory = EmbedFactory(config=config, bot=self)
        self.original_interaction:Interaction = original_interaction
        self.view = view
        self.settings = settings

    warn_message = TextInput(
        label='Warn Message (leave blank for default)',
        style=TextStyle.short,
        placeholder="We don't do that here..",
        required=False,
    )
    
    async def on_submit(self, interaction: Interaction):
        if  self.warn_message.value:
            self.settings.warn_message = self.warn_message.value
            embed = await self.embed_factory.create_settings_embed(self.settings)
            await self.original_interaction.edit_original_response(embed=embed, view=self.view)
            await interaction.response.send_message(f"Set warn message to be: {self.warn_message.value}", ephemeral=True)
        else:
            embed = await self.embed_factory.create_settings_embed(self.settings)
            await self.original_interaction.edit_original_response(embed=embed, view=self.view)
            await interaction.response.send_message(f"Set warn message to be: None", ephemeral=True)
        
class ResponseMessage(Modal, title='Response Message'):
    def __init__(self, config, original_interaction, view, settings:MonitorSettings):
        super().__init__()
        self.config = config
        self.embed_factory = EmbedFactory(config=config, bot=self)
        
        self.original_interaction:Interaction = original_interaction
        self.view = view
        self.settings = settings

    response_message = TextInput(
        label='Response',
        style=TextStyle.short,
        placeholder="Apples do grow in the ground!",
        required=True,
    )
    
    async def on_submit(self, interaction: Interaction):
        self.settings.response_message = self.response_message.value
        embed = await self.embed_factory.create_settings_embed(self.settings)
        await self.original_interaction.edit_original_response(embed=embed, view=self.view)
        await interaction.response.send_message(f"Set warn message to be: {self.response_message.value}", ephemeral=True)