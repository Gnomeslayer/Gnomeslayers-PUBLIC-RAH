# Third-party imports
import asyncio
import aiohttp
import json
import validators
from fuzzywuzzy import fuzz
import random

# Standard library imports
from datetime import datetime, timezone, timedelta

from battlemetrics import Battlemetrics
import supportfiles.database as mydatabase
import supportfiles.model as model

class MainFunctions():
    def __init__(self, config:dict):
        self.config = config
        self.wrapper = Battlemetrics(config['tokens']['battlemetrics_token'])

    async def _time_to_epoch(self, time:str) -> int:
        if not time[-1].lower() == "z":
            time = time.replace(" ", "T")
            time = time + "Z"
        timestamp_obj = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
        epoch_time = int(timestamp_obj.timestamp())
        return epoch_time
    
    def _remove_links(self, text:str):
            text = text.replace("}", "")
            text = text.replace("{", "")
            text = text.replace("]", "")
            text = text.replace("[", "")
            text = text.replace("|", "")
            text = text.replace("discord.gg", "discordlink")
            text = text.replace("https://", "")
            text = text.replace("http://", "")
            return text

    async def server_info(self, server_id:int) -> model.Server:
    
        serverinfo = await self.wrapper.server.info(server_id=server_id)
        if serverinfo['data']:
            server_name = serverinfo["data"]["attributes"]["name"]
            players = serverinfo["data"]["attributes"]["players"]
            maxplayers = serverinfo["data"]["attributes"]["maxPlayers"]
            
            player_ids = []
            for included in serverinfo['included']:
                if included['type'] == "identifier":
                    if included["attributes"]["type"] == "steamID":
                        player_ids.append(included["attributes"]["identifier"])
                        
            return model.Server(server_id=server_id,server_name=server_name,player_count=players,max_players=maxplayers, player_ids=player_ids)
        else:
            return model.Server()
        
        
    async def get_player_info(self, player_id:str) -> model.Player:
        player = await self.wrapper.player.info(identifier=player_id)
        if not player:
            return model.Player
        if not player.get('data'):
            with open(f"{player_id}_failed.json", "w") as f:
                f.write(json.dumps(player, indent=4))
            print(f"Failed to get data on player: {player_id}, check file: {player_id}_failed.json")
            return model.Player
        player = await self.sort_player(player)
        await asyncio.sleep(0.1)  # Slight sleep so we don't get rate limited.
        return player

    async def get_activity_logs(self, player_id:str) -> model.ActivityLogs:
        session = await self.wrapper.player.session_history(player_id=player_id)
        activity_logs = model.ActivityLogs()
        if session:
            session = await self.sort_session_history(session)
            activity_logs.recent_server_id = session['recent_server_id']
            activity_logs.recent_server_name = session['recent_server_name']
            activity_logs.still_online = session['still_online']
        await asyncio.sleep(0.1)
        kill_data = await self.player_stats(bmid=player_id)
        await asyncio.sleep(0.1)
        player_report_count = await self.get_player_reports(player_id=player_id)
        await asyncio.sleep(0.1)
        arkan_report_count = await self.get_arkans(player_id=player_id)
        activity_logs.arkan_reports = arkan_report_count
        activity_logs.player_reports = player_report_count
        activity_logs.kills_day = kill_data['kills_day']
        activity_logs.deaths_day = kill_data['deaths_day']
        return activity_logs
    
    async def team_info(self, server_id:str, steam_id:str) -> dict:
        return await self.wrapper.server.console_command(server_id=server_id, command=f"teaminfo {steam_id}")

    async def combatlog(self, server_id:str, steam_id:str) -> dict:
        return await self.wrapper.server.console_command(server_id=server_id, command=f"combatlog {steam_id}")

    async def activity_logs_search(self, search:str) -> dict:
        return await self.wrapper.activity_logs(filter_search=search)

    async def get_player_reports(self, player_id:str) -> dict:
        playerreports = await self.wrapper.activity_logs(filter_bmid=player_id, whitelist="rustLog:playerReport")
        if playerreports:
            return len(playerreports['data'])
        else:
            return 0

    async def get_arkans(self, player_id:str):
        arkanreports = await self.wrapper.activity_logs(filter_bmid=player_id, whitelist="unknown", filter_search="arkan")
        if arkanreports:
            return len(arkanreports['data'])
        else:
            return 0

    async def sort_session_history(self, session:dict) -> dict:
        recent_server_name = "No data."
        recent_server_id = 0
        still_online = "No"
        if session:
            if session.get('data'):
                if session['data']:
                    if not session['data'][0]['attributes']['stop']:
                        still_online = "Still online"
                    else:
                        formattedTime = await self._time_to_epoch(session['data'][0]['attributes']['stop'])
                        still_online = f"<t:{formattedTime}:R>"
                    recent_server_id = session['data'][0]['relationships']['server']['data']['id']
                    recent_server_name = "Unable to find server name. Goodluck!"
                    for included in session['included']:
                        if included['type'] == 'server':
                            if str(included['id']) == str(recent_server_id):
                                recent_server_name = included['attributes']['name']
                                break
        session = {
            "recent_server_name": recent_server_name,
            "recent_server_id": recent_server_id,
            "still_online": still_online
        }
        return session

    async def get_player_notes(self, player_id:str, guild_id:str) -> dict:
        player_notes = await self.wrapper.notes.list(player_id=player_id)
        if player_notes['data']:
            player_notes = await self.sort_notes(player_notes, guild_id)
        else:
            player_notes = {
                'hidden': 0,
                'shown': 0,
                'note_data': []
            }
        await asyncio.sleep(0.1)  # Slight sleep so we don't get rate limited.
        return player_notes

    async def get_player_bans(self, player_id:str, guild_id:str) -> dict:
        player_server_bans = await self.wrapper.bans.search(player_id=player_id)
        if player_server_bans['meta']['total']:
            if player_server_bans.get('meta'):
                if player_server_bans['meta']['total']:
                    player_server_bans = await self.sort_server_bans(player_server_bans, guild_id)
            else:
                player_server_bans = {
                                'hidden': 0,
                                'shown': 0,
                                'sample': None,
                                'ban_info': []
                            }
        else:
            player_server_bans = {
                                'hidden': 0,
                                'shown': 0,
                                'sample': None,
                                'ban_info': []
                            }
        await asyncio.sleep(0.1)  # Slight sleep so we don't get rate limited.
        return player_server_bans


    async def get_related_players(self, battlemetrics_id: int) -> list:

        related_players = await self.wrapper.player.identifiers(player_id=battlemetrics_id)
        if related_players:
            related_players = await self.sort_related(related_players)
        if not related_players:
            related_players = {
                'vac_banned_related': [],
                'regular_related': [],
                'rustbanned_related': []
        }
        return related_players


    async def sort_related(self, related_players: dict) -> list:

        players = {
            'vac_banned_related': [],
            'regular_related': [],
            'rustbanned_related': []
        }
        ips = []
        idlist = []
        for data in related_players['data']:
            if data['attributes']['type'] == "ip":
                vpn = False
                if not data['attributes'].get('identifier'):
                    random_number = random.randint(1,10000)
                    with open(f'related_players_{random_number}.json', 'w') as f:
                        f.write(json.dumps(related_players, indent=4))
                        print(f"Check file: related_players_{random_number}.json")
                        return
                ip = data['attributes']['identifier']
                if data['attributes']['metadata'].get('connectionInfo'):
                    asn = data['attributes']['metadata']['connectionInfo']['asn']
                    country = data['attributes']['metadata']['country']
                    isp_name = data['attributes']['metadata']['connectionInfo']['isp']
                    if data['attributes']['metadata']['connectionInfo'].get('tor'):
                        if data['attributes']['metadata']['connectionInfo']['tor']:
                            vpn = True

                    if data['attributes']['metadata']['connectionInfo'].get('datacenter'):
                        if data['attributes']['metadata']['connectionInfo']['datacenter']:
                            vpn = True
                    if data['attributes']['metadata']['connectionInfo'].get('proxy'):
                        if data['attributes']['metadata']['connectionInfo']['proxy']:
                            vpn = True
                if not vpn:
                    vpn_db = await mydatabase.get_ip_info(ip=ip)
                    if vpn_db:
                        vpn = vpn_db['is_vpn']
                    else:
                        vpn = await self.check_if_ip_vpn(ip=ip)
                if vpn:
                    continue
                ip_info = model.Isps(ip=ip,
                            isp_id=asn,
                            is_vpn=vpn,
                            country=country,
                            isp_name=isp_name)
                await mydatabase.add_ip(ip=ip, isp_id=asn, is_vpn=vpn, country=country, isp_name=isp_name)
                ips.append(ip_info)
                for related in data['relationships']['relatedPlayers']['data']:

                    for included in related_players['included']:
                        name = "Unknown"
                        player_id = related['id']

                        if included['type'] == "identifier":
                            if included['relationships']['player']['data']['id'] == player_id:

                                if included['attributes'].get('metadata'):
                                    if player_id in idlist:
                                        continue
                                    else:
                                        idlist.append(player_id)
                                    steamid = 0
                                    if included['attributes']['metadata'].get('profile'):
                                        name = included['attributes']['metadata']['profile']['personaname']
                                        steamid = included['attributes']['metadata']['profile']['steamid']
                                    vacban_count = 0
                                    vac_banned = False
                                    

                                    community_banned = False
                                    game_ban_count = 0
                                    last_ban = 0
                                    rustbanned = False
                                    rustbancount = 0
                                    rustban_days = 0
                                    
                                    if included['attributes']['metadata'].get('bans'):
                                        vacban_count = included['attributes']['metadata']['bans']['NumberOfVACBans']
                                        vac_banned = included['attributes']['metadata']['bans']['VACBanned']
                                        last_ban = included['attributes']['metadata']['bans']['DaysSinceLastBan']
                                        community_banned = included['attributes']['metadata']['bans']['CommunityBanned']
                                        game_ban_count = included['attributes']['metadata']['bans']['NumberOfGameBans']

                                    if included['attributes']['metadata'].get('rustBans'):
                                        rustbanned = included['attributes']['metadata']['rustBans']['banned']
                                        rustbancount = included['attributes']['metadata']['rustBans']['count']
                                        given_time = datetime.strptime(
                                            f"{included['attributes']['metadata']['rustBans']['lastBan']}", "%Y-%m-%dT%H:%M:%S.%fZ")
                                        current_time = datetime.utcnow()
                                        rustban_days = (current_time - given_time)
                                        
                                    if rustbanned:
                                        rustbanned_text = f"Rustbans: {rustbancount} | {rustban_days} day(s) ago"
                                    else:
                                        rustbanned_text = "Rustbans: Not rustbanned."
                                    player = {
                                        "battlemetrics_id": player_id,
                                        "steam_id": steamid,
                                        "player_name": name,
                                        "community_banned": community_banned,
                                        "game_ban_count": game_ban_count,
                                        "rustbanned_bool": rustbanned,
                                        "rustbanned_text": rustbanned_text,
                                        "rustbancount": rustbancount,
                                        "banned_days_ago": rustban_days,
                                        "ip_info": ip_info,
                                        "vac_banned": vac_banned,
                                        "vacban_count": vacban_count,
                                        "last_ban": last_ban
                                    }
                                    player = model.Player(**player)

                                    if vac_banned:
                                        players['vac_banned_related'].append(player)
                                    elif rustbanned:
                                        players['rustbanned_related'].append(player)
                                    else:
                                        players['regular_related'].append(player)

        return players


    async def sort_server_bans(self, player_server_bans: dict, guildid:int) -> list:
        guild_info = await self.get_guild(guildid=guildid)
        server_bans = {
            'hidden': 0,
            'shown': 0,
            'sample': None,
            'ban_info': []
        }
        
    
        for data in player_server_bans['data']:
            server_ban = model.Serverbans()
            server_ban.bandate = data['attributes']['timestamp']
            server_ban.banid = data['id']
            server_ban.bannote = data['attributes']['note']
            server_ban.banreason = self._remove_links(data['attributes']['reason'])
            server_ban.bmid = data['relationships']['player']['data']['id']
            if data['relationships'].get('server'):
                server_ban.serverid = data['relationships']['server']['data']['id']
            else:
                server_ban.serverid = 0

            server_ban.orgid = data['relationships']['organization']['data']['id']
            server_ban.uuid = data['attributes']['uid']
            if data['attributes']['expires']:
                server_ban.expires = data['attributes']['expires']
            else:
                server_ban.expires = "Never"
            banner_id = 0
            if data['relationships'].get('user'):
                banner_id = data['relationships']['user']['data']['id']
            else:
                server_ban.banner = "Server Ban"
            for identifier in data['attributes']['identifiers']:
                if identifier['type'] == "steamID":
                    if identifier.get('metadata'):
                        server_ban.steamid = identifier['metadata']['profile']['steamid']
                    else:
                        if identifier.get('identifier'):
                            server_ban.steamid = identifier['identifier']
                        else:
                            server_ban.steamid = 0
                            random_number = random.randint(1,10000)
                            with open(f"failed_identifier_{random_number}.json", "w") as f:
                                f.write(json.dumps(player_server_bans, indent=4))
                            print(f"\n----\nFailed to get identifier?\nGuild ID: {guildid}\nFile: failed_identifier_{random_number}.json \n The specific part: {identifier}\n-----\n")

            for included in player_server_bans['included']:
                if included['type'] == "server":
                    if included['id'] == server_ban.serverid:
                        server_ban.servername = included['attributes']['name']
                if included['type'] == "user":
                    if included['id'] == banner_id:
                        server_ban.banner = included['attributes']['nickname']
            
            if guild_info:
                if str(guild_info.organization_id) == str(server_ban.orgid):
                    if server_bans['shown'] < 5:
                        if server_bans['sample']:
                            server_bans['sample'] += f"\n➣ [{server_ban.banreason}](https://www.battlemetrics.com/rcon/bans/edit/{server_ban.banid})"
                        else:
                            server_bans['sample'] = f"➣ [{server_ban.banreason}](https://www.battlemetrics.com/rcon/bans/edit/{server_ban.banid})"
                    server_bans['shown'] += 1
                    server_bans['ban_info'].append(server_ban)
                    continue
                if not guild_info.sharing_data:
                    server_bans['hidden'] += 1
                    continue
            organization = await self.get_guild_by_orgid(orgid=str(data['relationships']['organization']['data']['id']))
            if organization:
                if organization.sharing_data:
                    if server_bans['shown'] < 5:
                        if server_bans['sample']:
                            server_bans['sample'] += f"\n➣ [{server_ban.banreason}](https://www.battlemetrics.com/rcon/bans/edit/{server_ban.banid})"
                        else:
                            server_bans['sample'] = f"➣ [{server_ban.banreason}](https://www.battlemetrics.com/rcon/bans/edit/{server_ban.banid})"
                    server_bans['shown'] += 1
                    server_bans['ban_info'].append(server_ban)
                else:
                    server_bans['hidden'] += 1
            else:
                if server_bans['shown'] < 5:
                    if server_bans['sample']:
                        server_bans['sample'] += f"\n➣ [{server_ban.banreason}](https://www.battlemetrics.com/rcon/bans/edit/{server_ban.banid})"
                    else:
                        server_bans['sample'] = f"➣ [{server_ban.banreason}](https://www.battlemetrics.com/rcon/bans/edit/{server_ban.banid})"
                    server_bans['shown'] += 1
                    server_bans['ban_info'].append(server_ban)
        return server_bans


    async def sort_notes(self, player_notes: dict, guild_id:int) -> list:
        guild_info = await self.get_guild(guildid=guild_id)
        notes = {
            'hidden': 0,
            'shown': 0,
            'note_data': []
        }
        for data in player_notes['data']:
            if data['relationships'].get('user'):
                note = model.Notes(
                    noteid=data['id'],
                    bmid=data['relationships']['player']['data']['id'],
                    orgid=data['relationships']['organization']['data']['id'],
                    notemakerid=data['relationships']['user']['data']['id'],
                    note=data['attributes']['note'],
                    notemakername="Unknown"
                )
            else:
                note = model.Notes(
                    noteid=data['id'],
                    bmid=data['relationships']['player']['data']['id'],
                    orgid=data['relationships']['organization']['data']['id'],
                    notemakerid=data['relationships']['organization']['data']['id'],
                    note=data['attributes']['note'],
                    notemakername="Unknown"
                )
            for included in player_notes['included']:
                if included['type'] == "user":
                    if included['id'] == note.notemakerid:

                        note.notemakername = included['attributes']['nickname']
                if included['type'] == "organization":
                    if included['id'] == note.orgid:
                        note.orgname = included['attributes']['name']
            if guild_info:
                if str(guild_info.organization_id) == str(note.orgid):
                    notes['note_data'].append(note)
                    notes['shown'] += 1
                    continue
                if not guild_info.sharing_data:
                    notes['hidden'] += 1
                    continue
            organization = await self.get_guild_by_orgid(orgid=str(note.orgid))
            if organization:
                if organization.sharing_data:
                    notes['note_data'].append(note)
                    notes['shown'] += 1
                else:
                    notes['hidden'] += 1
            else:
                notes['note_data'].append(note)
                notes['shown'] += 1
                        
        return notes

    async def sort_player(self, player: dict) -> model.Player:

        player_data = {}
        player_data['battlemetrics_id'] = player['data']['id']
        player_data['player_name'] = player['data']['attributes']['name']
        player_data['playtime'] = 0
        player_data['playtime_training'] = 0
        player_data['names'] = []

        vacban_count = 0
        vac_banned = False
        last_ban = 0
        community_banned = False
        game_ban_count = 0
        
        rustbanned = False
        rustbancount = 0
        banned_days_ago = 0

        for included in player['included']:
            if included['type'] == "identifier":
                if included['attributes']['type'] == "steamID":
                    player_data['steam_id'] = included['attributes']['identifier']
                    if included['attributes'].get('metadata'):
                        if included['attributes']['metadata'].get('profile'):
                            vac_banned = included['attributes']['metadata']['bans']['VACBanned']
                            vacban_count = included['attributes']['metadata']['bans']['NumberOfVACBans']
                            community_banned = included['attributes']['metadata']['bans']['CommunityBanned']
                            game_ban_count = included['attributes']['metadata']['bans']['NumberOfGameBans']
                            last_ban = included['attributes']['metadata']['bans']['DaysSinceLastBan']
                            player_data['avatar_url'] = included['attributes']['metadata']['profile']['avatarfull']
                            # player_data['account_created'] = included['attributes']['metadata']['profile']['timecreated']
                            player_data['limited'] = False
                            if included['attributes']['metadata']['profile'].get('isLimitedAccount'):
                                player_data['limited'] = included['attributes']['metadata']['profile']['isLimitedAccount']
                            player_data['profile_url'] = included['attributes']['metadata']['profile']['profileurl']
                        if included['attributes']['metadata'].get('rustBans'):
                            rustbanned = included['attributes']['metadata']['rustBans']['banned']
                            rustbancount = included['attributes']['metadata']['rustBans']['count']
                            given_time = datetime.strptime(
                                f"{included['attributes']['metadata']['rustBans']['lastBan']}", "%Y-%m-%dT%H:%M:%S.%fZ")
                            current_time = datetime.utcnow()
                            banned_days_ago = (current_time - given_time).days

                if included['attributes']['type'] == "name":
                    player_data['names'].append(
                        included['attributes']['identifier'])

            if included['type'] == "server":
                training_names = ["rtg", "aim", "ukn", "arena",
                                "combattag", "training", "aimtrain", "train", "arcade", "bedwar", "bekermelk", "escape from rust"]
                for name in training_names:
                    if name in included['attributes']['name']:
                        player_data['playtime_training'] += included['meta']['timePlayed']
                player_data['playtime'] += included['meta']['timePlayed']
        
        if vac_banned:
            vac_banned = f"VAC Bans: {vacban_count}"
        else:
            vac_banned = "VAC Bans: No VAC Bans"   
        
        if community_banned:
            community_banned = f"Community Bans: {game_ban_count}"
        else:
            community_banned = "Community Bans: No community bans"
            
        if rustbanned:
            rustbanned_text = f"Rustbans: {rustbancount} | {banned_days_ago} day(s) ago"
        else:
            rustbanned_text = "Rustbans: Not rustbanned."
        
        last_ban = f"Days since last non rust ban: {last_ban}"
            
        player_data['playtime'] = player_data['playtime'] / 3600
        player_data['playtime'] = round(player_data['playtime'], 2)
        player_data['playtime_training'] = player_data['playtime_training'] / 3600
        player_data['playtime_training'] = round(
            player_data['playtime_training'], 2)
        player_data['last_ban'] = last_ban
        player_data['community_banned'] = community_banned
        player_data['game_ban_count'] = game_ban_count
        player_data['vac_banned'] = vac_banned
        player_data['vacban_count'] = vacban_count
        player_data['rustbanned_text'] = rustbanned_text
        player_data['rustbanned_bool'] = rustbanned
        player_data['rustbancount'] = rustbancount
        player_data['banned_days_ago'] = banned_days_ago    
        
        myplayer = model.Player(**player_data)
        return myplayer


    async def check_cheetos(self, discord_id) -> dict:

        """"Check cs api & return list of guilds"""
        headers = {"Auth-Key": self.config['tokens']['cheetos_api_key'],
                "DiscordID": f"{self.config['additional']['DiscordIDForCheetos']}"}
        url = f"https://Cheetos.gg/api.php?action=search&id={discord_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    resp_dict = json.loads(await resp.text())
                    if "no users found" in str(resp_dict).lower() or "null" in str(resp_dict).lower():
                        return None
                    else:
                        return resp_dict


    async def check_if_ip_vpn(self, ip: str) -> dict:

        url = f"https://vpnapi.io/api/{ip}?key={self.config['tokens']['vpn_token']}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as r:
                response = await r.json()
        if not response or not response.get('security'):
            with open('error_logs.txt', 'a') as file:
                file.write(f"VPN Checker had an issue... The IP: {ip}\nThe response: {response}")
            return False
        if response["security"]["vpn"] or response["security"]["proxy"] or response["security"]["tor"] or response["security"]["relay"]:
            return True
        else:
            return False


    async def get_profiles(self, user_id: str, guildid: str) -> model.Profiles:
        results = {}
        # Search for registered user in our database.
        signed_tos = await mydatabase.get_user_tos(user_id=str(user_id))
        if signed_tos:
            results['signed_tos'] = signed_tos['signed_tos']
        else:
            results['signed_tos'] = False
        
        
        user_profile = await mydatabase.get_user_profile_by_guild(user_id=user_id, guild_id=guildid)
        blacklisted_user = await mydatabase.get_blacklisted_user(user_id=user_id)
        server_profile = await mydatabase.get_guild_profile_by_guildid(guildid=str(guildid))
        manager = await mydatabase.get_server_manager(user_id=user_id, guildid=str(guildid))

        if user_profile:
            results['user_profile'] = model.UserProfile(**user_profile)
        else:
            await mydatabase.add_or_update_approve(user_id=user_id, guildid=guildid, approved=False)
            user_profile = await mydatabase.get_user_profile_by_guild(user_id=user_id, guild_id=guildid)
            try:
                results['user_profile'] = model.UserProfile(**user_profile)
            except Exception as e:
                results['user_profile'] = model.UserProfile()
                with open('error_logs.txt', 'a') as file:
                                file.write(f"Error occured on command {e}\nSomething went wrong with profile generation...\nUser ID: {user_id}\nGuild ID: {guildid}")
                

        if blacklisted_user:
            results['blacklisted'] = blacklisted_user
        else:
            results['blacklisted'] = None

        if server_profile:
            results['server_profile'] = model.ServerProfile(**server_profile)
        else:
            await mydatabase.add_guild(guildid=guildid)
            try:
                server_profile = await mydatabase.get_guild_profile_by_guildid(guildid=str(guildid))
                results['server_profile'] = model.ServerProfile(**server_profile)
            except Exception as e:
                with open('error_logs.txt', 'a') as file:
                    file.write(f"Error occured on command {e}\nUnable to make a new server profile for guildid: {guildid}")
                results['server_profile'] = model.ServerProfile(server_id=guildid)

        if manager:
            results['managers'] = manager
        return results


    async def get_id_from_steam(self, url: str) -> int:

        """Takes the URL (well part of it) and returns a steam ID"""
        url = (
            f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?format=json&"
            f"key={self.config['tokens']['steam_token']}&vanityurl={url}&url_type=1"
        )
        async with aiohttp.ClientSession(
            headers={"Authorization": self.config['tokens']['steam_token']}
        ) as session:
            async with session.get(url=url) as r:
                response = await r.json()
        if response['response'].get('steamid'):
            return response["response"]["steamid"] if response["response"]["steamid"] else 0
        else:
            return 0


    async def get_player_ids(self, submittedtext: str) -> model.Playerids:
        bmid = 0
        steamid = 0    
        user_ids = await mydatabase.get_player_ids_by_steamid(steamid=str(submittedtext))
        
        player_ids = None
        steamurl = None
        if user_ids:
            link_check = await self.retrieve_discord_links(steam_id=user_ids[0]['steamid'])
            id_list = {
                'steamid': user_ids[0]['steamid'],
                'bmid': user_ids[0]['bmid'],
                'steamurl': user_ids[0]['steamurl'],
                'confidence': None,
                'discordid': []
            }
            for ids in user_ids:
                if not id_list['steamid']:
                    id_list['steamid'] = ids['steamid']
                if not id_list['bmid']:
                    id_list['bmid'] = ids['bmid']
                if not id_list['steamurl']:
                    id_list['steamurl'] = ids['steamurl']
                if ids['discordid'] == "None" or not ids['discordid']:
                    ids['discordid'] = None
                if ids['discordid']:
                    if str(ids['discordid']) in link_check:
                        ids['confidence'] = 100
                        await mydatabase.save_or_update_ids(steamid=ids['steamid'],bmid=ids['bmid'],steamurl=ids['steamurl'],confidence=100,discordid=ids['discordid'])
                        link_check.remove(ids['discordid'])
                    discord = {
                        'discordid': ids['discordid'],
                        'confidence': ids['confidence']
                        }
                    id_list['discordid'].append(discord)
            if link_check:
                for link in link_check:
                    discord = {
                        'discordid': link,
                        'confidence': 100
                    }
                    id_list['discordid'].append(discord)
                    await mydatabase.save_or_update_ids(steamid=ids['steamid'],bmid=ids['bmid'],steamurl=ids['steamurl'],confidence=100,discordid=link)
            player_ids = model.Playerids(**id_list)
            return player_ids
        else:
            if validators.url(submittedtext):
                mysplit = submittedtext.split("/")
                profile = mysplit[4]
                if mysplit[3] == "id":
                    steamid = await self.get_id_from_steam(profile)
                    steamurl = submittedtext
                if mysplit[3] == "profiles":
                    steamid = profile
                    steamurl = submittedtext
                if mysplit[3] == "rcon":
                    bmid = mysplit[5]
                if mysplit[3] == "players":
                    bmid = mysplit[4]
            else:
                if len(submittedtext) != 17:
                    return None
                steamid = submittedtext
            
            
        if not steamid and not user_ids and not bmid:
            return
        if bmid:
            player_ids = model.Playerids(bmid=bmid)
            return player_ids
        
        identifiers = await self.wrapper.player.match_identifiers(identifier=int(steamid),identifier_type="steamID")
        if not identifiers['data']:
            return
        bmid = identifiers['data'][0]['relationships']['player']['data']['id']
        link_check = await self.retrieve_discord_links(steam_id=steamid)
        if link_check:
            id_list = {
                'bmid': bmid,
                'confidence': 0,
                'steamid': steamid,
                'steamurl': steamurl,
                'discordid': []
            }
            for discordid in link_check:
                id_list['discordid'].append({'discordid': discordid, 'confidence': 100})
                await mydatabase.save_or_update_ids(steamid=steamid,bmid=bmid,steamurl=steamurl,confidence=100,discordid=discordid)
        else:
            id_list = {
                'bmid': bmid,
                'confidence': 0,
                'steamid': steamid,
                'steamurl': steamurl,
                'discordid': []
            }
            await mydatabase.save_or_update_ids(steamid=steamid,bmid=bmid,steamurl=steamurl,confidence=0)
        
        player_ids = model.Playerids(**id_list)
        return player_ids


    async def compare_names(self, original_names: list, related_names: list):

        name_ratios = []

        for original_name in original_names:
            for related_name in related_names:
                match_ratio = fuzz.ratio(original_name, related_name)
                name_ratios.append(
                    {"match_ratio": match_ratio, "original_name": original_name,
                        "related_name": related_name}
                )
        sorted_name_matches = sorted(
            name_ratios, key=lambda k: k["match_ratio"], reverse=True
        )
        return sorted_name_matches[:5]


    async def kda_two_weeks(self, bmid: int) -> dict:
        weekago = datetime.now(
            timezone.utc) - timedelta(hours=168)
        weekago = str(weekago).replace("+00:00", "Z:")
        weekago = weekago.replace(" ", "T")
        url = "https://api.battlemetrics.com/activity"
        params = {
            "version": "^0.1.0",
            "tagTypeMode": "and",
            "filter[timestamp]": str(weekago),
            "filter[types][whitelist]": "rustLog:playerDeath:PVP",
            "filter[players]": f"{bmid}",
            "include": "organization,user",
            "page[size]": "100"
        }
        return await self.wrapper.helpers._make_request(method="GET", url=url, params=params)

    async def kda_day(self, bmid: int) -> dict:
        weekago = datetime.now(
            timezone.utc) - timedelta(hours=24)
        weekago = str(weekago).replace("+00:00", "Z:")
        weekago = weekago.replace(" ", "T")
        url = "https://api.battlemetrics.com/activity"
        params = {
            "version": "^0.1.0",
            "tagTypeMode": "and",
            "filter[timestamp]": str(weekago),
            "filter[types][whitelist]": "rustLog:playerDeath:PVP",
            "filter[players]": f"{bmid}",
            "include": "organization,user",
            "page[size]": "100"
        }
        return await self.wrapper.helpers._make_request(method="GET", url=url, params=params)
        
    async def player_stats(self, bmid: int) -> model.Playerstats:
        kda_results = await self.kda_day(bmid)
        stats = {
            'kills_day': 0,
            'deaths_day': 0
        }
        if kda_results:
            if kda_results.get('data'):
                for stat in kda_results['data']:
                    mytimestamp = stat['attributes']['timestamp'][:10]
                    mytimestamp = datetime.strptime(mytimestamp, '%Y-%m-%d')
                    days_ago = (datetime.now() - mytimestamp).days
                    if stat['attributes']['data'].get('killer_id'):
                        if stat['attributes']['data']['killer_id'] == int(bmid):
                            if days_ago <= 1:
                                stats['kills_day'] += 1
                        else:
                            if days_ago <= 1:
                                stats['deaths_day'] += 1
        if kda_results:
            if kda_results.get('links'):
                while kda_results["links"].get("next"):
                    await asyncio.sleep(0.1)
                    myextension = kda_results["links"]["next"]
                    kda_results = await self.wrapper.helpers._make_request(method="GET", url=myextension)
                    if kda_results:
                        for stat in kda_results['data']:
                            mytimestamp = stat['attributes']['timestamp'][:10]
                            mytimestamp = datetime.strptime(
                                mytimestamp, '%Y-%m-%d')
                            days_ago = (datetime.now() - mytimestamp).days
                            if stat['attributes']['data'].get('killer_id'):
                                if stat['attributes']['data']['killer_id'] == int(bmid):
                                    if days_ago <= 1:
                                        stats['kills_day'] += 1
                                    else:
                                        if days_ago <= 1:
                                            stats['deaths_day'] += 1
        return stats


    async def register_guild(self, guildid: str):
        await mydatabase.add_guild(guildid=guildid)


    async def authorize_server(self, guildid: str, whitelisted: bool = False):
        await mydatabase.authorize_server(guildid=guildid, whitelisted=whitelisted)


    async def add_blacklisted_user(self, user_id: str):
        await mydatabase.blacklisted_user(user_id=user_id)


    async def remove_blacklisted_user(self, user_id: str):
        await mydatabase.blacklisted_user(user_id=user_id)


    async def signed_tos(self, user_id: str, signed_tos: bool):
        await mydatabase.add_or_update_tos(user_id=user_id, signed=signed_tos)


    async def approve_user(self, user_id: str, guildid: str, approved: bool):
        await mydatabase.add_or_update_approve(user_id=str(user_id), guildid=guildid, approved=approved)


    async def search_user(self, userid: str, guildid: str = None):
        if guildid:
            user_db = await mydatabase.get_user_profile_by_guild(user_id=userid, guild_id=guildid)
            return user_db
        else:
            user_db = await mydatabase.get_user_profile(user_id=userid)
            userinfo = []
            if user_db:

                for user in user_db:
                    userinfo.append({
                        'user_id': user['user_id'],
                        'server_id': user['server_id'],
                        'approved': user['approved']

                    })
            return userinfo


    async def get_user_by_guild(self, user_id: str, guild_id: int):
        user_db = await mydatabase.get_user_profile_by_guild({"user_id": user_id, "guild_id": guild_id})
        user = None
        if user_db:
            user = model.UserProfile(**user_db)
        return user


    async def get_blacklisted_user(self, user_id: str):
        user_db = await mydatabase.blacklisted_user(user_id=user_id)
        user = None
        return user


    async def get_guild(self, guildid: str):
        guild_db = await mydatabase.get_guild_profile_by_guildid(guildid=guildid)
        guild = None
        if guild_db:
            guild = model.ServerProfile(**guild_db)
        return guild


    async def get_all_users(self):
        users_db = await mydatabase.all_users()
        user_list = []
        if users_db:
            for u in users_db:
                user_list.append(model.UserProfile(**u))
        return user_list


    async def get_all_users_by_guild(self, guildid: str):
        users_db = await mydatabase.all_users_by_guild(guildid=guildid)
        user_list = []
        if users_db:
            for u in users_db:
                user_list.append(model.UserProfile(**u))
        return user_list


    async def get_all_guilds(self) -> list:
        guilds_db = await mydatabase.all_guilds()
        guilds_list = []
        if guilds_db:
            for u in guilds_db:
                guilds_list.append(model.ServerProfile(**u))
        return guilds_list

    async def get_guild_by_orgid(self, orgid:str) -> model.ServerProfile:
        guilds_db = await mydatabase.get_guild_profile_by_orgid(organization_id=str(orgid))
        if guilds_db:
            guilds_db = model.ServerProfile(**guilds_db)
        return guilds_db

    async def send_joinleave(self, content: str):
        log_channel = self.config['logs']['joinleave']
        embed = {
            "username": f"RAH Command Logger",
            "embeds": [
                {
                    "title": f"Application console log",
                    "fields": [
                        {
                            "name": "Logged Information for review",
                            "value": f"{content}",
                            "inline": False
                        },
                    ],
                    "footer": {
                        "text": f"Rah Command Logger"
                    }
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(log_channel, json=embed)
            except Exception as e:
                with open('error_logs.txt', 'a') as file:
                    file.write(f"Error occured on command {e}")
            await session.close()


    async def send_approve(self, content: str):
        log_channel = self.config['logs']['approve']
        embed = {
            "username": f"RAH Command Logger",
            "embeds": [
                {
                    "title": f"Application console log",
                    "fields": [
                        {
                            "name": "Logged Information for review",
                            "value": f"{content}",
                            "inline": False
                        },
                    ],
                    "footer": {
                        "text": f"Rah Command Logger"
                    }
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(log_channel, json=embed)
            except Exception as e:
                with open('error_logs.txt', 'a') as file:
                    file.write(f"Error occured on command {e}")
            await session.close()


    async def send_report(self, content: str):
        report_channel = self.config['logs']['report_channel']
        embed = {
            "username": f"RAH Command Logger",
            "embeds": [
                {
                    "title": f"Application console log",
                    "fields": [
                        {
                            "name": "Logged Information for review",
                            "value": f"{content}",
                            "inline": False
                        },
                    ],
                    "footer": {
                        "text": f"Rah Command Logger"
                    }
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(report_channel, json=embed)
            except Exception as e:
                print(e)
            await session.close()


    async def send_link_report(self, content: str):
        report_channel = self.config['logs']['link_channel']
        embed = {
            "username": f"RAH Command Logger",
            "embeds": [
                {
                    "title": f"Linkey Linkey",
                    "fields": [
                        {
                            "name": "Logged Information for review",
                            "value": f"{content}",
                            "inline": False
                        },
                    ],
                    "footer": {
                        "text": f"Rah Command Logger"
                    }
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(report_channel, json=embed)
            except Exception as e:
                print(e)
            await session.close()


    async def send_users_report(self, content: str):
        report_channel = self.config['logs']['users_report_channel']
        embed = {
            "username": f"Help",
            "embeds": [
                {
                    "title": f"RAH users who cannot use the bot properly.",
                    "fields": [
                        {
                            "name": "USERS!!",
                            "value": f"{content}",
                            "inline": False
                        },
                    ],
                    "footer": {
                        "text": f"Rah users sent every hour on the hour."
                    }
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(report_channel, json=embed)
            except Exception as e:
                print(e)
            await session.close()


    async def send_signedtos(self, content: str):
        log_channel = self.config['logs']['signedtos']
        embed = {
            "username": f"RAH Command Logger",
            "embeds": [
                {
                    "title": f"Application console log",
                    "fields": [
                        {
                            "name": "Logged Information for review",
                            "value": f"{content}",
                            "inline": False
                        },
                    ],
                    "footer": {
                        "text": f"Rah Command Logger"
                    }
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(log_channel, json=embed)
            except Exception as e:
                print(e)
            await session.close()

    # Searches Linking APIS for any linked accounts.

    async def retrieve_discord_links(self, steam_id:int):
        guild_profiles = await self.get_all_guilds()
        discord_ids = []
        for guild_profile in guild_profiles:
            guild_profile:model.GuildProfile = guild_profile
            db_check = await mydatabase.link_check(steam_id=steam_id, orgid=guild_profile.organization_id)
            if not db_check and guild_profile.linking_url:
                url = guild_profile.linking_url
                token = guild_profile.linking_token
                url = url.format(token=token, steam_id=steam_id)
                response = None
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response = await response.json()
                if response:
                    response = str(response).lower()
                    if response == "no users found" or response == "no users found." or response == "none" or response == "null":
                        continue
                    
                    if len(response) < 25:
                        if not response in discord_ids:
                            discord_ids.append(str(response))
                            await mydatabase.save_links(steamid=steam_id,discordid=response, orgid=guild_profile.organization_id)
        return discord_ids

    async def add_manager(self, guildid: str, user_id: str):
        await self.approve_user(user_id=user_id, guildid=guildid, approved=True)
        await mydatabase.add_manager(guildid=str(guildid), user_id=str(user_id))


    async def get_managers(self, guildid: str):
        managers = await mydatabase.get_managers(guildid=guildid)
        manager_list = []
        for manager in managers:
            print(manager)
            manager_list.append(manager['manager_id'])
        return manager_list


    async def remove_manager(self, guildid: str, user_id: str):
        await self.approve_user(user_id=user_id, guildid=guildid, approved=False)
        await mydatabase.remove_manager(guildid=str(guildid), user_id=str(user_id))


    async def setting_show_logs(self, guildid: str, setting: bool):
        await mydatabase.show_logs(guildid=guildid, setting=setting)


    async def setting_log_channel(self, guildid: str, channel_id: str):
        await mydatabase.log_channel(guildid=guildid, channel_id=str(channel_id))


    async def update_server(self, guildid: str, server_name: str, organization_id: str):
        await mydatabase.update_server(guildid=guildid, server_name=server_name, organization_id=organization_id)


    async def setmanager(self, guildid: str, manager_id: str):
        await self.approve_user(user_id=manager_id, guildid=guildid, approved=True)
        await mydatabase.add_manager(guildid=str(guildid), user_id=str(manager_id))



    async def get_rah_link_by_server(self, server_id: str, discord_id: str, steam_id: str):
        return await mydatabase.rah_link_by_server(server_id=server_id, discord_id=discord_id, steam_id=steam_id)


    async def get_rah_link_by_user(self, user_id: str, discord_id: str, steam_id: str):
        return await mydatabase.rah_link_by_user(user_id=user_id, discord_id=discord_id, steam_id=steam_id)


    async def add_ids(self, discord_id: str, steam_id: str, server_id: str, bmid:str, confidence:int,user_id: str):
        await mydatabase.save_or_update_ids(steamid=steam_id, bmid=bmid, discordid=discord_id, confidence=confidence)
        await mydatabase.add_rah_link(user_id=user_id, steam_id=steam_id, discord_id=discord_id, server_id=server_id)
        
    async def store_logs(self, author_id: str, author_name: str, guild_name: str, guild_id: str, channel_id: str, channel_name: str, steam_id:str, command:str):
        await mydatabase.log(author_id=author_id,
                    author_name=author_name,
                    guild_name=guild_name,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    channel_name=channel_name,
                    steam_id=steam_id,
                    command=command)

    async def guild_setting(self, guildid:str, setting:str, option:bool):
        await mydatabase.guild_settings(guildid=guildid, setting=setting, option=option)

    async def add_link_api(self, guildid:str, url:str, token:str):
        await mydatabase.guild_settings(guildid=guildid, setting="linking_url", option=url)
        await mydatabase.guild_settings(guildid=guildid, setting="linking_token", option=token)
        
    async def user_setting(self, guildid:str, user_id:str, setting:str, option:bool):
        await mydatabase.user_settings(guildid=guildid,userid=user_id, setting=setting, option=option)


    async def get_banned_profile(self, steam_id:str):
        document = await mydatabase.banned_profile(steam_id)
        if document:
            ip_info = model.Isps(isp_name=document['isp_name'],is_vpn=document['is_vpn'], country=document['country'])
            profile = model.Player(battlemetrics_id=document['battlemetrics_id'],ip_info=ip_info, steam_id=document['steam_id'],
                            player_name=document['player_name'], community_banned=document['community_banned'], game_ban_count=document['game_ban_count'],
                            rustbanned_text = document['rustbanned_text'], rustbancount=document['rustbancount'], banned_days_ago=document['banned_days_ago'])
            return profile
        
    async def get_logs_by_author(self, author_id):
        return await mydatabase.get_logs_by_author(author_id=author_id)

    async def get_logs_by_steamid(self, steam_id):
        return await mydatabase.get_logs_by_steamid(steam_id=steam_id)

    async def get_logs_by_command(self, command):
        return await mydatabase.get_logs_by_command(command=command)

    async def get_logs_by_guild(self, guild_id):
        return await mydatabase.get_logs_by_guild(guild_id=guild_id)


    async def add_monitor_setting(self, settings):
        
        return await mydatabase.add_monitor_setting(settings=settings)
        
    async def add_monitor_ignore_role(self, guild_id:str, role_id:str):
        
        return await mydatabase.add_monitor_ignore_role(guild_id = guild_id, role_id = role_id)
        
    async def get_monitor_info(self, guild_id:str) -> list:
        response = await mydatabase.get_monitor_info(guild_id=guild_id)
        if not response:
            return
        
        settings = []
        
        for setting in response:
            settings.append(model.Monitor(**setting))
        return settings

    async def get_monitor_ignore_role(self, guild_id:str) -> list:
        response = await mydatabase.get_monitor_ignore_role(guild_id=guild_id)
        if not response:
            return
        ignored_roles = []
        
        for setting in response:
            ignored_roles.append(int(setting['role_id']))
            
        return ignored_roles