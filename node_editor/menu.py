import os
from typing import NoReturn, Final

import pygame_gui
import pygame as pg
from pygame import Event
from pygame_gui.elements import UIButton

from app import Screen
from config import Config, resource_path

config: Final[Config] = Config()


def create_game_dir(path: str) -> NoReturn:
    if not os.path.isdir(os.path.join(path, 'images')):
        os.makedirs(os.path.join(path, 'images/temp_mini'))
        os.makedirs(os.path.join(path, 'images/upload'))
    with open(os.path.join(path, 'game.json'), 'w') as file:
        file.write('{}')
    config.set_root(path)


class MenuScreen(Screen):
    def __init__(self) -> NoReturn:
        super().__init__()
        self.ui_manager: pygame_gui.UIManager = pygame_gui.UIManager(self.surface.get_size(), resource_path('theme.json'))

        buttons: dict[str, tuple[int, int, int, int]] = {
            'Создать новую игру': (20, 60, 250, 30),
            'Открыть файл игры в редакторе': (20, 90, 250, 30),
            'Запустить игру из файла': (20, 120, 250, 30),
        }

        def _create_button(name: str) -> UIButton:
            return UIButton(relative_rect=pg.Rect(*buttons[name]),
                            text=name,
                            manager=self.ui_manager,
                            anchors={
                                'left': 'left',
                                'right': 'right',
                                'top': 'top',
                                'bottom': 'bottom'})

        self.button_create_game: UIButton = _create_button('Создать новую игру')
        self.button_open_game: UIButton = _create_button('Открыть файл игры в редакторе')
        self.button_start_game: UIButton = _create_button('Запустить игру из файла')

        self.input_path = pygame_gui.elements.UITextEntryLine(relative_rect=pg.Rect(20, 155, 250, 30),
                                                              initial_text=config.get_root(),
                                                              manager=self.ui_manager,
                                                              anchors={
                                                                  'left': 'left',
                                                                  'right': 'right',
                                                                  'top': 'top',
                                                                  'bottom': 'bottom'})

    def update(self) -> NoReturn:
        self.surface.fill('white')

        self.ui_manager.update(1.371)
        self.ui_manager.draw_ui(self.surface)
        pg.display.update()

    def control(self, events: list[Event]) -> bool | str:
        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.button_open_game:
                        return 'editor'
                    case self.button_start_game:
                        return 'start'
                    case self.button_create_game:
                        create_game_dir(config.get_root())
                        return 'editor'
            if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                if event.ui_element == self.input_path:
                    path = event.text.replace('\\', '/')
                    config.set_root(path)
            self.ui_manager.process_events(event)

        if len(events) > 0:
            return True
        return False
