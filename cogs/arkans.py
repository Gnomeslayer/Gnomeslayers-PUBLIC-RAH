from discord import Interaction
from discord.app_commands import guild_only, command
from discord.ext import commands, tasks
from supportfiles.embedfactory import EmbedFactory


from supportfiles.functions import MainFunctions
from battlemetrics import Battlemetrics
from supportfiles.reporter import Reporter
import supportfiles.model as model
from supportfiles.views.arkanbuttons import ArkanButtons

import json

class Arkans(commands.Cog):
    def __init__(self, bot:commands.Bot, config:dict):
        print("[Cog] Arkans has been initiated")
        self.bot = bot
        self.config= config
        self.rahresetter.start()
        self.fun = MainFunctions(config=config)
        self.embed_factory = EmbedFactory(config=config, bot=bot)
        self.bmapi = Battlemetrics(api_key=config['tokens']['battlemetrics_token'])
        self.arkan_buttons = ArkanButtons(config=config)

    users = []

    @tasks.loop(seconds=15)
    async def rahresetter(self):
        self.users = []
        
    async def check_permissions(self, user_id:int, guild_id:int, channel_id = None) -> dict:
        profiles = await self.fun.get_profiles(user_id=user_id, guildid=guild_id)
        profiles['cooldown'] = False
        if channel_id:
            if not int(profiles['server_profile'].rah_listen_channel) == int(channel_id):
                return False
        if not profiles['user_profile'].approved:
            return False
        if not profiles['server_profile'].whitelisted:
            return False
        if profiles['blacklisted']:
            return False
        
        if user_id in self.users:
            profiles['cooldown'] = True
        else:
            self.users.append(user_id)
        return profiles
    
    @command(name="getarkans", description="Checks a users profile for arkans")
    @guild_only()
    async def getarkans(self, interaction: Interaction, profile_or_identifier:str, send_teaminfo:bool = False):
       
        await interaction.response.defer(ephemeral=True)
        
        permissions = await self.check_permissions(user_id=interaction.user.id,
                                                   guild_id=interaction.guild.id)
        if not permissions:
            return
        
        if permissions['cooldown']:
            await interaction.followup.send("This command is on cooldown. Please wait around 15 seconds before trying again!", ephemeral=True)
            return
        
        log = {
               "author_id": interaction.user.id,
               "author_name": interaction.user.name,
               "guild_name": interaction.guild.name,
               "guild_id":interaction.guild.name,
               "channel_id": interaction.channel.id,
               "channel_name": interaction.channel.id,
               "content": f"Searched: {profile_or_identifier} Teaminfo: {send_teaminfo}",
               "command": "getarkans",
               "server_profile": permissions['server_profile']}
        await self.embed_factory.logs(**log)
        await interaction.followup.send("Please wait a moment for me to retrieve the data for this user. Responses can sometimes take a moment, but if you do not get a response, please REEE @Gnomeslayer on discord! <@197979859773947906>", ephemeral=True)
        
        player_ids:model.Playerids = await self.fun.get_player_ids(profile_or_identifier)
        
        if not player_ids:
            await interaction.followup.send("Could not locate player. Please ensure you put 1 of the following types:\n"
                                            "Battlemetrics profile URL (example) <https://www.battlemetrics.com/rcon/players/12345>\n"
                                            "Steam Identifier (example) 76561198173991835"
                                            "Steam Profile URL (example) <https://steamcommunity.com/id/12345/>", ephemeral=True)
            return
        
        if player_ids.bmid:
            responses = await self.bmapi.activity_logs(filter_bmid=player_ids.bmid, filter_search="No Recoil probable violation", whitelist="unknown")
            if responses['data']:
                await interaction.followup.send("Found something. Will send you any ARKANS after processing.", ephemeral=True)
                reporter = Reporter(config=self.config, bot=self.bot)
                arkan_responses = []
                for response in responses['data']:
                    tempmsg = response['attributes']['message'].lower()
                    if "no recoil probable violation" in tempmsg:
                        response = await reporter.arkan(data=response)
                        arkan_responses.append(response)
                    else:
                        print(f"Despite our efforts, we still found something not arkan related:\n{tempmsg}")
            else:
                await interaction.followup.send("No Arkans :( guy must be shit.", ephemeral=True)
        else:
            await interaction.followup.send("Could not locate player. Please ensure you put 1 of the following types:\n"
                                            "Battlemetrics profile URL (example) <https://www.battlemetrics.com/rcon/players/12345>\n"
                                            "Steam Identifier (example) 76561198173991835"
                                            "Steam Profile URL (example) <https://steamcommunity.com/id/12345/>", ephemeral=True)
        
        if arkan_responses:
            arkans = ArkanButtons(config=self.config)
            arkans.arkans = arkan_responses
            embed = await self.embed_factory.arkan_embed(arkan_responses[0])
            await interaction.followup.send(embed=embed,view=arkans, ephemeral=True)
            if send_teaminfo:
                teaminfo = await self.fun.team_info(server_id=arkan_responses[0]['serverid'],steam_id=arkan_responses[0]['steamid'])
                if teaminfo.get('data'):
                    teaminfo = teaminfo['data']['attributes']['result']
                    teaminfo_embed = await self.embed_factory.set_teaminfo_embed(teaminfo=teaminfo, player_name="Unknown")
                    await interaction.followup.send(embed=teaminfo_embed, ephemeral=True)
                else:
                    await interaction.followup.send("Unable to grab team info data..Contact Gnomeslayer to figure this nonsense out.", ephemeral=True)
                    print(f"Failed to get teaminfo data in ARKANS\nSearched: {profile_or_identifier}\nServer: {arkan_responses[0]['serverid']}")