from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput
from supportfiles.functions import MainFunctions

import aiohttp

class Integration(Modal, title='RAH Integration'):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.fun = MainFunctions(config=config)

    identifier = TextInput(
        label='Your STEAM ID or BM profile URL',
        style=TextStyle.short,
        required=True,
    )

    async def on_submit(self, interaction: Interaction):
        await self.fun.signed_tos(user_id=interaction.user.id, signed_tos=True)
        integration_channel = self.config['logs']['integration']
        user_roles = []
        for role in interaction.user.roles:
            user_roles.append(role.name)
        await interaction.response.send_message("Thank you for submitting your discord ID or BM profile URL. We may contact you if we have any issues, however assume no issues and you can proceed to use the RAH bot. Enjoy! :D", ephemeral=True)
        the_report = {
            "username": "RAH Integration",
            "embeds": [
                {
                    "author": {
                        "name": f"{interaction.user.name} | {interaction.user.id}"
                    },
                    "title": "RAH Integration",
                    "description": f"**Guild ID:** {interaction.guild.id}\n**Guild name:** {interaction.guild.name}",
                    "color": 15258703,
                    "fields": [
                        {
                            "name": f"Roles",
                            "value": f"```{user_roles}```",
                            "inline": False
                        },
                        {
                            "name": "STEAM ID/BM Profile URL",
                            "value": f"```{self.identifier.value}```",
                            "inline": True
                        }
                    ]
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            await session.post(url=integration_channel, json=the_report)