from typing import NoReturn, Final

import pygame
import pygame_gui
from pygame import Surface, Event

from pygame_gui.elements import UIButton, UIImage
from pygame_gui.windows import UIFileDialog
from pygame_gui.core.utility import create_resource_path

from app import Screen
from config import Config, resource_path

config: Final[Config] = Config()


class ImageLoadApp(Screen):
    def update(self) -> NoReturn:
        self.surface.fill(self.ui_manager.ui_theme.get_colour('dark_bg'))
        time_delta = self.clock.tick(60) / 1000.0
        self.ui_manager.update(time_delta)
        self.ui_manager.draw_ui(self.surface)
        pygame.display.update()

    @staticmethod
    def get_path(raw_path: str) -> str:
        path = raw_path.replace('\\', '/')
        return f'{config.get_dir_upload()}/{path[path.rfind("/"): path.find(".")]}.jpeg'

    def control(self, events: list[Event]) -> bool:
        if len(events) <= 0:
            return False

        for event in events:
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.load_button:
                        self.file_dialog = UIFileDialog(pygame.Rect(160, 50, 440, 500),
                                                        self.ui_manager,
                                                        window_title='Load Image...',
                                                        initial_file_path=config.get_dir_upload(),
                                                        allow_picking_directories=True,
                                                        allow_existing_files_only=True,
                                                        allowed_suffixes={""})
                        self.load_button.disable()

                    case self.accept_button:
                        self.node.replace_image(self.file_path[self.file_path.rfind("/") + 1:])
                        self.editor.load_input = False

            if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                if self.display_loaded_image is not None:
                    self.display_loaded_image.kill()

                try:
                    image_path = create_resource_path(event.text)
                    loaded_image = pygame.image.load(image_path).convert_alpha()
                    self.file_path = self.get_path(event.text)
                    pygame.image.save(loaded_image, self.file_path)
                    image_rect = loaded_image.get_rect()
                    aspect_ratio = image_rect.width / image_rect.height
                    need_to_scale = False
                    if image_rect.width > self.max_image_display_dimensions[0]:
                        image_rect.width = self.max_image_display_dimensions[0]
                        image_rect.height = int(image_rect.width / aspect_ratio)
                        need_to_scale = True

                    if image_rect.height > self.max_image_display_dimensions[1]:
                        image_rect.height = self.max_image_display_dimensions[1]
                        image_rect.width = int(image_rect.height * aspect_ratio)
                        need_to_scale = True

                    if need_to_scale:
                        loaded_image = pygame.transform.smoothscale(loaded_image,
                                                                    image_rect.size)

                    image_rect.center = (self.surface.get_size()[0] / 2, self.surface.get_size()[1] / 2)

                    self.display_loaded_image = UIImage(relative_rect=image_rect,
                                                        image_surface=loaded_image,
                                                        manager=self.ui_manager)
                    self.accept_button.enable()

                except pygame.error as er:
                    print('Непонятная ошибка')

            if event.type == pygame_gui.UI_WINDOW_CLOSE and event.ui_element == self.file_dialog:
                self.load_button.enable()
                self.file_dialog = None

            self.ui_manager.process_events(event)
        return True

    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.node = None
        self.ui_manager = pygame_gui.UIManager(self.surface.get_size(), resource_path('theme.json'))
        self.surface.fill(self.ui_manager.ui_theme.get_colour('dark_bg'))
        self.load_button = UIButton(relative_rect=pygame.Rect(-200, -60, 180, 30),
                                    text='Загрузить изображение',
                                    manager=self.ui_manager,
                                    anchors={'left': 'right',
                                             'right': 'right',
                                             'top': 'bottom',
                                             'bottom': 'bottom'})

        self.accept_button = UIButton(relative_rect=pygame.Rect(20, -60, 180, 30),
                                      text='Подтвердить',
                                      manager=self.ui_manager,
                                      anchors={
                                          'left': 'left',
                                          'right': 'right',
                                          'top': 'bottom',
                                          'bottom': 'bottom'})

        self.accept_button.disable()
        self.file_dialog = None
        self.file_path: str = ''

        # scale images, if necessary so that their largest dimension does not exceed these values
        self.max_image_display_dimensions = (400, 400)
        self.display_loaded_image = None

        self.clock = pygame.time.Clock()


if __name__ == "__main__":
    app = ImageLoadApp()
