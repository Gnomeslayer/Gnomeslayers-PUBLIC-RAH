from discord import Interaction, ui, ButtonStyle
from supportfiles.embedfactory import EmbedFactory
from supportfiles.views.relatedbuttons import RelatedButtons
from supportfiles.views.notesbuttons import NotesButtons
from supportfiles.views.serverbansbuttons import ServerBansButtons
from supportfiles.views.logsbuttons import AdditionalInfoButtons
from supportfiles.functions import MainFunctions
import supportfiles.model as model


class ProfileButtons(ui.View):
    def __init__(self, config:dict):
        super().__init__()
        self.config = config
        self.serverbans = None
        self.notes = None
        self.related_players = None
        self.original_player:model.Player = None
        self.embed_factory = EmbedFactory(config=config, bot=self)
        self.fun = MainFunctions(config=config)
        
    @ui.button(label="View Related", style=ButtonStyle.green, row=0, emoji="🧑‍🤝‍🧑")
    async def view_related(self, interaction: Interaction, button: ui.Button):
        if self.related_players:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("Grabbing player information. One moment please.", ephemeral=True)
            embed = await self.embed_factory.create_related_profile_embed(original_player=self.original_player, related_player=self.related_players[0], 
                                                                          guild_id=interaction.guild.id)
            related_pagination = RelatedButtons(config=self.config)
            related_pagination.clear_items()
            
            related_pagination.related_players = self.related_players
            related_pagination.original_player = self.original_player
            if len(self.related_players) > 1:
                related_pagination.add_item(related_pagination.next)
                related_pagination.add_item(related_pagination.previous)
                related_pagination.next.label = f"View Related 2/{len(self.related_players)}"
                related_pagination.previous.label = f"View Related {len(self.related_players)}/{len(self.related_players)}"
            await interaction.followup.send(embed=embed, view=related_pagination, ephemeral=True)
        else:
            await interaction.response.send_message("There are no related players. Bummer.", ephemeral=True)

    @ui.button(label="View Notes", style=ButtonStyle.green, row=0, emoji="🗒️")
    async def view_notes(self, interaction: Interaction, button: ui.Button):
        if self.notes:
            embed = await self.embed_factory.create_notes_embed(self.notes[0])
            pagination_buttons = NotesButtons(config=self.config)
            pagination_buttons.clear_items()
            pagination_buttons.add_item(pagination_buttons.send_file)
            pagination_buttons.notes = self.notes
            if len(self.notes) > 1:
                pagination_buttons.add_item(pagination_buttons.next_note)
                pagination_buttons.add_item(pagination_buttons.previous_note)
                pagination_buttons.next_note.label = f"View Note 2/{len(self.notes)}"
                pagination_buttons.previous_note.label = f"View Note {len(self.notes)}/{len(self.notes)}" 
            
            await interaction.response.send_message(embed=embed, view=pagination_buttons, ephemeral=True)
        else:
           await interaction.response.send_message("There are no notes to show.", ephemeral=True)

    @ui.button(label="View Serverbans", style=ButtonStyle.green, row=0, emoji="🔨")
    async def view_serverbans(self, interaction: Interaction, button: ui.Button):
        
        if self.serverbans:
            embed = await self.embed_factory.create_ban_embed(ban=self.serverbans[0])
            pagination_buttons = ServerBansButtons(config=self.config)
            pagination_buttons.clear_items()
            pagination_buttons.add_item(pagination_buttons.send_file)
            pagination_buttons.serverbans = self.serverbans
            
            if len(self.serverbans) > 1:
                pagination_buttons.add_item(pagination_buttons.next_ban)
                pagination_buttons.add_item(pagination_buttons.previous_ban)
                pagination_buttons.next_ban.label = f"View Ban 2/{len(self.serverbans)}"
                pagination_buttons.previous_ban.label = f"View Ban {len(self.serverbans)}/{len(self.serverbans)}" 
            await interaction.response.send_message(embed=embed, view=pagination_buttons, ephemeral=True)
        else:
           await interaction.response.send_message("There are no serverbans to show.", ephemeral=True)
           
    @ui.button(label="View Activity Logs", style=ButtonStyle.gray, row=1, emoji="🧱")
    async def view_activity_logs(self, interaction: Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Retrieving Log Data now.", ephemeral=True)
        log_data = await self.fun.get_activity_logs(self.original_player.battlemetrics_id)
        embed = await self.embed_factory.create_activity_embed(log_data)
        extrabuttons = AdditionalInfoButtons(config=self.config)
        extrabuttons.player_name = self.original_player.player_name
        extrabuttons.steam_id = self.original_player.steam_id
        extrabuttons.bmid = self.original_player.battlemetrics_id
        if log_data.recent_server_id:
            extrabuttons.server_id = log_data.recent_server_id
        else:
            extrabuttons.view_teaminfo.disabled = True
            extrabuttons.view_combatlog.disabled = True
            
        await interaction.followup.send(embed=embed, ephemeral=True, view=extrabuttons)