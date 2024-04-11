from discord.ui import View, Button, button
from discord import ButtonStyle, Interaction
from supportfiles.modals.integration_modal import Integration

from supportfiles.functions import MainFunctions

class TOS_Buttons(View):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.fun = MainFunctions(config=config)

    @button(label="Accept", style=ButtonStyle.green)
    async def Accept(self, interaction: Interaction, button: Button):
        integrationmodal = Integration(config=self.config)
        integrationmodal.config = self.config
        await interaction.response.send_modal(integrationmodal)
        #await interaction.response.send_message("Thank you for accepting the TOS please contact the server owner to approve you", ephemeral=True)
        content = f"""**Accepted TOS **
        **Author: ** {interaction.user.name}({interaction.user.id})
        ** Author Roles: ** ```{interaction.user.roles}```** Context: ** Pressed Accept
        ** Discord Server: ** {interaction.guild.name}({interaction.guild.id})
        ** Discord Channel: ** {interaction.channel.name}({interaction.channel.id})"""
        await self.fun.send_approve(content=content)

    @button(label="Reject", style=ButtonStyle.red)
    async def Reject(self, interaction: Interaction, button: Button):
        await self.fun.signed_tos(user_id=interaction.user.id, signed_tos=False)
        await interaction.response.send_message("You're still registered however until you sign the TOS you will not be able to use this bot.", ephemeral=True)
        content = f"""**Rejected TOS **
        **Author: ** {interaction.user.name}({interaction.user.id})
        ** Author Roles: ** ```{interaction.user.roles}```** Context: ** Pressed Reject
        ** Discord Server: ** {interaction.guild.name}({interaction.guild.id})
        ** Discord Channel: ** {interaction.channel.name}({interaction.channel.id})"""
        await self.fun.send_approve(content=content)