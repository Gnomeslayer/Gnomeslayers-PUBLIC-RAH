from dataclasses import dataclass, field
from typing import Optional,List

@dataclass
class Playernames():
    name:str = None
    steamid:int = 0
    
@dataclass
class Servers():
    serverid:int = 0
    servername:str = None
    orgid:int = 0
    orgname:str = None

@dataclass
class Isps():
    _id: int = None
    ip: str = None
    isp_id: str = None
    isp_name: str = None
    is_vpn: bool = None
    country: str = None

@dataclass
class Logs():
    _id: int = None
    author_id: int = None
    author_name: str = None
    author_roles: str = None
    guild_name: str = None
    guild_id: int = None
    channel_id: int = None
    channel_name: str = None
    content: str = None
    time: str = None

@dataclass
class Tos():
    signed_tos:bool = False
    user_id:int = 0

@dataclass
class Blacklisted_users():
    user_id:int = 0

@dataclass
class GuildProfile():
    server_id:int = 0
    server_name:str = None
    organization_id:int = None
    whitelisted:bool = False
    overwrite_preferences:bool = False
    ephemeral_responses:bool = False
    log_channel:str = None
    show_logs:bool = False
    banlist:str = None
    enable_vdf:bool = True
    delete_vdf:bool = False
    get_alts:bool = True
    get_kda:bool = True
    sharing_data:bool = True
    cheetos:bool = True
    linking_url:str = None
    linking_token:str = None

@dataclass
class GuildManagers():
    server_id:int = 0
    manager_id:int = 0

@dataclass
class UserProfile():
    user_id:int = 0
    server_id:int = 0
    approved:bool = False
    ephemeral_responses:bool = True
    include_alts:bool = True
    include_stats:bool = True
    
@dataclass
class Playerids():
    _id: int = None
    steamid: str = None
    steamurl: str = None
    bmid: int = None
    discordid: list = None
    confidence: int = 0

@dataclass
class playerprofile():
    battlemetrics_id:int = 0
    steam_id:int = 0
    player_name:str = None
    community_banned:bool = False
    game_ban_count:int = 0
    rustbanned_text:str = None
    rustbancount:int = None
    banned_days_ago:int = 0
    isp_name:str = None
    is_vpn:bool = False
    country:str = None

@dataclass
class Links():
    discordid:int = 0
    steamid:int = 0
    orgid:int = 0

@dataclass
class Playerstats():
    _id: int = None
    steamid: str = None
    bmid: int = None
    kills_day: int = 0
    kills_week: int = 0
    kills_two_weeks: int = 0
    deaths_day: int = 0
    deaths_week: int = 0
    deaths_two_weeks: int = 0  

@dataclass
class ActivityLogs():
    kills_day:int = 0
    deaths_day:int = 0
    player_reports:int = 0
    arkan_reports:int = 0
    recent_server_id: int = 0
    recent_server_name: str = None
    still_online:str = None


@dataclass
class Notes():
    _id: int = None
    noteid: int = None
    bmid: int = None
    orgid: int = None
    notemakerid: int = None
    orgname: str = None
    note: str = None
    notemakername: str = None

@dataclass
class Serverbans():
    _id: int = None
    bmid: int = None
    steamid: str = None
    bandate: str = None
    expires: str = None
    banid: int = None
    bannote: str = None
    serverid: int = None
    servername: str = None
    banner: str = None
    banreason: str = None
    uuid: str = None
    orgid: int = None

@dataclass
class Player():
    _id: int = None
    battlemetrics_id: int = None
    steam_id: int = None
    profile_url: str = None
    avatar_url: str = None
    player_name: str = None
    names: list = None
    account_created: str = None
    playtime: int = None
    playtime_training: int = None
    rustbanned_bool: bool = None
    rustbanned_text: str = None
    rustbancount: int = None
    banned_days_ago: int = None
    limited: bool = None
    community_banned: bool = False
    game_ban_count: int = 0
    vac_banned: bool = False
    vacban_count: int = 0
    last_ban: int = 0,
    recent_server_name: str = None
    recent_server_id: int = 0,
    ip_info: Isps = Isps
    still_online: str = None

@dataclass
class UserProfile():
    _id: int = None
    user_id: str = None
    server_id: str = None
    approved: bool = False
    ephemeral_responses: bool = True
    include_alts: bool = True
    include_stats: bool = True
    include_serverbans:bool = True
    include_notes:bool = True
    include_cheetos:bool = True

@dataclass
class ServerProfile():
    _id: int = None
    server_id: str = None
    server_name: str = None
    organization_id: int = 0
    whitelisted: bool = False
    overwrite_preferences: bool = True
    ephemeral_responses: bool = True
    log_channel: str = None
    show_logs: bool = False
    api_token: str = None
    banlist: str = None
    enable_vdf: bool = True
    sharing_data: bool = True
    delete_vdf: bool = False
    include_alts: bool = True
    include_stats: bool = True
    include_cheetos: bool = True
    include_notes: bool = True
    include_serverbans: bool = True
    force_rah:bool = False
    linking_url:str = None
    linking_token:str = None
    rah_listen_channel:str = 0
    vdf_listen_channel:str = 0
    
    
@dataclass
class Profiles():
    server_profile:ServerProfile = ServerProfile
    user_profile:UserProfile = UserProfile
    blacklisted:bool = False
    signed_tos:Tos = Tos
    
@dataclass
class Monitor():
    _id: int = None
    phrase:str = None
    ban:bool = False
    timeout_user:bool = False
    delete:bool = False
    warn:bool = False
    warn_message:str = None
    alert_staff:bool = False
    respond:bool = False
    response_message:str = None
    timeout_time:int = 0
    match_strength_percent:int = 100
    guild_id:int = 0
    
@dataclass
class MonitorSettings():
    phrase:str
    ban:bool = False
    timeout_user:bool = False
    delete:bool = False
    warn:bool = False
    alert_staff:bool = False
    respond:bool = False
    response_message:str = None
    timeout_time:int = 1
    match_strength_percent:int = 100
    warn_message:str = "This guild doesn't allow this message. Appropriate actions have been taken."
    guild_id:int = 0
    

@dataclass
class Server:
    server_id: Optional[int] = None
    server_name: Optional[str] = None
    player_count: int = 0
    max_players:int = 0
    player_ids: List[int] = field(default_factory=list)