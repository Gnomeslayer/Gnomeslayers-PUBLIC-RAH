from datetime import datetime
from discord import Interaction, Embed, Member, File, abc
from discord.ext import commands
from discord.app_commands import guild_only, command, Choice, choices
from supportfiles.embedfactory import EmbedFactory
from supportfiles.views.tos_buttons import TOS_Buttons
from supportfiles.views.logsbuttons import LogButtons

import os
import asyncio
import json
from supportfiles.functions import MainFunctions

class PublicCommands(commands.Cog):
    def __init__(self, bot, config):
        print("[Cog] public_commands has been initiated")
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.fun = MainFunctions(config=config)
        self.embed_factory = EmbedFactory(config=config, bot=bot)
    
    ignored_users = []
    
                
    user_settings = [
        Choice(name="Cheetos", value="include_cheetos"),
        Choice(name="Include Notes", value="include_notes"),
        Choice(name="Include Alts", value="include_alts"),
        Choice(name="Include Serverbans", value="include_serverbans"),
        Choice(name="Hide Responses", value="ephemeral_responses"),
        Choice(name="Include stats", value="include_stats"),
        Choice(name="Approved", value="approved")
        ]
    
    guild_settings = [
        Choice(name="Overwrite user settings", value="overwrite_preferences"),
        Choice(name="Use Cheetos", value="include_cheetos"),
        Choice(name="Share Data", value="sharing_data"),
        Choice(name="Include Stats", value="include_stats"),
        Choice(name="Include Notes", value="include_notes"),
        Choice(name="Include Alts", value="include_alts"),
        Choice(name="Include Serverbans",value="include_serverbans"),
        Choice(name="Hide Responses",value="ephemeral_responses"),
        Choice(name="Enable VDF", value="enable_vdf")
    ]
    
    rah_settings = [
        Choice(name="RAH Force", value="force_rah"),
        Choice(name="Overwrite user settings",
                            value="overwrite_preferences"),
        Choice(name="Use Cheetos", value="include_cheetos"),
        Choice(name="Share Data", value="sharing_data"),
        Choice(name="Include Stats", value="include_stats"),
        Choice(name="Include Notes", value="include_notes"),
        Choice(name="Include Alts", value="include_alts"),
        Choice(name="Include Serverbans",
                            value="include_serverbans"),
        Choice(name="Hide Responses",
                            value="ephemeral_responses"),
        Choice(name="Enable VDF", value="enable_vdf")
    ]
    
    userpresets = [
        Choice(name="RAH LITE", value="RAH LITE"),
        Choice(name="RAH FULL", value="RAH FULL")
    ]
    
    guildpresets = [
        Choice(name="RAH LITE", value="RAH LITE"),
        Choice(name="RAH FULL", value="RAH FULL")
    ]
    
    async def mychecks(self, guild_id, user_id):
        guild_list = [1]
        user_list = [1]
        if guild_id in guild_list and user_id in user_list:
            return True
        else:
            return False
    
    async def super_staff_check(self, guild_id, user_id):
        guild_list = [1]
        user_list = [1]
        if guild_id in guild_list and user_id in user_list:
            return True
        else:
            return False
    
    @command(name="rahtos", description="RAH TOS")
    @guild_only()
    async def rahtos(self, interaction: Interaction):        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if profiles:
            if profiles['signed_tos']:
                await interaction.response.send_message("You've already signed the TOS. You do not need to sign it again. **EVER**", ephemeral=True)
                return

        tosbuttons = TOS_Buttons(conifg=self.config)
        tosbuttons.config = self.config
        embed = Embed(
            title=f"RUST ADMIN TOS",
            color=int("0xe74c3c", base=16), description="**You Must Read and Accept the Terms Before You Use**")
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1078401845191516241/1080924975004917841/R.A.H_4.png")
        embed.add_field(
            name="Rule #1", value="Sharing any information from this bot is strictly forbidden.", inline=False)
        embed.add_field(
            name="Rule #2", value="Links and screenshots or references to the bot may NOT be used for ban notes.", inline=False)
        embed.add_field(
            name="Rule #3", value="This may not be shown or talked about to anyone that does not have access to it. Tickets, players, etc.", inline=False)
        embed.add_field(
            name="Rule #4", value="You accept that your guild usage of the bot will be monitored and can be removed for breaking these rules.", inline=False)
        embed.add_field(
            name="Rule #5", value="You Must have or be with a top 1000 rank BM organization and share read access with us in order to use the bot.", inline=False)
        embed.add_field(
            name="Completion", value="To complete the RAHTOS you need to supply one of the following: [Steam ID/URL](https://steamid.io/) or [BM Profile](https://www.battlemetrics.com/rcon/players)", inline=False)
        embed.add_field(
            name="Discord", value="[RAH DISCORD](https://gg/6ryNzcKXFt)", inline=False)
        await interaction.response.send_message(embed=embed, view=tosbuttons, ephemeral=True)

    @command(name="approve", description="Approves a user to use the discordbot")
    @guild_only()
    async def approve_user(self, interaction: Interaction, member: Member, force:bool = False):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return

        if member.id == interaction.user.id and interaction.guild.owner.id == interaction.user.id:
            await self.fun.approve_user(user_id=interaction.user.id, guildid=interaction.guild.id, approved=True)
            await interaction.response.send_message("""As you are the owner of the guild, you do not need to use this command on yourself. Only thing you need is to get your guild whitelisted, contact the staff on the official [RAH DISCORD](https://gg/6ryNzcKXFt) for assistance.\n
             But just as a precaution I set your status to approved, your server will still need to be whitelisted before you can use the bot.""", ephemeral=True)
            return
        # Don't exist or not whitelisted? Respond and exit.
        if not profiles['server_profile']:
            await interaction.response.send_message("This guild is not registered. Please register this guild.")
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            cheetos = await self.fun.check_cheetos(str(member.id))
            if force and mycheck:
                await self.fun.approve_user(user_id=str(member.id), guildid=interaction.guild.id, approved=True)
                await interaction.response.send_message(f"Approved {member.mention}")
            elif not cheetos:
                await self.fun.approve_user(user_id=str(member.id), guildid=interaction.guild.id, approved=True)
                await interaction.response.send_message(f"Approved {member.mention}")
            else:
                await self.fun.approve_user(user_id=str(member.id), guildid=interaction.guild.id, approved=False)
                await interaction.response.send_message(f"Targeted member was rejected as they're seen in {len(cheetos)} discord(s). Contact official [RAH DISCORD](https://gg/6ryNzcKXFt) Staff if you think this is an error.", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)

    @ command(name="unapprove", description="Unapproves a user to use the discordbot")
    @ guild_only()
    async def unapprove_user(self, interaction: Interaction, member: Member = None, member_id:str = None):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        memberid = member_id
        if member:
            memberid = member.id
        if not memberid:
            await interaction.response.send_message("please enter a valid member id.", ephemeral=True)
            return
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if str(memberid) == str(interaction.user.id) and interaction.guild.owner.id == interaction.user.id:
                await interaction.response.send_message("As you are the owner of the guild, you do not need to use this command on yourself. Only thing you need is to get your guild whitelisted, contact the staff on the official [RAH DISCORD](https://gg/6ryNzcKXFt) for assistance.", ephemeral=True)
                return
        # Don't exist or not whitelisted? Respond and exit.
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.approve_user(user_id=memberid, guildid=interaction.guild.id, approved=False)
            await interaction.response.send_message(f"Removed that user from the approval list. They can no longer use the bot on this server.")
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)


    @command(name="addmanager", description="Adds a manager to your ")
    @guild_only()
    async def addmanager(self, interaction: Interaction, member: Member):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck:
            cheetos = await self.fun.check_cheetos(str(member.id))
            if cheetos:
                if len(cheetos) >= 1:
                    await interaction.response.send_message(f"Targeted member was rejected as they're seen in {len(cheetos)} discord(s). Contact official [RAH DISCORD](https://gg/6ryNzcKXFt) Staff if you think this is an error.", ephemeral=True)
                    return
            await self.fun.add_manager(user_id=member.id, guildid=interaction.guild.id)
            if mycheck:
                await self.fun.send_report(f"{interaction.user} used the command addmanager, adding {member.id} as a manager")
            await interaction.response.send_message(f"Added {member.mention} to the managers list.", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners.", ephemeral=True)

    @command(name="removemanager", description="Removes a manager from your ")
    @guild_only()
    async def removemanager(self, interaction: Interaction, member: Member):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck:
            await self.fun.remove_manager(user_id=member.id, guildid=interaction.guild.id)
            if mycheck:
                await self.fun.send_report(f"{interaction.user} used the command removemanager, removing {member.id} as a manager")
            await interaction.response.send_message(f"Removed {member.mention} from the manager list. Also set their approval status to false.", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners.", ephemeral=True)

    @command(name="managerlist", description="Lists the managers linked to the RAH bot on your server.")
    @guild_only()
    async def managerlist(self, interaction: Interaction):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile']:
            await self.fun.register_guild(guildid=interaction.guild.id)
            profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            response = await self.fun.get_managers(guildid=interaction.guild.id)
            managers = None
            for manager in response:
                if not managers:
                    managers = f"ID: **{manager}** - <@{manager}>"
                else:
                    managers += f"\nID: **{manager}** - <@{manager}>"
            if managers:
                await interaction.response.send_message(f"{managers}", ephemeral=True)
            else:
                await interaction.response.send_message(f"You have no managers. Consider adding some using /addmanager", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners.", ephemeral=True)

    @command(name="serversettings", description="Shows your server settings.")
    @guild_only()
    async def serversettings(self, interaction: Interaction):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            guild_info = await self.fun.get_guild(guildid=interaction.guild.id)

            embed = Embed(title=f"Server settings",
                                  description=f"""**Guild name**: {guild_info.server_name}
                                  **Guild ID**: {guild_info.server_id}
                                  **Organization ID**: {guild_info.organization_id}
                                  **Whitelisted**: {guild_info.whitelisted}
                                  **Overwrite User Settings**: {guild_info.overwrite_preferences}
                                  **Ephemeral Responses**: {guild_info.ephemeral_responses}
                                  **Show Logs**: {guild_info.show_logs}
                                  **Enable VDF**: {guild_info.enable_vdf}
                                  **Sharing Data**: {guild_info.sharing_data}
                                  **Getting Alts**: {guild_info.include_alts}
                                  **Getting Stats**: {guild_info.include_stats}
                                  **Getting Serverbans**: {guild_info.include_serverbans}
                                  **Getting Notes**: {guild_info.include_notes},
                                  **Forced Settings By RAH**: {guild_info.force_rah}""",
                                  color=int("0x9b59b6", base=16))
            embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
            if guild_info.show_logs:
                embed.add_field(name="Log Channel",
                                value=f"```{guild_info.log_channel}```", inline=False)

            if guild_info.api_token:
                embed.add_field(name="API Token",
                                value=f"```An API token has been registered, but for security purposes it is not shown.```", inline=False)
            if guild_info.banlist:
                embed.add_field(name="Banlist",
                                value=f"```{guild_info.banlist}```", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)

    @command(name="enablelogs", description="Enables/Disables Logs")
    @guild_only()
    async def enablelogs(self, interaction: Interaction, setting:bool):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
                await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
                return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.setting_show_logs(guildid=interaction.guild.id, setting=setting)
            if setting:
                await interaction.response.send_message("RAH will now show logs. Please ensure you've set a log channel using /setlogchannel. This takes a channel ID\n**Enable Developer Mode**\nUser Settings -> Advanced (Under app settings) -> Developer Mode\n**Getting channel ID**\nRight click the target channel -> Copy Channel ID", ephemeral=True)
            else:
                await interaction.response.send_message("RAH will no longer show logs.", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
            
    @command(name="setlogchannel", description="Sets a log channel for RAH logging.")
    @guild_only()
    async def setlogchannel(self, interaction: Interaction, log_channel: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if not log_channel.isdigit():
            await interaction.response.send_message("Please enter a channel ID.\n**Enable Developer Mode**\nUser Settings -> Advanced (Under app settings) -> Developer Mode\n**Getting channel ID**\nRight click the target channel -> Copy Channel ID", ephemeral=True)
            return
        
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.setting_log_channel(guildid=interaction.guild.id, channel_id=log_channel)
            await interaction.response.send_message("RAH Log Channel set.", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
            
    @command(name="listusers", description="List the authorized users on your server")
    @guild_only()
    async def listusers(self, interaction: Interaction):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            users = await self.fun.get_all_users_by_guild(guildid=interaction.guild.id)
            
            user_list = []
            for user in users:
                member = self.bot.get_user(int(user.user_id))
                manager = False
                usercheck = await self.fun.get_profiles(user_id=user.user_id, guildid=user.server_id)
                
                if usercheck.get('managers'):
                    manager = True
                membername = "Unknown/Not in this guild"
                if member:
                    membername = member.name
                user_list.append({
                    'user_id': user.user_id,
                    'user_name': membername,
                    'approved': user.approved,
                    'manager': manager,
                    'signed_tos': usercheck['signed_tos']
                })
            with open("userlist.json", "w") as f:
                f.write(json.dumps(user_list, indent=4))
            with open("userlist.json", "rb") as f:
                await interaction.response.send_message(file=File(f, filename="userlist.json"), ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)

    @command(name="guildsettings", description="Enables/Disables various settings for your guild regarding RAH")
    @guild_only()
    @choices(setting=[*guild_settings])
    async def guildsettings(self, interaction: Interaction, setting: Choice[str], option:bool):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if profiles['server_profile'].force_rah:
            await interaction.response.send_message("RAH is forcing server settings upon your organization. Contact them [here](https://gg/5xHrC4qhfN) if there was an error.", ephemeral=True)
            return
            
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            if profiles['server_profile'].force_rah:
                await interaction.response.send_message("RAH is forcing server settings upon your organization. Contact them [here](https://gg/5xHrC4qhfN) if there was an error.", ephemeral=True)
                return
            await self.fun.guild_setting(guildid=interaction.guild.id, setting=setting.value, option=option)
            if option:
                await interaction.response.send_message(f"Enabled {setting.name}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Disabled {setting.name}", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
            
    @command(name="usersettings", description="Enables/Disables various settings for your guild members regarding RAH")
    @guild_only()
    @choices(setting=[*user_settings])
    async def usersettings(self, interaction: Interaction, user:Member, setting: Choice[str], option:bool):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.user_setting(guildid=interaction.guild.id,user_id=user.id, setting=setting.value, option=option)
            if option:
                await interaction.response.send_message(f"Enabled {setting.name} for {user} - This will only take affect if you have 'Overwrite user Settings' set to false.", ephemeral=True)
            else:
                await interaction.response.send_message(f"Disabled {setting.name} for {user} - This will only take affect if you have 'Overwrite user Settings' set to false.", ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
         
    @command(name="userprofilepresets", description="Presets for profiles so you don't have to manually do each one.")
    @guild_only()
    @choices(presets=[*userpresets])
    async def user_presets(self, interaction: Interaction, user: Member, presets:Choice[str]):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if presets.value.lower() == "rah lite":
            option = False
        elif presets.value.lower() == "rah full":
            option = True
        
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.user_setting(guildid=interaction.guild.id, user_id=user.id, setting="include_cheetos", option=option)
            await self.fun.user_setting(guildid=interaction.guild.id, user_id=user.id, setting="include_notes", option=option)
            await self.fun.user_setting(guildid=interaction.guild.id, user_id=user.id, setting="include_alts", option=option)
            await self.fun.user_setting(guildid=interaction.guild.id, user_id=user.id, setting="include_serverbans", option=option)
            await self.fun.user_setting(guildid=interaction.guild.id, user_id=user.id, setting="include_stats", option=option)
            
            await interaction.response.send_message(f"Applied the {presets.name} preset to {user.name}. Resulting in the following:\nUsing Cheetos: {option}\nIncluding Notes: {option}\nIncluding Alts: {option}\nIncluding Serverbans: {option}\nIncluding Stats: True", ephemeral=True)
            
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
    
    @command(name="rah_listen", description="Sets a channel for RAH to listen to.")
    @guild_only()
    async def rah_listen(self, interaction: Interaction, channel:abc.GuildChannel):
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="rah_listen_channel", option=channel.id)
            await interaction.response.send_message(f"RAH will now listen for steam ID's in that channel. You can still use /rah")
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
            
    @command(name="vdf_listen", description="Sets a channel for RAH to listen to.")
    @guild_only()
    async def vdf_listen(self, interaction: Interaction, channel:abc.GuildChannel):
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="vdf_listen_channel", option=channel.id)
            await interaction.response.send_message(f"RAH will now listen for VDF Files in that channel.")
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
            
    @command(name="guildprofilepresets", description="Presets for profiles so you don't have to manually do each one.")
    @guild_only()
    @choices(presets=[*guildpresets])
    async def guild_presets(self, interaction: Interaction, presets: Choice[str]):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return

        if profiles['server_profile'].force_rah:
            await interaction.response.send_message("RAH is forcing server settings upon your organization. Contact them [here](https://gg/5xHrC4qhfN) if there was an error.", ephemeral=True)
            return
        
        if presets.value.lower() == "rah lite":
            option = False
        elif presets.value.lower() == "rah full":
            option = True
            
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="include_cheetos", option=option)
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="include_notes", option=option)
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="include_alts", option=option)
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="include_serverbans", option=option)
            await self.fun.guild_setting(guildid=interaction.guild.id, setting="include_stats", option=option)

            await interaction.response.send_message(f"Applied the {presets.name} preset to your guild. Resulting in the following:\nUsing Cheetos: {option}\nIncluding Notes: {option}\nIncluding Alts: {option}\nIncluding Serverbans: {option}\nIncluding Stats: True", ephemeral=True)

        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)

    @command(name="get_logs", description="Gets logs")
    @guild_only()
    async def get_logs(self, interaction:Interaction, guildid:str=None, steam_id:str=None, author_id:str=None, command:str=None):
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return
        if profiles['blacklisted']:
            await interaction.response.send_message("You're blacklisted...")
            
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            if guildid:
                logs = await self.fun.get_logs_by_guild(guildid)
            elif steam_id:
                logs = await self.fun.get_logs_by_steamid(steam_id)
            elif author_id:
                logs = await self.fun.get_logs_by_author(author_id)
            elif command:
                logs = await self.fun.get_logs_by_command(command)
            else:
                await interaction.response.send_message("Please input 1 of the paramaters...", ephemeral=True)
                return
            if not logs:
                await interaction.response.send_message("No logs to be found.", ephemeral=True)
                return
            
            embed = await self.embed_factory.create_log_embed(logs[0])
            log_buttons = LogButtons(config=self.config)
            log_buttons.logs = logs
            await interaction.response.send_message(embed=embed, view=log_buttons, ephemeral=True)
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
            
    @command(name="get_all_logs", description="Gets logs")
    @guild_only()
    async def get_all_logs(self, interaction:Interaction, guildid:str=None, steam_id:str=None, author_id:str=None, command:str=None):
        profiles = await self.fun.get_profiles(guildid=interaction.guild.id, user_id=interaction.user.id)
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        
        if not profiles:
            await interaction.response.send_message("You need to first sign the RAH TOS before you can use a command. /rahtos", ephemeral=True)
            return
        if not profiles['server_profile'].whitelisted:
            await interaction.response.send_message("This guild is not whitelisted. Please contact the staff on the official RAH ")
            return
        if profiles['blacklisted']:
            await interaction.response.send_message("You're blacklisted...")
            
        if interaction.user == interaction.guild.owner or mycheck or profiles.get('managers'):
            if guildid:
                logs = await self.fun.get_logs_by_guild(guildid)
            elif steam_id:
                logs = await self.fun.get_logs_by_steamid(steam_id)
            elif author_id:
                logs = await self.fun.get_logs_by_author(author_id)
            elif command:
                logs = await self.fun.get_logs_by_command(command)
            else:
                await interaction.response.send_message("Please input 1 of the paramaters...", ephemeral=True)
                return
            if not logs:
                await interaction.response.send_message("No logs to be found.", ephemeral=True)
                return
            new_logs = []
            for log in logs:
                log = {
                    'author_id': log['author_id'],
                    'author_name': log['author_name'],
                    'guild_name': log['guild_name'],
                    'guild_id': log['guild_id'],
                    'channel_id': log['channel_id'],
                    'channel_name': log['channel_name'],
                    'steam_id': log['steam_id'],
                    'command': log['command'],
                    'time': log['time']
                }
                new_logs.append(log)
            with open(f"{interaction.user.id}_logs_file.json", "w") as f:
                f.write(json.dumps(new_logs, indent=4))
            await interaction.response.send_message(file=File(f"{interaction.user.id}_logs_file.json"), ephemeral=True)
            await asyncio.sleep(1)
            os.remove(f"{interaction.user.id}_logs_file.json")
        else:
            await interaction.response.send_message("This command is limited to server owners and managers.", ephemeral=True)
