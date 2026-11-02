#!/usr/bin/env python3
"""
Spell Master - 2D Side-View Fantasy Game with CV integration API
Entry point file.
"""
import utils.clients
import utils.http_session
import utils.transport
import utils.session
from game import Game

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
