from discord import ButtonStyle, Interaction
from discord.ui import Button, button, View
from supportfiles.embedfactory import EmbedFactory
from supportfiles.functions import MainFunctions
import supportfiles.modals.monitor_modals as mm
from supportfiles.model import MonitorSettings

class MonitorButtons(View):
    def __init__(self, config:dict, phrase:str, guild_id:str, match_strength_percent:int):
        super().__init__(timeout=None)
        self.config = config
        self.fun = MainFunctions(config=config)
        self.embed_factory = EmbedFactory(config=config, bot=self)
        self.settings:MonitorSettings = MonitorSettings(phrase=phrase, guild_id=guild_id, match_strength_percent=match_strength_percent)
        
    
    async def change_button(self, button:Button) -> None:
        button.style = ButtonStyle.danger if button.style == ButtonStyle.success else ButtonStyle.success
    
    async def message_embed(self):
        embed = await self.embed_factory.create_settings_embed(self.settings)
        return embed
    
    @button(label="Ban", style=ButtonStyle.danger, row=0)
    async def ban_button(self, interaction: Interaction, button: Button):
        await self.change_button(button)
        self.settings.ban = not self.settings.ban
        embed = await self.message_embed()
        await interaction.response.edit_message(embed=embed, view = self)
            
    @button(label="Timeout User", style=ButtonStyle.red, row=0)
    async def timeout_user_button(self, interaction: Interaction, button: Button):
        await self.change_button(button)
        
        original_interaction:Interaction = interaction
        self.settings.timeout_user = not self.settings.timeout_user
        timeoutmodal = mm.TimeoutTime(original_interaction = original_interaction, view = self, settings=self.settings)
        
        await interaction.response.send_modal(timeoutmodal)
    
    @button(label="delete", style=ButtonStyle.red, row=0)
    async def delete_button(self, interaction: Interaction, button: Button):
        await self.change_button(button)
        self.settings.delete = not self.settings.delete
        embed = await self.message_embed()
        await interaction.response.edit_message(embed=embed, view = self)
    
    @button(label="warn", style=ButtonStyle.red, row=1)
    async def warn_button(self, interaction: Interaction, button: Button):
        await self.change_button(button)
        
        original_interaction:Interaction = interaction
        self.settings.warn = not self.settings.warn
        WarnModal = mm.WarnMessage(original_interaction = original_interaction, view = self, settings=self.settings)
        
        await interaction.response.send_modal(WarnModal)
    
    @button(label="Alert Staff", style=ButtonStyle.red, row=1)
    async def alert_staff_button(self, interaction: Interaction, button: Button):
        await self.change_button(button)
        self.settings.alert_staff = not self.settings.alert_staff
        embed = await self.message_embed()
        await interaction.response.edit_message(embed=embed, view = self)
    
    @button(label="Respond", style=ButtonStyle.red, row=1)
    async def respond_button(self, interaction: Interaction, button: Button):
        await self.change_button(button)
        
        original_interaction:Interaction = interaction
        self.settings.respond = not self.settings.respond
        ResponseModal = mm.ResponseMessage(original_interaction = original_interaction, view = self, settings=self.settings)
        
        await interaction.response.send_modal(ResponseModal)
        
    @button(label="Save", style=ButtonStyle.blurple, row=2)
    async def save_button(self, interaction: Interaction, button: Button):
        await self.fun.add_monitor_setting(self.settings)
        await interaction.response.edit_message(view=None, embed=None, content=f"I will now monitor in this guild for the phrase: `{self.settings.phrase}`")
        
    @button(label="Cancel", style=ButtonStyle.blurple, row=2)
    async def cancel_button(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(view=None, embed=None, content=f"# Cancelled")