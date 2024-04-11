from supportfiles.functions import MainFunctions
import requests
import vdf
import discord
from discord.ext import commands, tasks

from discord import Embed
from re import search, findall, DOTALL
from datetime import datetime

class VDFchecker(commands.Cog):
    def __init__(self, bot, config):
        print("[Cog] VDFchecker has been initiated")
        self.users = []
        self.bot:commands.Bot = bot
        self.config:dict = config
        self.fun = MainFunctions(config=config)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.vdfcheckerresetter.start()

    @tasks.loop(seconds=30)
    async def vdfcheckerresetter(self):
        self.users = []

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.attachments:
            return
        
        message_attachment = message.attachments
        def lowercase_keys(obj):
            if isinstance(obj, dict):
                obj = {key.lower(): value for key, value in obj.items()}
                for key, value in obj.items():
                    if isinstance(value, list):
                        for idx, item in enumerate(value):
                            value[idx] = lowercase_keys(item)
                    obj[key] = lowercase_keys(value)
            return obj
        def _findaccounts(myfile):
            if "accounts" in myfile:
                return myfile["accounts"]
            for k, v in myfile.items():
                if isinstance(v, dict):
                    item = _findaccounts(v)
                    if item is not None:
                        return item
        def _findusers(myfile):
            if "users" in myfile:
                return myfile["users"]
            for k, v in myfile.items():
                if isinstance(v, dict):
                    item = _findusers(v)
                    if item is not None:
                        return item
        def _fixfile(myfile):
            contents = myfile
            # Find the "Accounts" section in the VDF file
            accounts_pattern = r'"Accounts"\s*{\s*(.*?)\s*}'
            accounts_match = search(
                accounts_pattern, contents, DOTALL)
            if accounts_match:
                # Iterate over each account in the "Accounts" section
                accounts_text = accounts_match.group(1)
                account_pattern = r'(".*?")\s*({)?'
                accounts = findall(account_pattern, accounts_text)
                open = True
                count = 1
                for i, account in enumerate(accounts):
                    name, brace = account
                    count += 1
                    if not brace:
                        if name.lower() != '"steamid"':
                            if open:
                                contents = contents.replace(
                                    name, name + '{', 1)
                                open = False
                            else:
                                if count != len(accounts):
                                    contents = contents.replace(
                                        name, name + '}', 1)
                                open = True
                    if brace:
                        open = False
            return contents
        for attachment in message_attachment:
            if "vdf" in attachment.filename:
                profiles = await self.fun.get_profiles(user_id=message.author.id, guildid=message.guild.id)
                if not profiles['user_profile'].approved:
                    return
                if not profiles['server_profile'].whitelisted:
                    return
                if profiles['blacklisted']:
                    return
                if not profiles['server_profile'].enable_vdf:
                    return
                
                if int(profiles['server_profile'].vdf_listen_channel):
                    if not int(profiles['server_profile'].vdf_listen_channel) == int(message.channel.id):
                        return
                
                await self.fun.store_logs(author_id=message.author.id,
                         author_name=message.author.name,
                         guild_name=message.guild.name,
                         guild_id=message.guild.id,
                         channel_id=message.channel.id,
                         channel_name=message.channel.name,
                         steam_id="0",
                         command="vdf")
                if profiles['server_profile'].show_logs:
                    guild = self.bot.get_guild(int(profiles['server_profile'].server_id))
                    log_channel = guild.get_channel(int(profiles['server_profile'].log_channel))
                    embed = Embed(title=f"LOGS!!",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x9b59b6", base=16))
                    embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
                    embed.add_field(name="Author Name and ID", value=f"```{message.author.name} - {message.author.id}```", inline=False)
                    embed.add_field(name="Guild Name and ID", value=f"```{message.guild.name} - {message.guild.id}```", inline=False)
                    embed.add_field(name="Channel Name and ID the command was used in", value=f"```{message.channel.name} - {message.channel.id}```", inline=False)
                    embed.add_field(name="Command Used", value=f"```Submitted a VDF File.```")
                    embed.add_field(name="Log Commands", value="Use the command `/get_all_logs` to retrieve all logs as a file.\nUse `/get_logs` to cycle through logs.", inline=False)
                    try:
                        await log_channel.send(embed=embed)
                    except:
                        pass
                
                usingcmd = ''
                checked_ids = []
                if message.author.id in self.users:
                    usingcmd = await message.reply("You are already using a command. Please wait until it finishes. (or this message dissappears)")
                    await usingcmd.delete(delay=30)
                    return
                else:
                    self.users.append(message.author.id)
                try:
                    if int(message.guild.id) == 975049069644886076:
                        waitmsg = await message.reply("Please wait a moment for me to search this file. Responses can sometimes take a moment, but if you do not get a response, please REEE @Gnomeslayer on discord! [Tag removed coz Gnome hates pings from bots.]")
                    else:
                        await message.reply("Please wait a moment for me to search this file. Responses can sometimes take a moment, but if you do not get a response, please REEE @Gnomeslayer on discord! <@197979859773947906>")
                except Exception as e:
                    await message.channel.send("Scanning of this VDF File has been rejected. Contact Gnomeslayer for further information. [RAH DISCORD](https://discord.gg/PrczhwME72)\nAlternatively you can just disable VDF Scanning entirely using /guildsettings")
                    with open('error_logs.txt', 'a') as file:
                        file.write(f"Error occured on command {e}\nUnable to scan VDF for some reason!\nGuild: {message.guild.name}\nGuild ID: {message.guild.id}\nAuthor: {message.author.name} - {message.author.id}")
                    return
                try:
                    await waitmsg.delete(delay=5)
                except:
                    pass
                attachment_url = attachment.url
                file_request = requests.get(attachment_url)
                data = file_request.content.decode("utf-8")
                matches = None
                new_dict = {}
                try:
                    myvdf = vdf.loads(data)
                except:
                    error_1 = await message.reply("There seems to be some issues with the file.. Attempting to fix..")
                    await error_1.delete(delay=5)
                    myvdf = _fixfile(data)
                    try:
                        myvdf = vdf.loads(myvdf)
                    except:
                        error_2 = await message.reply("Unable to fix the issues, resorting to a basic search")
                        await error_2.delete(delay=5)
                        pattern = r'"([^"]*7656[^"]*)"'
                        matches = findall(pattern, data)
                if matches:
                    for m in matches:
                        new_dict[m] = {'steamid': m}
                else:
                    myvdf = lowercase_keys(myvdf)
                    new_dict = _findaccounts(myvdf)
                accounts = {}
                if new_dict:
                    foundmsg = await message.reply(f"Found {len(new_dict)} accounts")
                    await foundmsg.delete(delay=5)
                    for k in new_dict:
                        if not new_dict[k].get('steamid'):
                            error_3 = await message.reply(f"The account {k} does not have a steamid, possibly deleted. Check the VDF File.")
                            await error_3.delete(delay=5)
                            continue
                        accounts[k] = {"steamid": new_dict[k]['steamid']}
                if not new_dict:
                    new_dict = _findusers(myvdf)
                if not new_dict:
                    nosteamids_msg = await message.reply("There are no steam ids in this file.")
                    await nosteamids_msg.delete(delay=5)
                    if message.author.id in self.users:
                        self.users.remove(message.author.id)
                    return
                if not accounts:
                    for k in new_dict:
                        accounts[new_dict[k]['accountname']] = {
                            "steamid": k}
                embed = Embed(title=f"VDF Check request by {message.author.name}", color=int(
                    "0x9b59b6", base=16))
                embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
                for k in accounts:
                    if accounts[k]['steamid'] in checked_ids:
                        duplicate_msg = await message.reply("Duplicate steam ID found. Ignoring.")
                        await duplicate_msg.delete(delay=5)
                        continue
                    else:
                        checked_ids.append(accounts[k]['steamid'])
                    user_ids = await self.fun.get_player_ids(submittedtext=accounts[k]['steamid'])
                    if user_ids:
                        if user_ids.discordid:
                            discord_profile = f"Linked to {len(user_ids.discordid)} discord account(s)."
                            for discordid in user_ids.discordid:
                                
                                response = await self.fun.check_cheetos(discord_id=discordid['discordid'])
                                if response:
                                    discord_profile += f"\nID: {discordid['discordid']} [{discordid['confidence']}%] - Linked to {len(response)} cheater discord(s)"
                        else:
                            discord_profile = "This user isn't linked to any discord accounts! You can link one using /linkids or allowing RAH to access your linking system! Contact the staff over at the [RAH DISCORD](https://discord.gg/6ryNzcKXFt) to learn more."
                        if user_ids.bmid:
                            player_info = await self.fun.get_player_info(user_ids.bmid)
                            user_account_status = None
                            if player_info.rustbanned_bool:
                                user_account_status = f"{player_info.rustbanned_text}"
                            if user_account_status:
                                embed.add_field(
                                    name=f"Steam ID: {accounts[k]['steamid']}", value=f"{user_account_status}\n{discord_profile}", inline=False)
                            else:
                                embed.add_field(
                                    name=f"Steam ID: {accounts[k]['steamid']}", value=f"No Serverbans or community bans\n{discord_profile}", inline=False)
                        else:
                            embed.add_field(
                                name=f"Steam ID: {accounts[k]['steamid']}", value="Could not find this user.", inline=False)
                    else:
                        embed.add_field(
                                name=f"Steam ID: {accounts[k]['steamid']}", value="Could not find this user.", inline=False)
                bot_response_1 = await message.reply(embed=embed)
                await message.delete(delay=300)
                await bot_response_1.delete(delay=300)
        if message.author.id in self.users:
            self.users.remove(message.author.id)
        return