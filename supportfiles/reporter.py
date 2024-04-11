from battlemetrics import Battlemetrics
from discord.ext.commands import Bot
from supportfiles.embedfactory import EmbedFactory
from discord import TextChannel

import re

class Reporter:
    def __init__(self, config: dict, bot:Bot, channel:TextChannel = None):
        self.bot = bot
        self.config = config
        self.api = Battlemetrics(api_key=config["tokens"]["battlemetrics_token"])
        self.embedfactory = EmbedFactory(config=config, bot=bot)
        self.channel = channel
        self.sent_teaminfo = False
        

    async def sort_arkan_data(self, data:dict) -> dict:
        message_id = data['id'] #Message ID
        
        #Format the message to ensure we can actually work with it.
        message = r"{}".format(data['attributes']['message'])
        message = re.sub('Shooting on the move\n',
                        'Shooting on the move | ', message)
        message = re.sub('Shooting on the move\nRecoil',
                        "Shooting on the move | Recoil", message)
        message_split = message.split("\n")
        
        #Sort our data        
        report = []
        myrecoils = []
        for message in message_split:
            if message:
                report.append(message)
                if "Projectile" in message:
                    myrecoils.append(message)
        
        projectiles = ''
        for recoil in myrecoils:
            recoil_list = recoil.split(" | ")
            if projectiles:
                projectiles += f"**{recoil_list[0]}**```"
            else:
                projectiles = f"**{recoil_list[0]}**```"
            recoil_list.pop(0)
            for projectile in recoil_list:
                if projectiles:
                    projectiles += f"{projectile}"
                else:
                    projectiles = f"{projectile}"
            projectiles += "```"
                
        #Extract some data before we fuck with the recoil
        title = report[0]
        player = report[1]
        player_name = player[:-18][7:]
        steamid = player[-17:] #Steam ID?
        violation_number = int(report[2][14:])
        shotcount = report[3][12:]
        probability = report[4][12:-1]
        
        attachment_count = int(report[5][20:])
        attachments = ""
        count = 0
        report_jump = 0
        while count < attachment_count:
            attachment_report = report[6 + count].split(".")
            attachment = attachment_report[2]
            if len(attachment_report) > 3:
                attachment += f" {attachment_report[3]}"
            if attachments:
                attachments += f"\n{attachment}"
            else:
                attachments = f"{attachment}"
            count += 1
            report_jump += 1
            
        recoil_angles = re.findall("(\sRecoil\sangle:\s)(\d{1,2}\.?\d*)", data['attributes']['message'])
        zero_count = 0
        for angle in recoil_angles:
            value = float(angle[1])
            text = angle[0]
            text = re.sub('\n', '', text)
            if text[0] == ' ':
                text = text[1:]
            text = text[:-2]
            if value == 0:
                zero_count += 1

        weapon = report[6+report_jump][9:-1]
        ammo = report[7+report_jump][7:]

        serverid = data['relationships']['servers']['data'][0]['id']
        orgid = data['relationships']['organizations']['data'][0]['id']
        battlemetrics_id = data['relationships']['players']['data'][0]['id']
        bmurl = f"https://www.battlemetrics.com/rcon/players/{battlemetrics_id}"
        serverinfo = None
        servername = "No Server name"
        #playerids = None
        #bmid = playerids['bmid']
        #bmurl = f"https://www.battlemetrics.com/rcon/players/{bmid}"

        #playerinfo = ""

        #playerinfo = await bm.get_player_info(bmid=bmid)
        #footer = arkancfg['default']['footer']
        #if orgid in arkancfg:
        #    footer = arkancfg[orgid]['footer']

        sorted_data = {
            "timestamp": data['attributes']['timestamp'],
            "orgid": orgid,
            "serverid": serverid,
            "battlemetrics_id": battlemetrics_id,
            "servername": servername,
            "bmurl": bmurl,
            "title": title,
            "playername": player_name,
            "steamid": steamid,
            "violation_number": violation_number,
            "shotcount": shotcount,
            "probability": probability,
            "attachments_count": attachment_count,
            "attachments": attachments,
            "weapon": weapon,
            "ammo": ammo,
            "projectiles": projectiles,
            "zero_count": zero_count,
            "autoban": "No action has been taken",
            "action_taken": "No action taken",
            "footer": f"Footer Text - [{message_id}]"
        }

        return sorted_data

    async def sort_aimbot_data(self, data:dict) -> dict:
        message = data['attributes']['message']
        message = r"{}".format(message).split("\n")
        steam_id = message[1] # Get the steam ID
        organization_id = data['relationships']['organizations']['data'][0]['id']
        serverid = data['relationships']['servers']['data'][0]['id']
        violation = int(message[2].split("#")[1]) #The violation count!
        steam_id = steam_id.split(" ")[1] #Refine our steam ID to actually be a steam Id
        if data.get('relationships'):
            if data['relationships'].get('players'):
                battlemetrics_id = data['relationships']['players']['data'][0]['id']
                battlemetrics_url = f"[RCON](https://www.battlemetrics.com/rcon/players/{battlemetrics_id})"
            else:
                battlemetrics_id = None,
                battlemetrics_url = None
        else:
            battlemetrics_url = None
            battlemetrics_id = None
            
        playername = None
        
        aimbot_data = {
                "violation_number": violation,
                "playername": "Unknown",
                "steam_id": steam_id,
                "servername": "Unknown",
                "serverid": serverid,
                "organization_id": organization_id,
                "battlemetrics_id": battlemetrics_id,
                "playerinfo": None,
                "playername": playername,
                "battlemetrics_url": battlemetrics_url,
                "action_taken": None
            }
        return aimbot_data
    
    async def kick_player(self, steamid:str, serverid:str):
        command = f"kick {steamid}"
        
        response = await self.api.server.console_command(server_id=serverid, command=command)
        if response.get('data'):
            return response['data']['attributes']['result']
        
    async def get_teaminfo(self, steamid:str, serverid:str):
        command = f"teaminfo {steamid}"
        
        response = await self.api.server.console_command(server_id=serverid, command=command)
        if response.get('data'):
            return response['data']['attributes']['result']
        
    async def ban_player(self, reason:str, note:str, org_id:str, server_id:str, battlemetrics_id:str, steam_id:str):
        await self.api.player.add_ban(reason=reason,
                                              note=note,
                                              org_id=org_id,
                                              banlist=self.config['additional']['banlist'],
                                              server_id=server_id,
                                              battlemetrics_id=battlemetrics_id,
                                              steam_id=steam_id)
    
    async def aimbot(self, data:dict):
        sorted_data = await self.sort_aimbot_data(data=data)
        if sorted_data['violation_number'] >= self.config['cogs']['aimbot']['violation_threshold']:
            if self.config['cogs']['aimbot']['include_teaminfo']:
                teaminfo = await self.get_teaminfo(steamid=sorted_data['steam_id'], serverid=sorted_data['serverid'])
                teaminfo_channel:TextChannel = self.bot.get_channel(self.config['cogs']['aimbot']['teaminfo_channel'])
                teaminfo_embed = await self.embedfactory.set_teaminfo_embed(teaminfo=teaminfo, player_name=sorted_data['playername'])
                await teaminfo_channel.send(embed=teaminfo_embed)
                
            
            if self.config['cogs']['aimbot']['kick']:
                sorted_data['action_taken'] = "Auto kicked the player"
                await self.kick_player(steamid=sorted['steam_id'], serverid=sorted_data['serverid'])
                
                
            if self.config['cogs']['aimbot']['ban']:
                sorted_data['action_taken'] = "Auto banned the player"
                await self.ban_player(reason="AIMBOT VIOLATION",
                                              note="Violated the aimbot",
                                              org_id=sorted_data['organization_id'],
                                              server_id=sorted_data['serverid'],
                                              battlemetrics_id=sorted_data['battlemetrics_id'],
                                              steam_id=sorted_data['steam_id'])
        report_channel:TextChannel = self.bot.get_channel(self.config['cogs']['aimbot']['report_channel'])
        report_embed = await self.embedfactory.aimbot_embed(sorted_data)
        await report_channel.send(embed=report_embed)
        
    async def arkan(self, data:dict):
            
        sorted_data = await self.sort_arkan_data(data=data)
        return sorted_data