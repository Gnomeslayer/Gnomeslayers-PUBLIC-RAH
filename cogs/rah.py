from discord import Interaction, Message
from discord.app_commands import guild_only, command
from discord.ext import commands, tasks
from supportfiles.embedfactory import EmbedFactory
from supportfiles.views.profilebuttons import ProfileButtons


from supportfiles.functions import MainFunctions
import asyncio


class Rah(commands.Cog):
    def __init__(self, bot, config):
        print("[Cog] Rust Admin Helper has been initiated")
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.rahresetter.start()
        self.fun = MainFunctions(config=config)
        self.embed_factory = EmbedFactory(config=config, bot=bot)

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
    
    async def search(self, search, guild_id, server_profile):
        try:
            # Fetch player IDs asynchronously
            player_ids = await self.fun.get_player_ids(search)
            # Check if player IDs are retrieved and if bmid is present
            if not player_ids or not player_ids.bmid:
                return None, None, None
            # Prepare asynchronous tasks to gather player information
            tasks = [
                self.fun.get_player_info(player_id=player_ids.bmid),
                self.fun.get_related_players(player_ids.bmid),
                self.fun.get_player_notes(player_id=player_ids.bmid, guild_id=guild_id),
                self.fun.get_player_bans(player_id=player_ids.bmid, guild_id=guild_id)
            ]
            
            # Gather responses from asynchronous tasks
            responses = await asyncio.gather(*tasks)
            player_profile, related_players, player_notes, server_bans = responses
            
            # Obtain Steam ID if not present in player_ids
            if not player_ids.steamid:
                player_ids.steamid = player_profile.steam_id
                if player_ids.steamid:
                    player_ids = await self.fun.get_player_ids(player_ids.steamid)
            
            # Sort related players
            sorted_related = []
            for category in ['vac_banned_related', 'rustbanned_related', 'regular_related']:
                sorted_related.extend(related_players[category])
                
            # Generate Discord profile information
            if server_profile.include_cheetos:
                discord_profile = await self.generate_discord_profile_with_cheetos(player_ids)
            else:
                discord_profile = await self.generate_discord_profile(player_ids)
            # Create embed with player details
            embed = await self.embed_factory.create_profile_embed(player_ids=player_ids,
                                            player_profile=player_profile,
                                            player_notes=player_notes,
                                            server_bans=server_bans,
                                            discord_profile=discord_profile,
                                            related_players=related_players)
            
            # Create profile buttons
            profile_buttons = await self.create_profile_buttons(server_bans, player_notes, sorted_related, player_profile)
            
            return embed, profile_buttons, None

        except Exception as e:
            # Handle any exceptions and log them
            with open('error_logs.txt', 'a') as file:
                file.write(f"Error occured on command {e}")
            error = "An error has occured. Please contact gnomeslayer on discord!"
            return None, None, error

    # Helper functions for generating Discord profile information
    async def generate_discord_profile(self, player_ids):
        if player_ids.discordid:
            discord_profiles = [f"ID: {discord['discordid']} [{discord['confidence']}%]" for discord in player_ids.discordid]
            return f"Linked to {len(player_ids.discordid)} discord account(s).\n" + '\n'.join(discord_profiles)
        else:
            return "This user isn't linked to any discord accounts! You can link one using /linkids or allowing RAH to access your linking system!\nContact the staff over at the RAH DISCORD - https://discord.gg/6ryNzcKXFt to learn more."

    async def generate_discord_profile_with_cheetos(self, player_ids):
        discord_profiles = []
        for player_discord in player_ids.discordid:
            response = await self.fun.check_cheetos(discord_id=int(player_discord['discordid']))
            if response:
                discord_profiles.append(f"ID: {player_discord['discordid']} [{player_discord['confidence']}%] - Linked to {len(response)} cheater discord server(s)")
            else:
                discord_profiles.append(f"ID: {player_discord['discordid']} [{player_discord['confidence']}%]")
        return f"Linked to {len(player_ids.discordid)} discord account(s).\n" + '\n'.join(discord_profiles)

    # Helper function for creating profile buttons
    async def create_profile_buttons(self, server_bans, player_notes, sorted_related, player_profile):
        profile_buttons = ProfileButtons(config=self.config)
        profile_buttons.clear_items()
        profile_buttons.serverbans = server_bans['ban_info']
        profile_buttons.notes = player_notes['note_data']
        profile_buttons.related_players = sorted_related
        profile_buttons.original_player = player_profile
        if sorted_related:
            profile_buttons.add_item(profile_buttons.view_related)
        if player_notes['note_data']:
            profile_buttons.add_item(profile_buttons.view_notes)
        if server_bans['ban_info']:
            profile_buttons.add_item(profile_buttons.view_serverbans)
        profile_buttons.add_item(profile_buttons.view_activity_logs)
        return profile_buttons

    
    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return
        profiles = await self.fun.get_profiles(user_id=message.author.id, guildid=message.guild.id)
        profiles['cooldown'] = False
        if not int(profiles['server_profile'].rah_listen_channel) == int(message.channel.id):
            return
        if not profiles['user_profile'].approved:
            await message.reply("You are not authorized to use this command. Contact Gnomeslayer (<@197979859773947906>) on discord or the official [RAH Discord](https://discord.gg/4evCkANXmE) if you believe this is an error")
            return
        if not profiles['server_profile'].whitelisted:
            await message.reply("This server is not authorized to use this command. Contact Gnomeslayer (<@197979859773947906>) on discord or the official [RAH Discord](https://discord.gg/4evCkANXmE) if you believe this is an error")
            return
        if profiles['blacklisted']:
            await message.reply("You are not authorized to use this command. Contact Gnomeslayer (<@197979859773947906>) on discord or the official [RAH Discord](https://discord.gg/4evCkANXmE) if you believe this is an error")
            return
        
        if message.author.id in self.users:
            profiles['cooldown'] = True
        else:
            self.users.append(message.author.id)
            
        if profiles['cooldown']:
            await message.reply("This command is on cooldown. Please wait around 15 seconds before trying again!")
            return
        
        log = {
               "author_id": message.author.id,
               "author_name": message.author.name,
               "guild_name": message.guild.name,
               "guild_id":message.guild.id,
               "channel_id": message.channel.id,
               "channel_name": message.channel.name,
               "content": message.content,
               "command": "rah",
               "server_profile": profiles['server_profile']}
        
        await self.embed_factory.logs(**log)
        if int(message.guild.id) == 1:
            await message.reply("Please wait a moment for me to retrieve the data for this user. Responses can sometimes take a moment, but if you do not get a response, please REEE @Gnomeslayer on discord! [Tag removed coz Gnome hates pings from bots.]")
        else:
            await message.reply("Please wait a moment for me to retrieve the data for this user. Responses can sometimes take a moment, but if you do not get a response, please REEE @Gnomeslayer on discord! <@197979859773947906>")
        #try:
        embed, profilebuttons, errors = await self.search(search=message.content, guild_id=message.guild.id, server_profile=profiles['server_profile'])
        if errors:
            await message.reply(errors)
            return
        if embed or profilebuttons:
            await message.reply(view=profilebuttons, embed=embed)
        else:
            await message.reply(content="No results found.")
        #except:
        #    print(f"\nERRORR!!!\nMessage content: {message.content}\nGuild ID: {message.guild.id}\nPermissions: {permissions}")
        #    await message.reply("Something went tragically wrong. Proceed to REEE @ Gnomeslayer on discord. Please. Seriously. If you're seeing this, it means you arent getting results. we're all doomed. The sky is falling. OH NO!!!! Oh wait. just an apple. Nevermind. Seriously tho. Message @ Gnomeslayer on discord.")
            
    @command(name="rah", description="Searches a users profile")
    @guild_only()
    async def rah(self, interaction: Interaction, steam_id_or_url:str):
        await interaction.response.defer(ephemeral=True)
        
        profiles = await self.fun.get_profiles(user_id=interaction.user.id, guildid=interaction.guild.id)
        profiles['cooldown'] = False
        
        if not profiles['user_profile'].approved:
            await interaction.followup.send("You are not authorized to use this command. Contact Gnomeslayer (<@197979859773947906>) on discord or the official [RAH Discord](https://discord.gg/4evCkANXmE) if you believe this is an error", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.followup.send("This server is not authorized to use this command. Contact Gnomeslayer (<@197979859773947906>) on discord or the official [RAH Discord](https://discord.gg/4evCkANXmE) if you believe this is an error", ephemeral=True)
            return
        if profiles['blacklisted']:
            await interaction.followup.send("You are not authorized to use this command. Contact Gnomeslayer (<@197979859773947906>) on discord or the official [RAH Discord](https://discord.gg/4evCkANXmE) if you believe this is an error", ephemeral=True)
            return
        
        if interaction.user.id in self.users:
            profiles['cooldown'] = True
        else:
            self.users.append(interaction.user.id)
            
        if profiles['cooldown']:
            await interaction.followup.send("This command is on cooldown. Please wait around 15 seconds before trying again!", ephemeral=True)
            return
        
        if profiles['cooldown']:
            await interaction.followup.send("This command is on cooldown. Please wait around 15 seconds before trying again!", ephemeral=True)
            return
        
        log = {
               "author_id": interaction.user.id,
               "author_name": interaction.user.name,
               "guild_name": interaction.guild.name,
               "guild_id":interaction.guild.id,
               "channel_id": interaction.channel.id,
               "channel_name": interaction.channel.name,
               "content": steam_id_or_url,
               "command": "rah",
               "server_profile": profiles['server_profile']}
        await self.embed_factory.logs(**log)
        await interaction.followup.send("Please wait a moment for me to retrieve the data for this user. Responses can sometimes take a moment, but if you do not get a response, please REEE @Gnomeslayer on discord! <@197979859773947906>", ephemeral=True)
        
        #try:
        embed, profilebuttons, errors = await self.search(search=steam_id_or_url, guild_id=interaction.guild.id, server_profile=profiles['server_profile'])
        if errors:
            await interaction.followup.send(content=errors, ephemeral=True)
            return
        if embed or profilebuttons:
            await interaction.followup.send(view=profilebuttons, embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(content="No results found.", ephemeral=True)
        #except:
        #    print(f"\nERRORR!!!\nMessage content: {steam_id_or_url}\nGuild ID: {interaction.guild.id}\nPermissions: {permissions}")
        #    await interaction.followup.send("Something went tragically wrong. Proceed to REEE @ Gnomeslayer on discord. Please. Seriously. If you're seeing this, it means you arent getting results. we're all doomed. The sky is falling. OH NO!!!! Oh wait. just an apple. Nevermind. Seriously tho. Message @ Gnomeslayer on discord.", ephemeral=True)