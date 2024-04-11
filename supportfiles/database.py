from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from supportfiles.model import MonitorSettings

client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client['rahmaster']

playerids_table = db["playerids"]  # Using
playerprofile_table = db["playerprofile"]  # Not Using
servers_table = db["servers"]  # Not Properly using
isps_table = db["isps"]
logs_table = db['logs']
blacklisted_users_table = db['blacklisted_users']
guild_profiles_table = db['guild_profile']
guild_managers_table = db['guild_managers']
user_profiles_table = db['user_profile']
tos_table = db['tos']
rahlink_table = db['rahlink']
banned_profiles_table = db['banned_profiles']
link_check_table = db['link_check']
monitor_settings_table = db['monitor_settings']
monitor_ignore_roles_table = db['monitor_ignore_roles']


async def get_player_ids_by_url(steamurl: str) -> None:
    document = await playerids_table.find_one({'steamurl': steamurl})
    return document


async def get_user_tos(user_id: str):
    document = await tos_table.find_one({'user_id': str(user_id)})
    return document


async def get_blacklisted_user(user_id: str) -> dict:
    document = await blacklisted_users_table.find_one({"user_id": str(user_id)})
    return document


async def get_server_manager(user_id: str, guildid: str):
    document = await guild_managers_table.find_one(
        {"manager_id": str(user_id), "server_id": str(guildid)})
    return document

async def add_or_update_tos(user_id: str, signed: bool):
    document = await tos_table.find_one({'user_id': str(user_id)})
    if document:
        tos_table.update_one({'user_id': str(user_id)}, {
                             '$set': {'signed_tos': signed}})
    else:
        tos_table.insert_one({'user_id': str(user_id), 'signed_tos': signed})


async def add_or_update_approve(user_id: str, guildid: str, approved: bool = False):

    document = await user_profiles_table.find_one(
        {'user_id': str(user_id), 'server_id': str(guildid)})
    if document:
        user_profiles_table.update_one({'user_id': str(user_id), 'server_id': str(guildid)}, {
                                       '$set': {'approved': approved}})
    else:
        user_profiles_table.insert_one(
            {
                "user_id": f"{user_id}",
                "server_id": f"{guildid}",
                "approved": approved,
                "ephemeral_responses": True,
                "include_alts": True,
                "include_stats": True,
                "include_serverbans": True,
                "include_notes": True,
                "include_cheetos": True
            })


async def blacklisted_user(user_id: str):
    document = await blacklisted_users_table.find_one({'user_id': str(user_id)})
    if document:
        return
    else:
        blacklisted_users_table.insert_one({'user_id': str(user_id)})






async def authorize_server(guildid: str, whitelisted: bool = False):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if document:
        guild_profiles_table.update_one({'server_id': str(guildid)}, {'$set': {
            'whitelisted': whitelisted}})
    else:
        await add_guild(guildid=guildid, whitelisted=whitelisted)


async def add_guild(guildid: str, whitelisted: bool = False):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if document:
        return
    guild_profiles_table.insert_one(
        {'server_id': str(guildid), 'whitelisted': whitelisted, 'organization_id': 0, 'server_name': "Unknown"})


async def add_manager(guildid: str, user_id: str):
    document = await guild_managers_table.find_one(
        {'manager_id': str(user_id), 'server_id': str(guildid)})
    if document:
        return
    guild_managers_table.insert_one(
        {'manager_id': str(user_id), 'server_id': str(guildid)}
    )





async def remove_manager(guildid: str, user_id: str):
    document = await guild_managers_table.find_one(
        {'manager_id': str(user_id), 'server_id': str(guildid)})
    if document:
        return
    guild_managers_table.delete_one(
        {'manager_id': str(user_id), 'server_id': str(guildid)}
    )


async def show_logs(guildid: str, setting: bool):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if not document:
        return

    guild_profiles_table.update_one({'server_id': str(guildid)}, {'$set': {
        'show_logs': setting}})


async def log_channel(guildid: str, channel_id: str):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if not document:
        return

    guild_profiles_table.update_one({'server_id': str(guildid)}, {'$set': {
        'log_channel': str(channel_id)}})


async def delete_vdf(guildid: str, setting: bool):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if not document:
        return

    guild_profiles_table.update_one({'server_id': str(guildid)}, {'$set': {
        'delete_vdf': setting}})


async def update_server(guildid: str, server_name: str, organization_id: str):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if not document:
        return

    guild_profiles_table.update_one({'server_id': str(guildid)}, {
                                    '$set': {'server_name': server_name, 'organization_id': str(organization_id)}})






async def guild_settings(guildid: str, setting: str, option: bool):
    document = await guild_profiles_table.find_one({'server_id': str(guildid)})
    if not document:
        return
    setting = setting.lower()
    guild_profiles_table.update_one({'server_id': str(guildid)}, {'$set': {
        f'{setting}': option}})
    

async def user_settings(guildid: str, userid:str, setting: str, option: bool):
    document = await user_profiles_table.find_one({'server_id': str(guildid), 'user_id': str(userid)})
    setting = setting.lower()
    if not document:
        user_profiles_table.insert_one({'server_id': str(guildid), 'user_id': str(
            userid), 'approved': False, f'{setting}': option})
    else:
        user_profiles_table.update_one({'server_id': str(guildid), 'user_id': str(userid)}, {'$set': {
            f'{setting}': option}})

#Updated Tables

async def get_user_profile_by_guild(user_id: str, guild_id: str):
    document = await user_profiles_table.find_one(
        {'user_id': str(user_id), 'server_id': str(guild_id)})
    return document


async def all_users():
    documents = user_profiles_table.find()
    user_list = []
    async for document in documents:
        user_list.append(document)
    return user_list

async def add_rah_link(user_id:str, discord_id:str, steam_id:str, server_id:str):
    
    if discord_id:
        rahlink_table.insert_one(
            {'user_id': str(user_id), 'discord_id': str(discord_id), 'steam_id': str(steam_id), 'server_id': str(server_id)})

async def all_guilds() -> dict:
    documents = guild_profiles_table.find({})
    guilds_list = []
    async for document in documents:
        guilds_list.append(document)
    return guilds_list

async def get_ip_info(ip: str):
    document = await isps_table.find_one({"ip": str(ip)})
    return document

async def get_guild_profile_by_guildid(guildid: str):
    document = await guild_profiles_table.find_one({"server_id": str(guildid)})
    if document:
        if document.get('sharing_data') is None:
            document['sharing_data'] = True
            await guild_settings(guildid=guildid, setting='sharing_data', option=True)
    return document

async def get_guild_profile_by_orgid(organization_id: str):
    document = await guild_profiles_table.find_one({"organization_id": str(organization_id)})
    if document:
        if document.get('sharing_data') is None:
            document['sharing_data'] = True
            await guild_settings(guildid=document['server_id'], setting='sharing_data', option=True)
    return document

async def rah_link_by_user(user_id: str, discord_id: str, steam_id: str):
    document = await rahlink_table.find_one(
        {'user_id': str(user_id), 'discord_id': str(discord_id), 'steam_id': str(steam_id)})
    return document

async def rah_link_by_server(server_id:str, discord_id:str, steam_id:str):
    document = await rahlink_table.find_one({'server_id': str(server_id), 'discord_id': str(discord_id), 'steam_id': str(steam_id)})
    return document

async def add_ip(ip: str, isp_id: str, is_vpn: bool, country: str, isp_name: str):
    documents = await get_ip_info(ip=ip)
    if documents:
        return
    isps_table.insert_one({
        "ip": str(ip),
        "isp_id": str(isp_id),
        "is_vpn": is_vpn,
        "country": country,
        "isp_name": isp_name
    })

async def get_player_ids_by_steamid(steamid: str) -> None:
    documents = playerids_table.find({'steamid': str(steamid)})
    id_list = []
    async for document in documents:
        doc = {
            'steamid': document['steamid'],
            'bmid': document['bmid'],
            'steamurl': document['steamurl'],
            'discordid': document['discordid'],
            'confidence': document['confidence']
        }
        id_list.append(doc)
    return id_list

async def save_links(steamid:str, discordid:str, orgid:str):
    document = await link_check(steam_id=steamid,orgid=orgid)
    if not document:
        link_check_table.insert_one({'steamid': steamid, 'orgid':orgid,  'discordid': discordid})

async def get_user_profile(user_id: str):
    documents = user_profiles_table.find({'user_id': str(user_id)})
    stuff = []
    async for document in documents:
        stuff.append(document)
    
    return stuff

async def save_or_update_ids(steamid: str = None, bmid: str = None, steamurl: str = None, discordid: str = None, confidence: int = 0) -> None:
    steamid = str(steamid)
    bmid = str(bmid)
    steamurl = str(steamurl)

    if discordid:
        discordid = str(discordid)
    else:
        discordid = "None"
    # Check if there's a document with the provided steamid, bmid, and discordid
    document = await playerids_table.find_one({'steamid': steamid, 'bmid': bmid, 'discordid': discordid})

    if document:
        # Update the existing document with the new confidence value
        await playerids_table.update_one({'steamid': steamid, 'bmid': bmid, 'discordid': discordid}, {'$set': {'confidence': confidence}})
    else:
        # Check if there's a document with the provided steamid, bmid, and 'None' discordid
        document = await playerids_table.find_one({'steamid': steamid, 'bmid': bmid, 'discordid': 'None'})

        if document:
            # Update the existing document with the new discordid and confidence value
            await playerids_table.update_one({'steamid': steamid, 'bmid': bmid, 'discordid': 'None'}, {'$set': {'discordid': discordid, 'confidence': confidence}})
        else:
            # If no document is found, insert a new one
            await playerids_table.insert_one({'steamid': steamid, 'bmid': bmid, 'confidence': confidence, 'steamurl': steamurl, 'discordid': discordid})

async def banned_profile(steam_id:str):
    document = await banned_profiles_table.find_one({'steamid': steam_id})
    return document
    
async def add_banned_profile(battlemetrics_id, steam_id, player_name, 
                             community_banned, game_ban_count, rustbanned_text,
                             rustbancount, banned_days_ago, isp_name, is_vpn, country):
    document = await banned_profile(steam_id=steam_id)
    if not document:
        banned_profiles_table.insert_one({'battlemetrics_id':battlemetrics_id, 'steam_id':steam_id, 'player_name':player_name, 
                             'community_banned': community_banned, 'game_ban_count':game_ban_count, 'rustbanned_text': rustbanned_text,
                             'rustbancount': rustbancount, 'banned_days_ago': banned_days_ago, 'isp_name':isp_name, 'is_vpn': is_vpn, 'country': country})

async def add_monitor_setting(settings:MonitorSettings):
    monitor_settings_table.insert_one({'phrase': settings.phrase, 'ban': settings.ban, 'timeout_user': settings.timeout_user,
                                       'delete': settings.delete, 'warn': settings.warn, 'alert_staff': settings.alert_staff,
                                       'respond': settings.respond, 'response_message': settings.response_message,
                                       'timeout_time': settings.timeout_time, 'match_strength_percent': settings.match_strength_percent,
                                       'guild_id': str(settings.guild_id), 'warn_message': settings.warn_message})

async def add_monitor_ignore_role(guild_id:str, role_id:str):
    monitor_ignore_roles_table.insert_one({'guild_id': str(guild_id), 'role_id': str(role_id)})

async def link_check(steam_id:str, orgid:int):
    documents = link_check_table.find({'steamid': steam_id, 'orgid': orgid})
    link_checks = []
    async for document in documents:
        link_checks.append(document)
    return link_checks

async def log(author_id: str, author_name: str, guild_name: str, guild_id: str, channel_id: str, channel_name: str, steam_id:str, command:str) -> None:
    log_entry = {
        'author_id': str(author_id),
        'author_name': str(author_name),
        'guild_name': str(guild_name),
        'guild_id': str(guild_id),
        'channel_id': str(channel_id),
        'channel_name': str(channel_name),
        'steam_id': steam_id,
        'command': command,
        'time': str(datetime.now())
    }
    logs_table.insert_one(log_entry)
    
async def get_logs_by_author(author_id):
    documents = logs_table.find({'author_id':author_id})
    logs = []
    async for log in documents:
        logs.append(log)
    return logs

async def get_logs_by_steamid(steam_id):
    documents = logs_table.find({'steam_id':steam_id})
    logs = []
    async for log in documents:
        logs.append(log)
    return logs

async def get_logs_by_command(command):
    documents = logs_table.find({'command':command})
    logs = []
    async for log in documents:
        logs.append(log)
    return logs

async def get_logs_by_guild(guild_id):
    documents = logs_table.find({'guild_id':guild_id})
    logs = []
    async for log in documents:
        logs.append(log)
    return logs

async def all_users_by_guild(guildid:str):
    documents = user_profiles_table.find({'server_id': str(guildid)})
    user_list = []
    async for document in documents:
        user_list.append(document)
    return user_list

async def get_managers(guildid: str):
    documents = guild_managers_table.find({'server_id': str(guildid)})
    manager_list = []
    async for document in documents:
        manager_list.append(document)
    
    return manager_list


async def get_monitor_info(guild_id:str) -> list:
    documents = monitor_settings_table.find({'guild_id': str(guild_id)})
    monitor_settings = []
    async for document in documents:
        monitor_settings.append(document)
    return monitor_settings

async def get_monitor_ignore_role(guild_id:str):
    documents = monitor_ignore_roles_table.find({'guild_id': str(guild_id)})
    monitor_settings = []
    async for document in documents:
        monitor_settings.append(document)
    return monitor_settings