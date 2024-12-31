from abc import abstractmethod, ABC
from typing import NoReturn, Final

import pygame as pg
from pygame import Surface, Rect, Color, Event

from config import Config

config: Final[Config] = Config()


class Screen(ABC):
    def __init__(self) -> NoReturn:
        self.surface: Surface = pg.display.set_mode(config.screen_size, pg.RESIZABLE)

    @abstractmethod
    def update(self) -> NoReturn:
        pass

    @abstractmethod
    def control(self, events: list[Event]) -> bool:
        pass


class ScreenLoading(Screen):
    def control(self, events: list[Event]) -> bool:
        pass

    def __init__(self):
        super().__init__()
        self.size: int = 100
        self.angle: int = 0
        self.rect: Rect = pg.Rect(self.surface.get_width() // 2 - self.size // 2, self.surface.get_height() // 2 - self.size // 2, self.size, self.size)

    def update(self) -> NoReturn:
        self.surface.fill(Color(0, 0, 0))
        fon = Surface((self.size, self.size)).convert_alpha()
        fon.fill(Color(255, 255, 255))
        fon = pg.transform.rotate(fon, self.angle)

        self.surface.blit(fon, fon.get_rect(center=(self.surface.get_width() // 2, self.surface.get_height() // 2)))

        self.angle = (self.angle - 1) % 360
        pg.display.update()
        clock = pg.time.Clock()
        clock.tick(120)