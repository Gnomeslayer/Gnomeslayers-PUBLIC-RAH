from discord import Embed
from discord.ext.commands import Bot
from supportfiles.functions import MainFunctions
from datetime import datetime
import supportfiles.model as model
import asyncio
from battlemetrics import Battlemetrics

class EmbedFactory():
    def __init__(self, config, bot:Bot):
        self.config = config
        self.bot = bot
        self.api = Battlemetrics(config['tokens']['battlemetrics_token'])
        self.fun = MainFunctions(config=config)
        
    async def _sort_combatlog(self, combatlog:str) -> dict:
        lines = combatlog.strip().split("\n")
        header = lines[0].split()

        result_dict = []
        for line in lines[1:]:
            values = line.split()
            entry = {}
            count = 0
            if values[0] == "+":
                break
            for i in values:
                entry[header[count]] = i
                count += 1
            result_dict.append(entry)
        result_dict.reverse()
        return result_dict

    async def _get_discord_profile(self, player_ids:model.Playerids) -> str:
        if player_ids.discordid:
            discord_profile = f"Linked to {len(player_ids.discordid)} discord account(s)."
            for player_discord in player_ids.discordid:
                response = await self.fun.check_cheetos(discord_id=player_discord['discordid'])
                if response:
                    discord_profile += f"\nID: {player_discord['discordid']} [{player_discord['confidence']}%] - Linked to {len(response)} cheater discord(s)"
                else:
                    discord_profile += f"\nID: {player_discord['discordid']} [{player_discord['confidence']}%]"
        else:
            discord_profile = "This user isn't linked to any discord accounts! You can link one using /linkids or allowing RAH to access your linking system!\nContact the staff over at the RAH DISCORD - https://discord.gg/6ryNzcKXFt to learn more."
        return discord_profile
    
    async def set_combatlog_embed(self, combatlog:dict, player_name:str, steam_id:int) -> Embed:
            
            sorted_log =  await self._sort_combatlog(combatlog)
            
            player_details = {}
            embed_description = None
            combatlog_fields = 0
            
            for item in sorted_log:
                
                if combatlog_fields == 2:
                    break
                
                if (item["attacker"] == "you" and item["target"] == "player") or (item["attacker"] == "player" and item["target"] == "you"):
                    time = item["time"]
                    players_steam_url = f"[You](https://steamcommunity.com/profiles/{steam_id})"
                    
                        
                    id = item["id"]
                    if id in player_details:
                        if player_details[id]["bmid"]:
                            battlemetrics_link = f"[{id}](https://www.battlemetrics.com/rcon/players/{player_details[id]['bmid']})"
                        else:
                            battlemetrics_link = f"{id}"
                    else:
                        battlemetrics_profile = await self.fun.activity_logs_search(search=id)
                        player_details[id] = {}
                        try:
                            player_details[id]["bmid"] = int(battlemetrics_profile["data"][0]["relationships"]["players"]["data"][0]["id"])
                            battlemetrics_link = f"[{id}](https://www.battlemetrics.com/rcon/players/{player_details[id]['bmid']})"
                        except:
                            player_details[id]["bmid"] = 0
                            battlemetrics_link = f"{id}"

                    
                    if item["attacker"] == "you":
                        attacker = players_steam_url
                    else:
                        attacker = battlemetrics_link
                    
                    if item["target"] == "you":
                        target = players_steam_url
                    else:
                        target = battlemetrics_link
                        
                    weapon = "weapon"
                    ammo = item["ammo"]
                    area = item["area"]
                    distance = item["distance"]
                    hp_change = f"{item['old_hp']} > {item['new_hp']}"
                    if not embed_description:
                        embed_description = f"{time} - {attacker} - {target} - {weapon} - {ammo} - {area} - {distance} - {hp_change}"
                    else:
                        embed_description += f"\n{time} - {attacker} - {target} - {weapon} - {ammo} - {area} - {distance} - {hp_change}"
                    if len(embed_description) >= 3500:
                        break
                    
            embed = Embed(title=f"Combatlog for {player_name}", description=embed_description)
            return embed
        
    async def error_embed(self, message:str) -> Embed:
        embed = Embed(title=f"Error", description=f"{message}", color=int("0x9b59b6", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        return embed
        
    async def create_log_embed(self, log:dict) -> Embed:
        embed = Embed(title=f"LOGS!!",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x9b59b6", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.add_field(name="Author Name and ID", value=f"```{log['author_name']} - {log['author_id']}```", inline=False)
        embed.add_field(name="Guild Name and ID", value=f"```{log['guild_name']} - {log['guild_id']}```", inline=False)
        embed.add_field(name="Channel Name and ID the command was used in", value=f"```{log['channel_name']} - {log['channel_id']}```", inline=False)
        embed.add_field(name="Command Used", value=f"```{log['command']}```")
        embed.add_field(name="Steam ID Involved", value=f"```{log['steam_id']}```")
        embed.add_field(name="Log Commands", value="Use the command `/get_all_logs` to retrieve all logs as a file.", inline=False)
        return embed
            
    async def logs(self, author_id:str, author_name:str, guild_name:str,
                   guild_id:str, channel_id:str, channel_name:str, content:str,
                   command:str, server_profile:model.ServerProfile) -> None:
        await self.fun.store_logs(author_id=author_id,
                            author_name=author_name,
                            guild_name=guild_name,
                            guild_id=guild_id,
                            channel_id=channel_id,
                            channel_name=channel_name,
                            steam_id=content,
                            command=command)
        if server_profile.show_logs:
            guild = self.bot.get_guild(int(server_profile.server_id))
            log_channel = guild.get_channel(int(server_profile.log_channel))
            embed = Embed(title=f"LOGS!!",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x9b59b6", base=16))
            embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
            embed.add_field(name="Author Name and ID", value=f"```{author_name} - {author_id}```", inline=False)
            embed.add_field(name="Guild Name and ID", value=f"```{guild_name} - {guild_id}```", inline=False)
            embed.add_field(name="Channel Name and ID the command was used in", value=f"```{channel_name} - {channel_id}```", inline=False)
            embed.add_field(name="Command and Content", value=f"**{command}**```{content}```")
            embed.add_field(name="Log Commands", value="Use the command `/get_all_logs` to retrieve all logs as a file.\nUse `/get_logs` to cycle through logs.", inline=False)
            try:
                await log_channel.send(embed=embed)
            except:
                pass
            
    async def create_settings_embed(self, settings:model.MonitorSettings) -> Embed:
        embed = Embed(title=f"Auto Mod Settings", 
                    description=f"Will respond to messages with an accuracy of: {settings.match_strength_percent}% or more",
                    color=int("0x9b59b6", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.add_field(name="Phrase to monitor", value=f"```{settings.phrase}```", inline=False)
        
        language = "Ruby" if settings.ban else "json"
        embed.add_field(name="Ban User", value=f"```{language}\n{settings.ban}```", inline=True)
        
        language = "Ruby" if settings.timeout_user else "json"
        embed.add_field(name="Timeout User", value=f"```{language}\n{settings.timeout_user}```", inline=True)
        
        language = "Ruby" if settings.delete else "json"
        embed.add_field(name="Delete Message", value=f"```{language}\n{settings.delete}```", inline=True)
        
        language = "Ruby" if settings.warn else "json"
        embed.add_field(name="Warn User", value=f"```{language}\n{settings.warn}```", inline=True)
        
        language = "Ruby" if settings.alert_staff else "json"
        embed.add_field(name="Alert staff", value=f"```{language}\n{settings.alert_staff}```", inline=True)
        
        language = "Ruby" if settings.respond else "json"
        embed.add_field(name="Respond to message", value=f"```{language}\n{settings.respond}```", inline=True)
        
        
        embed.add_field(name="Response Message", value=f"```{settings.response_message}```", inline=False)
        embed.add_field(name="Warn message", value=f"```{settings.warn_message}```", inline=False)
        embed.add_field(name="Timeout Time (minutes)", value=f"```{settings.timeout_time}```", inline=False)
        return embed
    
    
    async def create_profile_embed(self, player_ids:model.Playerids, player_profile:model.Player, player_notes:str,
                                   server_bans:dict, discord_profile:str, related_players:dict = None):

        embed = Embed(title=f"Displaying player information.",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:\nPlayer Name: {player_profile.player_name}\nSteam ID: [{player_ids.steamid}]({player_profile.profile_url})\n[RCON](https://www.battlemetrics.com/rcon/players/{player_ids.bmid})", color=int("0x3498db", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.add_field(name="Is this account limited on steam?", value=f"```{player_profile.limited}```", inline=False)
        embed.add_field(name="Hours", value=f"Total Time Played: {player_profile.playtime}\nTraining time:{player_profile.playtime_training}\nActual Servers: {player_profile.playtime - player_profile.playtime_training}", inline=True)
        
        embed.add_field(name=f"Notes", value=f"Total: {player_notes['hidden'] + player_notes['shown']}\nHiding: {player_notes['hidden']}\nVisible: {player_notes['shown']}", inline=True)
        embed.add_field(name=f"Server Bans - Total: {server_bans['hidden'] + server_bans['shown']}, Showing: {server_bans['shown']}, Hiding: {server_bans['hidden']}",value=f"{server_bans['sample']}", inline=False)
        embed.add_field(name="Rustbans, community bans and other bans", value=f"{player_profile.rustbanned_text}\n{player_profile.community_banned}\n{player_profile.vac_banned}\n{player_profile.last_ban}", inline=True)    
        embed.add_field(name="Connected Players", value=f"Total Connected Players: {len(related_players['regular_related']) + len(related_players['rustbanned_related']) + len(related_players['vac_banned_related'])}\nTotal Rust Bans: {len(related_players['rustbanned_related'])}\nTotal VAC Banned:{len(related_players['vac_banned_related'])}\nTotal not banned: {len(related_players['regular_related'])}", inline=True)
        
        embed.add_field(name="Discord Profile(s)", value=f"```{discord_profile}```", inline=False)
        return embed

    async def create_related_profile_embed(self, original_player:model.playerprofile,
                                           related_player:model.playerprofile, guild_id: str) -> Embed:
        tasks = [
            self.fun.get_player_info(player_id=related_player.battlemetrics_id),
            self.fun.get_player_notes(player_id=related_player.battlemetrics_id, guild_id=guild_id),
            self.fun.get_player_bans(player_id=related_player.battlemetrics_id, guild_id=guild_id)
        ]
        responses = await asyncio.gather(*tasks)
        player_profile, player_notes, server_bans = responses

        player_ids = await self.fun.get_player_ids(player_profile.steam_id)
        name_comparison = await self.fun.compare_names(original_player.names,player_profile.names)
        compared_names = None
        for comparison in name_comparison:
            if compared_names:
                compared_names += f"\n{comparison['original_name']} ➣ {comparison['related_name']} [{comparison['match_ratio']}%]"
            else:
                compared_names = f"{comparison['original_name']} ➣ {comparison['related_name']} [{comparison['match_ratio']}%]"
        discord_profile = await self._get_discord_profile(player_ids)

        embed = Embed(
            title="Displaying player information.",
            description=":warning: **This information is not to be shared. If you share this information with an unauthorized user, your access may be revoked.** :warning:\n"
                        f"Player Name: {player_profile.player_name}\n"
                        f"Steam ID: [{player_ids.steamid}]({player_profile.profile_url})\n"
                        f"[RCON](https://www.battlemetrics.com/rcon/players/{player_ids.bmid})",
            color=0x3498db
        )
        embed.set_footer(
            text="Created, developed and maintained by Gnomeslayer.\nLogged at: {}".format(datetime.now()),
            icon_url="https://i.imgur.com/pxonfff.png"
        )
        embed.add_field(name="Limited Account", value=f"```{player_profile.limited}```", inline=True)
        embed.add_field(name="Hours", value=f"Total Time Played: {player_profile.playtime}\nTraining time:{player_profile.playtime_training}\nActual Servers: {player_profile.playtime - player_profile.playtime_training}", inline=True)
        embed.add_field(name=f"Notes", value=f"Total: {player_notes['hidden'] + player_notes['shown']}\nHiding: {player_notes['hidden']}\nVisible: {player_notes['shown']}", inline=True)
        embed.add_field(name="Rustbans, community bans and other bans", value=f"{player_profile.rustbanned_text}\n{player_profile.community_banned}\n{player_profile.vac_banned}\n{player_profile.last_ban}", inline=False)
        embed.add_field(name=f"Server Bans - Total: {server_bans['hidden'] + server_bans['shown']}, Showing: {server_bans['shown']}, Hiding: {server_bans['hidden']}",value=f"{server_bans['sample']}", inline=False)
        embed.add_field(name="Discord Profile(s)", value=f"```{discord_profile}```", inline=False)
        embed.add_field(name="Name Comparisons (Searched Player ➣ Related Player)", value=f"```{compared_names}```", inline=False)
        embed.add_field(name="IP information", value=f"```ISP ID: {related_player.ip_info.isp_name}, IS VPN: {related_player.ip_info.is_vpn}, COUNTRY: {related_player.ip_info.country}, ISP NAME: {related_player.ip_info.isp_name}```")
        return embed

    async def create_ban_embed(self, ban:model.Serverbans) -> Embed:
        embed = Embed(title=f"Displaying player serverban information.",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x3498db", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.add_field(name="Banner",value=f"{ban.banner}",inline=True,)
        embed.add_field(name="Links",value=f"[Ban](https://www.battlemetrics.com/rcon/bans/edit/{ban.banid})\n[Server](https://www.battlemetrics.com/servers/rust/{ban.serverid})",inline=True)
        embed.add_field(name="Dates",value=f"```Issued: {ban.bandate}\nExpires: {ban.expires}```", inline=False)
        embed.add_field(name="Ban reason",value=f"```{ban.banreason}```",inline=False)
        ban_msg = ban.bannote
        if ban_msg:
            if len(ban_msg) >= 900:
                ban_msg = ban_msg[:500]
                ban_msg += "...(Truncated)"
            else:
                ban_msg = "No note"
        embed.add_field(name="Note", value=f"```{ban_msg}```", inline=False)
        return embed

    async def create_notes_embed(self, note:model.Notes) -> Embed:
        embed = Embed(title=f"Displaying player notes information.",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x3498db", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.add_field(name="Note ID",value=f"{note.noteid}",inline=True)
        embed.add_field(name="Organization info",value=f"org id: {note.orgid}\nOrg Name: {note.orgname}", inline=True,)
        embed.add_field(name="Note Maker",value=f"{note.notemakername}",inline=True,)
        note_msg = note.note
        if len(note_msg) >= 900:
            note_msg = note_msg[:900]
            note_msg += "...(Truncated)"
        embed.add_field(name="Note", value=f"```{note_msg}```", inline=False)
        return embed

    async def create_activity_embed(self, activity_logs:model.ActivityLogs) -> Embed:
        embed = Embed(title=f"Displaying player notes information.",description=f" :warning: **This information is not to be shared, if you share this information with an unauthorized user your access may be revoked.** :warning:", color=int("0x3498db", base=16))
        embed.set_footer(text=f"Created, developed and maintained by Gnomeslayer.\nLogged at: {str(datetime.now())}", icon_url="https://i.imgur.com/pxonfff.png")
        embed.add_field(name="Stats (1 day period)", value=f"Kills: {activity_logs.kills_day}\nDeaths:{activity_logs.deaths_day}", inline=True)
        embed.add_field(name="F7 Reports", value=f"{activity_logs.player_reports}", inline=True)
        embed.add_field(name="Arkan Reports", value=f"{activity_logs.arkan_reports}", inline=True)
        embed.add_field(name=f"Last Played Server - Last Played: {activity_logs.still_online}", value=f"```{activity_logs.recent_server_name}```", inline=False)
        return embed
    
    async def set_teaminfo_embed(self, teaminfo:str, player_name:str) -> Embed:
        team = teaminfo.split()
        team_links = None
        teammate_count = 0
        embed = Embed(
            title=f"Team information for {player_name}")
        for teammate in team:
            if teammate.isnumeric():
                if len(teammate) == 17:
                    await asyncio.sleep(0.1)
                    user_ids = await self.api.player.match_identifiers(identifier=teammate, identifier_type="steamID")
                    battlemetrics_id = user_ids['data'][0]['relationships']['player']['data']['id']
                    if teammate_count == 4:
                        embed.add_field(
                            name=f"Team Links", value=f"\n{team_links[:1020]}", inline=False)
                        team_links = None
                    teammate_count += 1
                    if team_links:
                        team_links += f"\n[Battlemetrics](https://www.battlemetrics.com/rcon/players/{battlemetrics_id}) - [Steam](http://steamcommunity.com/profiles/{teammate}) - {user_ids['data'][0]['attributes']['metadata']['profile']['personaname']}"
                    else:
                        team_links = f"[Battlemetrics](https://www.battlemetrics.com/rcon/players/{battlemetrics_id}) - [Steam](http://steamcommunity.com/profiles/{teammate}) - {user_ids['data'][0]['attributes']['metadata']['profile']['personaname']}"
        
        if team_links:
            embed.add_field(name=f"Team Links",
                            value=f"{team_links[:1020]}", inline=False)
        else:
            embed.add_field(name=f"Team Links",
                            value=f"Player is not in a team.", inline=False)
        embed.add_field(
            name=f"Raw Team Information", value=f"```perl\n{teaminfo}```", inline=False)
        return embed
    
    async def aimbot_embed(self, report:dict) -> Embed:
        embed = Embed(
            title=f"AIMBOT VIOLATION")
        embed.set_footer(text="Footer Text")
        embed.add_field(name="Violation Number", value=f"{report['violation_number']}", inline=True)
        embed.add_field(name="Links", value=f"[Steam](http://steamcommunity.com/profiles/{report['steam_id']}) - {report['steam_id']}\n"
                        f"{report['battlemetrics_url']}", inline=True)
        embed.add_field(name="Server Details", value=f"[Server](https://www.battlemetrics.com/rcon/servers/{report['serverid']})", inline=False)
        embed.add_field(name="Action Taken", value=f"```{report['action_taken']}```", inline=False)
        return embed
    
    async def arkan_embed(self, data:dict) -> Embed:
        embed = Embed(
            title=f"ARKAN WATCHER")
        embed.set_footer(text=f"{data['footer']}")
        embed.add_field(name="Player", value=f"{data['playername']} - {data['steamid']}\n([Steam](http://steamcommunity.com/profiles/{data['steamid']}) - [Battlemetrics]({data['bmurl']}))", inline=False)
        embed.add_field(name="NR Violation #", value = f"{data['violation_number']}", inline=True)
        embed.add_field(name="Probability", value = f"{data['probability']}%", inline=True)
        embed.add_field(name="Shot Count", value=f"{data['shotcount']}", inline=True)
        embed.add_field(name="Weapon", value=f"{data['weapon']}", inline=True)
        embed.add_field(name="Ammo", value=f"{data['ammo']}", inline=True)
        embed.add_field(name=f"Attachments Count: {data['attachments_count']}", value=f"{data['attachments']}", inline=True)
        embed.add_field(name="Projectiles", value=f"{data['projectiles']}", inline=True)
        embed.add_field(name="Zero Count", value=f"{data['zero_count']}", inline=False)
        embed.add_field(name="Action Taken", value=f"{data['action_taken']}", inline=False)
        
        return embed