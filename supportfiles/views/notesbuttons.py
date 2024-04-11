from discord import ui, ButtonStyle, Interaction, File
from supportfiles.embedfactory import EmbedFactory
import supportfiles.model as model
import os
import json

class NotesButtons(ui.View):
    def __init__(self, config:dict):
        super().__init__()
        self.notes = None
        self.page_number = 0
        self.config = config
        self.embed_factory = EmbedFactory(config=config, bot=self)
        
    @ui.button(label="Previous Note", style=ButtonStyle.red)
    async def previous_note(self, interaction: Interaction, button: ui.Button):
        if self.page_number == 0:
            self.page_number = len(self.notes) - 1
        else:
            self.page_number -= 1
        embed = await self.embed_factory.create_notes_embed(self.notes[self.page_number])
        
        button.label = f"View Note {self.page_number}/{len(self.notes)}"
        self.next_note.label = f"View Note {self.page_number + 1}/{len(self.notes)}"
        
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Send as file", style=ButtonStyle.blurple)
    async def send_file(self, interaction: Interaction, button: ui.Button):
        thenote:model.Notes = self.notes[self.page_number]
        thenote = {
            "noteid": thenote.noteid,
            "bmid": thenote.bmid,
            "orgid": thenote.orgid,
            "notemakerid": thenote.notemakerid,
            "orgname": thenote.orgname,
            "notemakername": thenote.notemakername,
            "note": thenote.note
        }

        with open(f"{interaction.user.id}_note_file.json", "w") as f:
            f.write(json.dumps(thenote, indent=4))
        await interaction.response.send_message(file=File(f"{interaction.user.id}_note_file.json"), ephemeral=True)
        os.remove(f"{interaction.user.id}_note_file.json")

    @ui.button(label="Next Note", style=ButtonStyle.green)
    async def next_note(self, interaction: Interaction, button: ui.Button):
        if self.page_number >= (len(self.notes) - 1):
            self.page_number = 0
        else:
            self.page_number += 1
        embed = await self.embed_factory.create_notes_embed(self.notes[self.page_number])
        
        button.label = f"View Note {self.page_number}/{len(self.notes)}"
        self.previous_note.label = f"View Note {self.page_number - 1}/{len(self.notes)}"
        
        await interaction.response.edit_message(embed=embed, view=self)