import sys
from enum import Enum, auto
from typing import NoReturn, Union, Final

import pygame as pg
from pygame import Event

from app import Screen
from config import Config
from editor import Editor
from game import GameScreen
from menu import MenuScreen

config: Final[Config] = Config()


class AppState(Enum):
    editor = auto()
    game = auto()
    menu = auto()


class App:
    def __init__(self) -> NoReturn:
        pg.display.set_caption('Novel Application')
        self.screen: Screen = None
        self.state: AppState = None
        self.path_file: str = config.get_root()
        self.set_screen(AppState.menu)

    def set_screen(self, screen: AppState) -> NoReturn:
        if self.state is AppState.editor:
            self.screen.close_editor()

        self.state: AppState = screen

        match screen:
            case AppState.editor:
                self.screen = Editor.deserialize()
            case AppState.game:
                self.screen = GameScreen()
            case AppState.menu:
                self.screen = MenuScreen()
        self.screen.update()

    def run(self):
        while True:
            if pg.event.get(eventtype=(pg.QUIT, pg.WINDOWCLOSE)):
                if self.state is AppState.editor:
                    self.screen.close_editor()

                pg.quit()
                sys.exit()

            events: list[Event] = pg.event.get()

            for event in events:
                if event.type == pg.KEYDOWN:
                    match event.key:
                        # case pg.K_1:
                        #     self.set_screen(AppState.editor)
                        # case pg.K_2:
                        #     self.set_screen(AppState.game)
                        case pg.K_3:
                            self.set_screen(AppState.menu)
                if event.type == pg.VIDEORESIZE:
                    config.screen_size = self.screen.surface.get_size()

            control: Union[bool, str] = self.screen.control(events)
            if isinstance(control, str):
                match control:
                    case 'start':
                        self.set_screen(AppState.game)
                    case 'editor':
                        self.set_screen(AppState.editor)
                    case 'menu':
                        self.set_screen(AppState.menu)

            elif control:
                self.screen.update()


if __name__ == '__main__':
    app: App = App()
    app.run()
