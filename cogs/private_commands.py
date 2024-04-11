from supportfiles.functions import MainFunctions
import asyncio, os, json
from discord import Interaction, File, Member
from discord.ext import commands
from discord.app_commands import Choice, guild_only, command, choices


class PrivateCommands(commands.Cog):
    def __init__(self, bot, config):
        print("[Cog] private_commands has been initiated")
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.fun = MainFunctions(config=config)
        
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

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        content = f"""**Joined a guild:** {guild}
        **Guild ID:** {guild.id}
        **Guild Owner:** {guild.owner}
        **Guild Owner ID:** {guild.owner.id},
        **Whitelisted:** False"""
        await self.fun.register_guild(guildid=guild.id)
        await self.fun.send_joinleave(content=content)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        content = f"""**Removed from guild:** {guild}
        **Guild ID:** {guild.id}
        **Guild Owner:** {guild.owner}
        **Guild Owner ID:** {guild.owner.id},
        **Whitelisted:** False <Updated>,
        **All Users have been unapproved from this server.**"""
        await self.fun.authorize_server(guildid=guild.id, whitelisted=False)
        users = await self.fun.get_all_users_by_guild(guildid=guild.id)
        for user in users:
            await self.fun.approve_user(user_id=user.user_id,guildid=user.server_id, approved=False)
        managers = await self.fun.get_managers(guildid=guild.id)
        for manager in managers:
            await self.fun.remove_manager(guildid=guild.id,user_id=manager)
        await self.fun.send_joinleave(content=content)
        
    @commands.Cog.listener()
    async def on_memeber_remove(self, member:Member):
        guild_id = member.guild.id
        user_id = member.id
        await self.fun.approve_user(user_id=user_id, guildid=guild_id, approved=False)
        await self.fun.remove_manager(user_id=user_id,guildid=guild_id)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass
        else:
            with open('error_logs.txt', 'a') as file:
                file.write(f"Error occured on command {error}")
    
    @command(name="checkuser", description="Checks a user")
    @guild_only()
    async def checkuser(self, interaction: Interaction, userid: str, guildid:str = None):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        userinfo = await self.fun.search_user(userid=userid, guildid=guildid)
        message = None
        guild = None
        member_name = None
        if guildid:
            
            try:
                guild = self.bot.get_guild(int(userinfo['server_id']))
            except:
                pass
            
            if guild:
                guild_name = guild.name
                if not member_name:
                    member = guild.get_member(int(userid))
                    if member:
                        member_name = member.name
            else:
                guild_name = "Unknown"
            message = f"User ID: {userinfo['user_id']}\nServer ID: {userinfo['server_id']}\nServer Name: {guild_name}\nApproved: {userinfo['approved']}"
            
        elif userinfo:
            for info in userinfo:
                try:
                    guild = self.bot.get_guild(int(info['server_id']))
                except:
                    pass
                if guild:
                    guild_name = guild.name
                    if not member_name:
                        member = guild.get_member(int(userid))
                        if member:
                            member_name = member.name
                else:
                    guild_name = "Unknown"
                if message:
                    message += f"\n----\nUser ID: {info['user_id']}\nServer ID: {info['server_id']}\nServer Name: {guild_name}\nApproved: {info['approved']}"
                else:
                    message = f"User ID: {info['user_id']}\nServer ID: {info['server_id']}\nServer Name: {guild_name}\nApproved: {info['approved']}"
                    
        await self.fun.send_report(f"{interaction.user} used the command checkuser on {userid} ({member_name})")
        await interaction.response.send_message(f"Name: {member_name}\nID: {userid}\n```{message}```", ephemeral=True)


    @command(name="invitelink", description="Sends an invite link to channel")
    @guild_only()
    async def invitelink(self, interaction: Interaction):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        link = "`https://discord.com/oauth2/authorize?`"
        await self.fun.send_report(f"{interaction.user} used the command invitelink")
        await interaction.response.send_message(f"The invite link for this bot to send\n{link}", ephemeral=True)

    @command(name="leaveguild", description="Forces the bot to leave a guild")
    @guild_only()
    async def leaveguild(self, interaction: Interaction, guildid: str):
        mycheck = await self.super_staff_check(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        for guild in self.bot.guilds:
            if guild.id == int(guildid):
                await guild.leave()
                content = f"""**Removed from guild:** {guild}
                **Guild ID:** {guild.id}
                **Guild Owner:** {guild.owner}
                **Guild Owner ID:** {guild.owner.id}"""
                await self.fun.send_joinleave(content=content)
                await interaction.response.send_message("Left")
                return
        await interaction.response.send_message("I am not in that guild.")

    @command(name="listguilds", description="List guilds bot is in")
    @guild_only()
    async def listguilds(self, interaction: Interaction):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        guildlist = {}
        guilds_db = await self.fun.get_all_guilds()

        # Get a list of guilds the bot is in!
        for guild in self.bot.guilds:
            guildlist[str(guild.id)] = {
                "guild_name": guild.name,
                "guildid": guild.id,
                "guild_owner": guild.owner.name,
                "guild_owner_id": guild.owner.id
            }

        for guild_db in guilds_db:
            if not str(guild_db.server_id) in guildlist:
                await self.fun.authorize_server(guildid=guild_db.server_id, whitelisted=False)
                users = await self.fun.get_all_users_by_guild(guildid=guild_db.server_id)
                for user in users:
                    await self.fun.approve_user(user_id=user.user_id,guildid=guild_db.server_id, approved=False)
                managers = await self.fun.get_managers(guildid=guild_db.server_id)
                for manager in managers:
                    await self.fun.remove_manager(guildid=guild_db.server_id,user_id=manager)
        
                guildlist[str(guild_db.server_id)] = {
                    "Whitelisted": False,
                    "guildid": guild_db.server_id,
                    "notes": "Due to the bot no longer being in this discord server, the bot has blacklisted it until further notice.",
                    "organization_id": guild_db.organization_id,
                    "server_name": guild_db.server_name
                }
            else:
                guildlist[str(guild_db.server_id)
                          ]['organization_id'] = guild_db.organization_id
                guildlist[str(guild_db.server_id)
                          ]['server_name'] = guild_db.server_name
                guildlist[str(guild_db.server_id)
                          ]['Whitelisted'] = guild_db.whitelisted
        with open("guildlist.json", "w") as f:
            f.write(json.dumps(guildlist, indent=4))
        with open("guildlist.json", "rb") as f:
            await self.fun.send_report(f"{interaction.user} used the command listguilds")
            await interaction.response.send_message(file=File(f, filename="guildlist.json"))
        await asyncio.sleep(1)
        os.remove('guildlist.json')
    
    @command(name="addguild", description="Registers a guild inside of the bot")
    @guild_only()
    async def addguild(self, interaction: Interaction, guildid: str, whitelisted: bool = True):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return

        if not guildid:
            await interaction.response.send_message("Please enter a guild id.")
            return
        await self.fun.authorize_server(guildid=guildid, whitelisted=whitelisted)
        await self.fun.send_report(f"{interaction.user} used the command addguild, adding {guildid}")
        await interaction.response.send_message("Registered the guild. Whitelisted by default, unless you set it to false. In which case, it'll be fine.. I hope! :D.")

    @command(name="whitelist_guild", description="Sets a guild to whitelisted")
    @guild_only()
    async def whitelist_guild(self, interaction: Interaction, guildid: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        if not guildid:
            await interaction.response.send_message("Please enter a guild id.")
            return
        await self.fun.authorize_server(guildid=guildid, whitelisted=True)
        await self.fun.send_report(f"{interaction.user} used the command whitelist_guild, whitelissting {guildid}")
        await interaction.response.send_message("Whitelisted this guild. OR DID I?! hahaha na, I totally did.")

    @command(name="blacklist_guild", description="Sets a guild to blacklisted")
    @guild_only()
    async def blacklist_guild(self, interaction: Interaction, guildid: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        if not guildid:
            await interaction.response.send_message("Please enter a guild id.")
            return

        await self.fun.authorize_server(guildid=guildid, whitelisted=False)
        await self.fun.send_report(f"{interaction.user} used the command blacklist_guild, blacklisting {guildid}")
        await interaction.response.send_message("Blacklisted this guild, but why would I? It's just a meme bro.")

    @command(name="blacklist_user", description="Adds a user to the bots blacklist")
    @guild_only()
    async def blacklist_user(self, interaction: Interaction, member_id: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        await self.fun.add_blacklisted_user(user_id=member_id)
        await self.fun.send_report(f"{interaction.user} used the command blacklist_user, blacklisting {member_id}")
        await interaction.response.send_message(f"Added to the blacklist")

    @command(name="adduser", description="Adds a user to the database.")
    @guild_only()
    async def adduser(self, interaction:Interaction, user_id:str, guildid:str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        if not mycheck['manager'] and not interaction.guild.owner:
            await interaction.response.send_message("You aren't a manager or server owner.", ephemeral=True)
            return
        
        await self.fun.approve_user(user_id=user_id, guildid=guildid, approved=True)
        await interaction.response.send_message(f"Added user")
    
    @command(name="whitelist_user", description="Removes a user from the whitelist")
    @guild_only()
    async def whitelist_user(self, interaction: Interaction, member_id: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You cannot use this command.")
            return
        await self.fun.remove_blacklisted_user(user_id=member_id)
        await self.fun.send_report(f"{interaction.user} used the command whitelist_user, whitelisting {member_id}")
        await interaction.response.send_message(f"Removed {member_id} from the blacklist")
    
    @command(name="serverdetails", description="Sets the server details")
    @guild_only()
    async def serverdetails(self, interaction: Interaction, server_id: str, server_name: str, organization_id: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You are not authorized to use this command.")
            return

        await self.fun.send_report(f"{interaction.user} used the command serverdetails, with these details: server_id: {server_id}, server_name: {server_name}, organization ID: {organization_id}")
        await self.fun.update_server(guildid=server_id, server_name=server_name, organization_id=organization_id)
        await interaction.response.send_message("Updated the server details.", ephemeral=True)
        
    @command(name="setmanager", description="Forces a person to be manager for a server.")
    @guild_only()
    async def setmanager(self, interaction: Interaction, server_id: str, manager_id: str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You are not authorized to use this command.")
            return
        
        await self.fun.send_report(f"{interaction.user} used the command setmanager, setting {manager_id} as a manager for {server_id}")
        await self.fun.setmanager(guildid=server_id, manager_id=manager_id)
        await interaction.response.send_message("Set that user as a manager.", ephemeral=True)
    
    @command(name="rahforce", description="Forces RAH settings onto a server.")
    @guild_only()
    @choices(setting=[*rah_settings])
    async def rahforce(self, interaction: Interaction, guildid:str, setting: Choice[str], option: bool):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You are not RAH staff.", ephemeral=True)
        
        await self.fun.guild_setting(guildid=guildid,setting=setting.value,option=option)
        if option:
            await interaction.response.send_message(f"Enabled {setting.name} for that organization. Please enable RAH FORCE and Overwrite to force this on that server.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Disabled {setting.name} for that organization. Please enable RAH FORCE to force this on that server.", ephemeral=True)

    
    @command(name="forcerahpreset", description="Forces RAH settings onto a server.")
    @guild_only()
    @choices(setting=[*guildpresets])
    async def rahforcepreset(self, interaction: Interaction, guildid:str, setting: Choice[str]):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You are not RAH staff.", ephemeral=True)
        
        if setting.value.lower() == "rah lite":
            await self.fun.guild_setting(guildid=guildid, setting="include_cheetos", option=False)
            await self.fun.guild_setting(guildid=guildid, setting="include_notes", option=False)
            await self.fun.guild_setting(guildid=guildid, setting="include_alts", option=False)
            await self.fun.guild_setting(guildid=guildid, setting="include_serverbans", option=False)
            await self.fun.guild_setting(guildid=guildid, setting="include_stats", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="force_rah", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="overwrite_preferences", option=True)
            await interaction.response.send_message(f"Applied the {setting.name} preset to the targeted guild. Resulting in the following:\nUsing Cheetos: False\nIncluding Notes: False\nIncluding Alts: False\nIncluding Serverbans: False\nIncluding Stats: True\nForce Rah: True\nOverwrite Preferences: True", ephemeral=True)
        elif setting.value.lower() == "rah full":
            await self.fun.guild_setting(guildid=guildid, setting="include_cheetos", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="include_notes", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="include_alts", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="include_serverbans", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="include_stats", option=True)
            await self.fun.guild_setting(guildid=guildid, setting="force_rah", option=False)
            await self.fun.guild_setting(guildid=guildid, setting="overwrite_preferences", option=True)
            await interaction.response.send_message(f"Applied the {setting.name} preset to the targeted guild. Resulting in the following:\nUsing Cheetos: True\nIncluding Notes: True\nIncluding Alts: True\nIncluding Serverbans: True\nIncluding Stats: True\nForce Rah: False\nOverwrite Preferences: True", ephemeral=True)

    @command(name="add_link_api", description="Adds a link API")
    @guild_only()
    async def add_link_api(self, interaction:Interaction, guildid:str, url:str, token:str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You are not RAH staff.", ephemeral=True)
        
        await self.fun.add_link_api(guildid=guildid,url=url,token=token)
        await interaction.response.send_message("Done.", ephemeral=True)
        
    @command(name="remove_link_api", description="Removes a link API")
    @guild_only()
    async def remove_link_api(self, interaction:Interaction, guildid:str):
        mycheck = await self.mychecks(guild_id=interaction.guild.id, user_id=interaction.user.id)
        if not mycheck:
            await interaction.response.send_message("You are not RAH staff.", ephemeral=True)
        
        await self.fun.add_link_api(guildid=guildid,url=None,token=None)
        await interaction.response.send_message("Done.", ephemeral=True)
