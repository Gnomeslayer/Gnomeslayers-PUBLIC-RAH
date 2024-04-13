import discord
import json
from discord.ext import commands

# Import cogs
from cogs.cheetos import Cheetos
from cogs.public_commands import PublicCommands
from cogs.private_commands import PrivateCommands
from cogs.rah import Rah
from cogs.rahlink import RahLink
from cogs.vdfchecker import VDFchecker
from cogs.chatmoderator import ChatModerator
from cogs.arkans import Arkans

with open("./configs/config.json", "r") as config_file:
    config = json.load(config_file)

class MyBot(commands.Bot):
    def __init__(self, config:dict):
        super().__init__(
            command_prefix=config['additional']['prefix'],
            intents=discord.Intents.all()
        )
        self.config = config
        self._cogs_to_load = {}
        if self.config['additional']['test_mode']:
            self._cogs_to_load['Cheetos'] = Cheetos
            self._cogs_to_load['PublicCommands'] = PublicCommands
            self._cogs_to_load['PrivateCommands'] = PrivateCommands
            self._cogs_to_load['Rah'] = Rah
            self._cogs_to_load['RahLink'] = RahLink
            self._cogs_to_load['VDFCHECKER'] = VDFchecker
            #self._cogs_to_load['ChatModerator'] = ChatModerator
            self._cogs_to_load['Arkans'] = Arkans
            #self._cogs_to_load['Websockets'] = WebsocketManager
            
        else:
            self._cogs_to_load['Cheetos'] = Cheetos
            self._cogs_to_load['PublicCommands'] = PublicCommands
            self._cogs_to_load['PrivateCommands'] = PrivateCommands
            self._cogs_to_load['Rah'] = Rah
            self._cogs_to_load['RahLink'] = RahLink
            self._cogs_to_load['VDFCHECKER'] = VDFchecker
            self._cogs_to_load['Arkans'] = Arkans


    async def on_ready(self):
        for name, cog_class in self._cogs_to_load.items():
               cog_instance = cog_class(bot=self, config=self.config)
               await self.add_cog(cog_instance)
        await self.tree.sync()
        print("Bot fully loaded and ready to go! Last update: 4/02/2024")

# Ensure the script is being run directly, not imported as a module
if __name__ == "__main__":
    
    if config['additional']['test_mode']:
        print("\n\n=========== BOT LOADED WITH TEST TOKENS ===========\n\n")
        bot = MyBot(config)
        bot.run(config['tokens']['test_discord_token'])
    else:
        print("\n\n=========== BOT LOADED WITH LIVE TOKENS ===========\n\n")
        bot = MyBot(config)
        bot.run(config['tokens']['discord_token'])
