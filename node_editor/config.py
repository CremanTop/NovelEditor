import os
import sys
from typing import Optional, NoReturn

Tuple2D = tuple[float, float]


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


class Config:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> NoReturn:
        self.screen_size: Tuple2D = (1280, 720)
        self._path: Optional[str] = ''
        self._game_file: Optional[str] = None

    def set_root(self, path: str) -> NoReturn:

        def _fing_json() -> str:
            for file in os.listdir(path):
                if file.endswith('.json'):
                    return file

        self._path = path
        self._game_file = _fing_json()

        print(self._path, self._game_file)

    def get_root(self) -> str:
        return self._path

    def get_file_game(self) -> str:
        return f'{self._path}/{self._game_file}'

    def get_dir_upload(self) -> str:
        return f'{self._path}/images/upload'

    def get_dir_mini(self) -> str:
        return f'{self._path}/images/temp_mini'
