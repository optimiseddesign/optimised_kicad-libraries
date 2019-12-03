from pcbnew import *
#import os

class SimplePlugin(ActionPlugin):
    def defaults(self):
        self.name = "Delete GND Tracks"
        self.category = "Helper Program"
        self.description = "A plugin to delete all tracks which have the Net name 'GND'."
        self.show_toolbar_button = False # Optional, defaults to False

    def Run(self):
        board = GetBoard()
        for track in board.GetTracks():
            if track.GetNetname() == 'GND':
                board.Delete(track)
                # FAILS - also deletes all connected VIAS , possibly try using board.GetItems() to work out if 'Segment' and delete if segment

SimplePlugin().register() # Instantiate and register to Pcbnew