import glob
import json
import os
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import NoReturn, Optional, Self, Any, Union, Final, TypeVar

import pygame as pg
import pygame_gui
from pygame import Surface, Color, Rect, Event
from pygame import gfxdraw
from pygame_gui.elements import UITextEntryBox, UIButton, UISelectionList

from ImageLoad import ImageLoadApp
from app import Screen
from config import Config, Tuple2D, resource_path

config: Final[Config] = Config()

pg.font.init()


def create_miniature(in_path: str, size: Tuple2D = (120, 67)) -> None:
    image = pg.image.load(in_path)
    scale = pg.transform.smoothscale(image, size)
    fon = Surface(size).convert_alpha()
    fon.fill(Color(255, 255, 255, 100))
    scale.blit(fon, fon.get_rect())
    pg.image.save(scale, f'{config.get_dir_mini()}/{in_path[in_path.rfind("/"): in_path.find(".")]}.jpeg')


def draw_circle(surface: Surface, x: int, y: int, radius: int, color: Color) -> NoReturn:
    gfxdraw.aacircle(surface, x, y, radius, color)
    gfxdraw.filled_circle(surface, x, y, radius, color)


def draw_line(surface: Surface, x1: int, y1: int, x2: int, y2: int, color: Color) -> NoReturn:
    gfxdraw.line(surface, x1, y1, x2, y2, color)


class ISerialisable(ABC):
    @abstractmethod
    def __my_dict__(self) -> dict[str, Any]:
        pass


class Graphic(ISerialisable, ABC):
    def __init__(self, color: Color, position: Tuple2D) -> NoReturn:
        self.color: Color = color
        self.pos: Tuple2D = position

    @abstractmethod
    def draw(self, surface: Surface) -> NoReturn:
        pass

    def __my_dict__(self) -> dict[str, Any]:
        return {
            'color': (self.color.r, self.color.g, self.color.b, self.color.a),
            'position': self.pos
        }


class Figure(Graphic, ABC):
    def __init__(self, color: Color, position: Tuple2D):
        super().__init__(color, position)
        self.geom: Any = None

    def set_pos(self, position: Tuple2D) -> NoReturn:
        self.pos = position

    def is_point_below(self, point: Tuple2D) -> bool:
        return self.geom.collidepoint(*point)

    def get_center(self) -> Tuple2D:
        pass


class Connector(Figure):
    def __init__(self, node, is_receiver: bool) -> NoReturn:
        super().__init__(Color(0, 0, 0), (0, 0))
        self.is_receiver: bool = is_receiver
        self.node: Node = node
        self.size: int = 20
        self.geom: Rect = pg.Rect(self.pos[0], self.pos[1], self.size, self.size)

    def set_pos(self, position: Tuple2D) -> NoReturn:
        self.pos = (position[0] - self.size / 2, position[1])
        self.geom = pg.Rect(self.pos[0], self.pos[1], self.size, self.size)

    def draw(self, surface: Surface) -> NoReturn:
        pg.draw.rect(surface, self.color, self.geom)

    def get_center(self) -> Tuple2D:
        return self.pos[0] + self.size // 2, self.pos[1] + self.size // 2

    def __my_dict__(self) -> dict[str, Any]:
        _dict = super().__my_dict__()
        _dict.update({
            'size': self.size
        })
        return _dict


class IText(ISerialisable, ABC):
    def __init__(self, text: str = '') -> NoReturn:
        self.text: str = text

    def set_text(self, text: str) -> NoReturn:
        self.text = text

    def __my_dict__(self) -> dict[str, Any]:
        return {
            'text': self.text
        }

    def render_text(self) -> Surface:
        text: str = self.text if len(self.text) <= 12 else self.text[:10] + '...'
        f1 = pg.font.SysFont('consolas', 16)

        return f1.render(text, True, (0, 0, 0))


Text = TypeVar("Text", bound=IText)


class Node(Figure, ABC):
    def __init__(self, position: Tuple2D, color: Color = Color(255, 255, 255)) -> NoReturn:
        super().__init__(color, position)
        self.connector1: Connector = Connector(self, True)
        self.connector2: Connector = Connector(self, False)
        self.choosen: bool = False
        self.initial: bool = False
        # self.set_pos(position)

    def __my_dict__(self) -> dict[str, Any]:
        _dict = super().__my_dict__()
        _dict.update({
            'connector1': self.connector1.__my_dict__(),
            'connector2': self.connector2.__my_dict__() if self.connector2 is not None else None
        })
        return _dict

    def get_connector(self, pos: Tuple2D) -> Connector | bool:
        if self.connector1.is_point_below(pos):
            return self.connector1
        if self.connector2.is_point_below(pos):
            return self.connector2
        return False


class CircleNode(Node):
    def __init__(self, position: Tuple2D, radius: float, color: Color = Color(255, 255, 255)) -> NoReturn:
        super().__init__(position, color)
        self.radius: float = radius
        self.set_pos(position)

    def draw(self, surface: Surface) -> NoReturn:
        # pg.draw.circle(surface, self.color, self.pos, self.radius)
        self.connector1.draw(surface)
        self.connector2.draw(surface)
        draw_circle(surface, int(self.pos[0]), int(self.pos[1]), int(self.radius), self.color)
        if self.choosen:
            gfxdraw.aacircle(surface, int(self.pos[0]), int(self.pos[1]), int(self.radius), Color(255, 0, 0))

    def set_pos(self, position: Tuple2D) -> NoReturn:
        super().set_pos(position)
        self.connector1.set_pos((position[0], position[1] - self.radius - self.connector1.size + 1))
        self.connector2.set_pos((position[0], position[1] + self.radius))

    def is_point_below(self, point: Tuple2D) -> bool:
        return ((self.pos[0] - point[0]) ** 2 + (self.pos[1] - point[1]) ** 2) ** 0.5 <= self.radius

    def get_center(self) -> Tuple2D:
        return self.pos

    def __my_dict__(self) -> dict[str, Any]:
        _dict = super().__my_dict__()
        _dict.update({
            'type': 1,
            'radius': self.radius
        })
        return _dict


class I2Sized(ISerialisable, ABC):
    def __init__(self, size: Tuple2D = (120, 67)) -> NoReturn:
        self.size: Tuple2D = size

    def set_size(self, size: Tuple2D) -> NoReturn:
        self.size = size

    def __my_dict__(self) -> dict[str, Any]:
        return {
            'size': self.size
        }


Node2Sized = TypeVar("Node2Sized", bound=[Node, I2Sized])


class ImageNode(Node, IText, I2Sized):
    def __init__(self, position: Tuple2D, color: Color = Color(255, 255, 255), path_image: str = None,
                 size: Tuple2D = (120, 67), centering: bool = True, is_mini_should: bool = True) -> NoReturn:
        Node.__init__(self, position, color)
        IText.__init__(self)
        I2Sized.__init__(self, size)
        self.geom: Rect = pg.Rect(self.pos[0] - 2, self.pos[1] - 2, self.size[0] + 4, self.size[1] + 4)
        self.set_pos(position)
        if centering:
            self.set_pos(self.get_center())

        self.image_mini: Surface = None
        self.path_image: str = path_image

        if self.path_image is not None:
            if os.path.exists(self.path_image):
                self.replace_image(path_image, is_mini_should)

    def draw(self, surface: Surface) -> NoReturn:
        color: Color = self.color
        if self.choosen:
            color = Color(255, 0, 0)
        pg.draw.rect(surface, color, self.geom)
        if self.image_mini is not None:
            surface.blit(self.image_mini, self.image_mini.get_rect(
                center=(self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1] // 2)))

        text: Surface = self.render_text()
        surface.blit(text, text.get_rect(center=(self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1] - 10)))

        self.connector1.draw(surface)
        self.connector2.draw(surface)
        if self.initial:
            pg.draw.polygon(surface, color, ((self.pos[0] - 20, self.pos[1] + self.size[1] // 2 - 20),
                                             (self.pos[0] - 20, self.pos[1] + self.size[1] // 2 + 20),
                                             (self.pos[0], self.pos[1] + self.size[1] // 2)))

    def set_pos(self, position: Tuple2D) -> NoReturn:
        super().set_pos(position)
        self.geom = pg.Rect(self.pos[0] - 2, self.pos[1] - 2, self.size[0] + 4, self.size[1] + 4)
        self.connector1.set_pos((position[0] + self.size[0] // 2, position[1] - self.connector1.size))
        self.connector2.set_pos((position[0] + self.size[0] // 2, position[1] + self.size[1]))

    def get_center(self) -> Tuple2D:
        return self.pos[0] - self.size[0] // 2, self.pos[1] - self.size[1] // 2

    def __my_dict__(self) -> dict[str, Any]:
        _dict = Node.__my_dict__(self)
        _dict.update(IText.__my_dict__(self))
        _dict.update(I2Sized.__my_dict__(self))
        _dict.update({
            'type': 2,
            'image_path': self.path_image
        })
        return _dict

    def replace_image(self, path_image: str, is_mini_should: bool = True) -> NoReturn:
        path_mini: str = f'{config.get_dir_mini()}/{path_image[path_image.rfind("/"): path_image.find(".")]}.jpeg'
        if is_mini_should:
            if not os.path.exists(path_mini):
                create_miniature(path_image, self.size)

            self.image_mini: Surface = pg.image.load(path_mini).convert()
        self.path_image: str = path_image


# class InputBox(Figure):
#     def __init__(self, color: Color, position: Tuple2D, node: Node) -> NoReturn:
#         super().__init__(color, position)
#         self.node: Node = node
#         self.geom: Rect = Rect(self.pos[0], self.pos[1], 140, 32)
#         self.text: str = ''
#         self.active: bool = False
#
#     def draw(self, surface: Surface) -> NoReturn:
#         color: Color = self.color
#         if self.active:
#             color = Color(self.color.r + 50, self.color.g + 50, self.color.b + 50)
#         pg.draw.rect(surface, color, self.geom)
#
#         base_font = pg.font.SysFont('consolas', 32)
#         text_surface = base_font.render(self.text, True, (255, 255, 255))
#         surface.blit(text_surface, (self.geom.x + 5, self.geom.y + 5))
#         self.geom.w = max(100, text_surface.get_width() + 10)
#
#     def __dict__(self) -> dict[str, Any]:
#         pass

class VarNode(Node, IText, I2Sized):
    def __init__(self, position: Tuple2D, color: Color = Color(255, 255, 255), size: Tuple2D = (120, 67),
                 centering: bool = True) -> NoReturn:
        Node.__init__(self, position, color)
        IText.__init__(self)
        I2Sized.__init__(self, size)
        self.geom: Rect = pg.Rect(self.pos[0] - 4, self.pos[1] - 4, self.size[0] + 8, self.size[1] + 8)
        self.set_pos(position)
        if centering:
            self.set_pos(self.get_center())

    def draw(self, surface: Surface) -> NoReturn:
        color: Color = self.color
        if self.choosen:
            color = Color(255, 0, 0)
        pg.draw.rect(surface, color, self.geom)
        pg.draw.rect(surface, Color(255, 255, 200), pg.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]))

        text: Surface = self.render_text()
        surface.blit(text, text.get_rect(center=(self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1] // 2)))

        self.connector1.draw(surface)
        self.connector2.draw(surface)
        if self.initial:
            pg.draw.polygon(surface, color, ((self.pos[0] - 20, self.pos[1] + self.size[1] // 2 - 20),
                                             (self.pos[0] - 20, self.pos[1] + self.size[1] // 2 + 20),
                                             (self.pos[0], self.pos[1] + self.size[1] // 2)))

    def set_pos(self, position: Tuple2D) -> NoReturn:
        super().set_pos(position)
        self.geom = pg.Rect(self.pos[0] - 2, self.pos[1] - 2, self.size[0] + 4, self.size[1] + 4)
        self.connector1.set_pos((position[0] + self.size[0] // 2, position[1] - self.connector1.size))
        self.connector2.set_pos((position[0] + self.size[0] // 2, position[1] + self.size[1]))

    def get_center(self) -> Tuple2D:
        return self.pos[0] - self.size[0] // 2, self.pos[1] - self.size[1] // 2

    def __my_dict__(self) -> dict[str, Any]:
        _dict = Node.__my_dict__(self)
        _dict.update(IText.__my_dict__(self))
        _dict.update(I2Sized.__my_dict__(self))
        _dict.update({
            'type': 4
        })
        return _dict


class InputBox:
    def __init__(self, position: Tuple2D, manager: pygame_gui.UIManager, node: Node) -> NoReturn:
        self.node: Node = node
        self.active: bool = False
        self.manager: pygame_gui.UIManager = manager
        self.entry: UITextEntryBox = UITextEntryBox(pg.Rect(position[0], position[1] - 100, 400, 300), manager=self.manager)
        self.button_ok: UIButton = UIButton(relative_rect=pg.Rect(position[0] + 405, position[1], 100, 100),
                                            text='Ок',
                                            manager=self.manager,
                                            anchors={
                                                'left': 'left',
                                                'right': 'right',
                                                'top': 'top',
                                                'bottom': 'bottom'})
        self.button_cancel: UIButton = UIButton(relative_rect=pg.Rect(position[0] + 510, position[1], 100, 100),
                                                text='Отмена',
                                                manager=self.manager,
                                                anchors={
                                                    'left': 'left',
                                                    'right': 'right',
                                                    'top': 'top',
                                                    'bottom': 'bottom'})

    def activate(self, node: Text) -> NoReturn:
        self.entry.show()
        self.button_ok.show()
        self.button_cancel.show()
        self.set_node(node)

    def deactivate(self) -> NoReturn:
        self.entry.hide()
        self.button_ok.hide()
        self.button_cancel.hide()

    def set_node(self, node: Text) -> NoReturn:
        self.node = node
        self.entry.set_text(node.text)


class VarBox(InputBox):
    def __init__(self, position: Tuple2D, manager: pygame_gui.UIManager, node: Node) -> NoReturn:
        InputBox.__init__(self, position, manager, node)

        self.entry.kill()
        self.entry: UITextEntryBox = UITextEntryBox(pg.Rect(position[0], position[1], 200, 100), manager=self.manager)
        self.mode: UISelectionList = UISelectionList(pg.Rect(position[0] + 200, position[1], 100, 100),
                                                     item_list=['Установить', 'Увеличить', 'Уменьшить'],
                                                     default_selection='Установить',
                                                     manager=self.manager)
        self.input_value: UITextEntryBox = UITextEntryBox(pg.Rect(position[0] + 300, position[1], 100, 100), manager=self.manager)

    def deactivate(self) -> NoReturn:
        InputBox.deactivate(self)
        self.mode.hide()
        self.input_value.hide()

    def activate(self, node: Text) -> NoReturn:
        InputBox.activate(self, node)
        self.mode.show()
        self.input_value.show()

    def set_node(self, node: Text) -> NoReturn:
        self.node = node
        if len(node.text) < 1:
            return
        self.entry.set_text(node.text.split()[0])
        self.input_value.set_text(node.text.split()[-1])
        self.mode._default_selection = 'Установить' if node.text.split()[1] == '=' else 'Увеличить' if node.text.split()[1] == '+=' else 'Уменьшить'
        self.mode._set_default_selection()


class EnumAction(Enum):
    set_main = 'Начальная'
    delete = 'Удалить'
    replace_text = 'Изменить текст'
    edit_var = 'Изменить переменную'
    import_image = 'Загрузить изображение'
    delete_answer = 'Удалить ответ'
    add_image_node = 'Добавить экран'
    add_answer_node = 'Добавить ответы'
    add_var_node = 'Добавить переменную'


class ActionBar(Figure, I2Sized):
    def __init__(self, color: Color, position: Tuple2D, node: Node) -> NoReturn:
        Figure.__init__(self, color, position)
        I2Sized.__init__(self, (180, 60))
        self.node: Node | None = node
        self.geom: Rect = pg.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
        self.task_selected: int = -1

    def _get_tasks(self) -> list[EnumAction]:
        if self.node is None:
            return [EnumAction.add_image_node, EnumAction.add_answer_node, EnumAction.add_var_node]
        tasks: list[EnumAction] = [EnumAction.delete]
        if isinstance(self.node, IText):
            tasks.append(EnumAction.replace_text)
        if isinstance(self.node, Node):
            tasks.append(EnumAction.set_main)
        if isinstance(self.node, ImageNode):
            tasks.append(EnumAction.import_image)
        if isinstance(self.node, Answer):
            tasks.append(EnumAction.delete_answer)
        if isinstance(self.node, VarNode):
            tasks.append(EnumAction.edit_var)
            tasks.remove(EnumAction.replace_text)
        return tasks

    def get_click_task(self, pos: Tuple2D) -> Union[EnumAction, False]:
        y: float = self.pos[1]
        tasks: list[EnumAction] = self._get_tasks()
        for task in tasks:
            self.geom.y = y
            if self.is_point_below(pos):
                return task
            y += self.size[1] + 1
        return False

    def backlight(self, pos: Tuple2D):
        task: EnumAction | bool = self.get_click_task(pos)
        if task:
            self.task_selected = self._get_tasks().index(task)
        else:
            self.task_selected = -1

    def draw(self, surface: Surface) -> NoReturn:
        y: float = self.pos[1]
        for task in self._get_tasks():
            color_button: Color = self.color
            color_text: Color = Color(255, 255, 255)
            if self._get_tasks().index(task) == self.task_selected:
                color_button = Color(0, 128, 128)

            self.geom.y = y
            pg.draw.rect(surface, color_button, self.geom)

            f1 = pg.font.SysFont('calibri', 16, bold=True)
            text1 = f1.render(str(task.value), True, color_text)
            surface.blit(text1, text1.get_rect(center=(self.pos[0] + self.size[0] // 2, y + self.size[1] // 2)))

            y += self.size[1] + 1

    def __my_dict__(self) -> dict[str, Any]:
        pass


class Answer(Figure, IText, I2Sized):
    def __init__(self, position: Tuple2D, node, color: Color = Color(128, 128, 128)):
        Figure.__init__(self, color, position)
        IText.__init__(self)
        I2Sized.__init__(self, (node.size[0], node.size[0] / 3))
        self.node: ChoosenNode = node
        self.geom: Rect = pg.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
        self.connector2: Connector = Connector(self, False)

        self.set_pos(position)

    def set_size(self, size: Tuple2D) -> NoReturn:
        self.size: size
        self.geom: Rect = pg.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
        self.set_pos(self.pos)

    def set_pos(self, position: Tuple2D) -> NoReturn:
        super().set_pos(position)
        self.geom: Rect = pg.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
        self.connector2.set_pos((position[0] + self.size[0] + self.connector2.size // 2,
                                 position[1] + self.size[1] // 2 - self.connector2.size // 2))

    def draw(self, surface: Surface) -> NoReturn:
        pg.draw.rect(surface, self.color, self.geom)
        self.connector2.draw(surface)

        text: Surface = self.render_text()
        surface.blit(text, text.get_rect(center=(self.pos[0] + self.size[0] // 2, self.pos[1] + self.size[1] // 2)))

    def __my_dict__(self) -> dict[str, Any]:
        _dict = Figure.__my_dict__(self)
        _dict.update(IText.__my_dict__(self))
        _dict.update({
            'size': self.size,
            'connector': self.connector2.__my_dict__()
        })
        return _dict


class ButtonAdd(Connector):
    def __init__(self, node):
        super().__init__(node, True)
        self.size = 30
        self.color = Color(0, 150, 0)

    def draw(self, surface: Surface) -> NoReturn:
        super().draw(surface)
        pg.draw.rect(surface, Color(200, 200, 200),
                     pg.Rect(self.pos[0] + self.size // 2 - 2, self.pos[1] + self.size // 2 - 12, 4, 24))
        pg.draw.rect(surface, Color(200, 200, 200),
                     pg.Rect(self.pos[0] + self.size // 2 - 12, self.pos[1] + self.size // 2 - 2, 24, 4))


class ChoosenNode(Node, I2Sized):
    def __init__(self, position: Tuple2D, color: Color = Color(100, 100, 255), create_answer: bool = True) -> NoReturn:
        Node.__init__(self, position, color)
        I2Sized.__init__(self, (120, 0))
        self.geom: Rect = pg.Rect(self.pos[0], self.pos[1], 0, 0)
        self.connector2 = None
        self.button_add: ButtonAdd = ButtonAdd(self)

        self.answers: list[Answer] = []

        if create_answer:
            self.add_answer()

        self.set_pos(position)

    def add_answer(self) -> NoReturn:
        size = (self.size[0], self.size[0] / 3)
        pos: Tuple2D = (self.pos[0], self.pos[1] + size[1] * len(self.answers) + len(self.answers))
        self.answers.append(Answer(pos, self))

        self.set_size((self.size[0], self.size[1] + size[1] + 1))

    def remove_answer(self, answer: Answer) -> NoReturn:
        self.answers.remove(answer)
        self.set_size((self.size[0], self.size[1] - answer.size[1] - 1))

    def set_pos(self, position: Tuple2D) -> NoReturn:
        super().set_pos(position)
        self.geom = pg.Rect(self.pos[0] - 2, self.pos[1] - 2, self.size[0] + 4, self.size[1] + 4)
        self.connector1.set_pos((position[0] + self.size[0] // 2, position[1] - self.connector1.size))
        self.button_add.set_pos((position[0] + self.size[0] // 2, position[1] + self.size[1] + 2))

        i = 0
        for answer in self.answers:
            shift: float = self.answers.index(answer) * self.size[0] / 3
            answer.set_pos((position[0], position[1] + shift + i))
            i += 1

    def set_size(self, size: Tuple2D) -> NoReturn:
        self.size = size
        self.geom = pg.Rect(self.pos[0] - 2, self.pos[1] - 2, self.size[0] + 4, self.size[1] + 4)
        for ans in self.answers:
            ans.set_size((self.size[0], self.size[0] / 3))

        self.set_pos(self.pos)

    def draw(self, surface: Surface) -> NoReturn:
        color: Color = self.color
        if self.choosen:
            color = Color(255, 0, 0)
        pg.draw.rect(surface, color, self.geom)
        self.connector1.draw(surface)
        self.button_add.draw(surface)
        for answer in self.answers:
            answer.draw(surface)

    def get_connector(self, pos: Tuple2D) -> Connector | bool:
        if self.connector1.is_point_below(pos):
            return self.connector1
        for answer in self.answers:
            if answer.connector2.is_point_below(pos):
                return answer.connector2
        return False

    def __my_dict__(self) -> dict[str, Any]:
        _dict = Node.__my_dict__(self)
        _dict.update(I2Sized.__my_dict__(self))
        _dict.update({
            'type': 3,
            'answers': {hash(ans): ans.__my_dict__() for ans in self.answers}
        })
        return _dict


class Arrow(Graphic):
    def __init__(self, first: Connector, second: Connector, color: Color = Color(0, 0, 0)) -> NoReturn:
        super().__init__(color, first.pos)
        self.start: Connector = first
        self.end: Connector | Tuple2D = second

    def __eq__(self, other: Self) -> bool:
        return (self.start is other.start and (self.end == other.end or self.end is other.end)) or \
               (self.start is other.end and self.end is other.start)

    def contain_node(self, node: Node) -> bool:
        result: bool = self.start.node is node or self.end.node is node
        if isinstance(node, Answer):
            result = result or any(self.start.node is a for a in node.node.answers) or any(self.end.node is a for a in node.node.answers) or self.start.node is node.node or self.end.node is node.node

        return result

    def draw(self, surface: Surface) -> NoReturn:
        # draw_line(surface, int(self.start.pos[0]), int(self.start.pos[1]), int(self.end.pos[0] if isinstance(self.end, Node) else self.end[0]), int(self.end.pos[1] if isinstance(self.end, Node) else self.end[1]), self.color)
        pg.draw.line(surface, self.color, self.start.get_center(),
                     self.end.get_center() if isinstance(self.end, Connector) else self.end, width=2)

    def __my_dict__(self) -> dict[str, Any]:
        _dict = super().__my_dict__()
        _dict.update({
            'start': str(hash(self.start.node)),
            'end': str(hash(self.end.node))
        })
        return _dict


class Editor(Screen):
    def __init__(self) -> NoReturn:
        super().__init__()
        self.nodes: list[Node2Sized] = []
        self.arrows: list[Arrow] = []
        self.choosen_nodes: dict[Node2Sized, bool] = {}
        self.choosen_arrow: Optional[Arrow] = None
        self.action_bar: Optional[ActionBar] = None
        self.action_bar_focus: bool = False

        self.image_app: ImageLoadApp = ImageLoadApp(self)
        self.load_input: bool = False

        self.ui_manager = pygame_gui.UIManager(self.surface.get_size(), resource_path('theme.json'))
        self.input_box: Optional[InputBox] = InputBox(
            (self.surface.get_width() / 2 - 200, self.surface.get_height() / 2 - 50), self.ui_manager, None)
        self.var_box: Optional[VarBox] = VarBox(
            (self.surface.get_width() / 2 - 200, self.surface.get_height() / 2 - 50), self.ui_manager, None)

        self.input_box.deactivate()
        self.var_box.deactivate()

        self.button_menu: UIButton = UIButton(relative_rect=pg.Rect(0, 0, 180, 30),
                                              text='Меню',
                                              manager=self.ui_manager,
                                              anchors={
                                                  'left': 'left',
                                                  'right': 'right',
                                                  'top': 'top',
                                                  'bottom': 'bottom'})

    def delete_node(self, node: Node) -> NoReturn:
        self.arrows = list(filter(lambda arrow: not arrow.contain_node(node), self.arrows))
        if isinstance(node, Answer):
            node = node.node
        if node in self.choosen_nodes:
            self.remove_choosen_node(node)
        self.nodes.remove(node)

    def set_main_node(self, node: Node) -> NoReturn:
        if node.initial:
            node.initial = False
            return
        for i in self.nodes:
            i.initial = False
        node.initial = True

    def add_choosen_node(self, node: Node, mode: bool = False) -> NoReturn:
        if node in self.choosen_nodes:
            return
        self.choosen_nodes[node] = mode
        node.choosen = True

    def remove_choosen_node(self, node: Node) -> NoReturn:
        self.choosen_nodes.pop(node)
        node.choosen = False

    def activate_action_bar(self, pos: Tuple2D, node: Node = None) -> NoReturn:
        if isinstance(node, ChoosenNode):
            for answer in node.answers:
                if answer.is_point_below(pos):
                    node = answer
                    break
        self.action_bar = ActionBar(Color(128, 128, 128), pos, node)
        self.action_bar_focus = True

    def action_bar_handler(self, pos: Tuple2D) -> NoReturn:
        task: EnumAction | bool = self.action_bar.get_click_task(pos)
        if task:
            match task:
                case EnumAction.set_main:
                    self.set_main_node(self.action_bar.node)
                case EnumAction.delete:
                    self.delete_node(self.action_bar.node)
                case EnumAction.replace_text:
                    self.input_box.activate(self.action_bar.node)
                case EnumAction.edit_var:
                    self.var_box.activate(self.action_bar.node)
                case EnumAction.import_image:
                    self.load_input = True
                    self.image_app.node = self.action_bar.node
                    # self.image_app.run()
                case EnumAction.delete_answer:
                    self.action_bar.node.node.remove_answer(self.action_bar.node)
                    self.arrows = list(filter(lambda arrow: arrow.start is not self.action_bar.node.connector2, self.arrows))
                case EnumAction.add_image_node:
                    self.nodes.append(ImageNode(pos, Color(100, 100, 255)))
                case EnumAction.add_answer_node:
                    self.nodes.append(ChoosenNode(pos))
                case EnumAction.add_var_node:
                    self.nodes.append(VarNode(pos, Color(255, 180, 100)))

    def node_handler(self, pos: Tuple2D) -> Node | Connector:
        for node in self.nodes:
            if node.is_point_below(pos):
                return node
            match node:
                case ImageNode() | VarNode() as node:
                    if node.connector1.is_point_below(pos):
                        return node.connector1
                    elif node.connector2.is_point_below(pos):
                        return node.connector2
                case ChoosenNode() as node:
                    if node.connector1.is_point_below(pos):
                        return node.connector1
                    elif node.button_add.is_point_below(pos):
                        node.add_answer()
                    else:
                        for ans in node.answers:
                            if ans.connector2.is_point_below(pos):
                                return ans.connector2

    def clear_action_bar(self) -> NoReturn:
        self.action_bar = None
        self.action_bar_focus = False

    def update(self) -> NoReturn:
        if self.load_input:
            self.image_app.update()
            return

        self.surface.fill('white')
        for arrow in self.arrows:
            arrow.draw(self.surface)
        if self.choosen_arrow:
            self.choosen_arrow.draw(self.surface)
        for node in self.nodes:
            if node.pos[0] + node.size[0] < 0 or node.pos[1] + node.size[1] < 0 or node.pos[0] > config.screen_size[0] or node.pos[1] > config.screen_size[1]:
                continue
            node.draw(self.surface)
        if self.action_bar:
            self.action_bar.draw(self.surface)

        self.ui_manager.update(1.371)
        self.ui_manager.draw_ui(self.surface)

        pg.display.update()
        self.serialize()

    def serialize(self) -> NoReturn:
        initial: tuple[Node] = tuple(filter(lambda node: node.initial, self.nodes))
        _dict = {
            'version': '1.1',
            'nodes': {hash(i): i.__my_dict__() for i in self.nodes},
            'arrows': [i.__my_dict__() for i in self.arrows],
            'initial': hash(initial[0]) if len(initial) > 0 else 0
        }
        with open(config.get_file_game(), mode='w') as file:
            json.dump(_dict, file, indent=' ' * 4)

    @staticmethod
    def deserialize(is_mini_should: bool = True) -> Self:
        editor: Editor = Editor()

        def recognition_graphic(graphic: dict) -> tuple[Color, Tuple2D]:
            color: list[int] = graphic['color']
            return Color(color[0], color[1], color[2], color[3]), tuple(graphic['position'])

        with open(config.get_file_game(), mode='r', encoding='utf-8') as file:
            data: dict = json.load(file)
        if data == {}:
            return editor
        nodes: dict = data['nodes']
        arrows: dict = data['arrows']
        initial: str = str(data['initial'])
        final_nodes: dict[str, Node] = {}
        final_arrows: list[Arrow] = []
        for node_hash in nodes.keys():
            node: dict = nodes[node_hash]
            c, p = recognition_graphic(node)
            node_obj = None
            match node['type']:
                case 1:
                    node_obj = CircleNode(p, node['radius'], c)
                case 2:
                    node_obj = ImageNode(p, c, node['image_path'], tuple(node['size']), centering=False,
                                         is_mini_should=is_mini_should)
                case 3:
                    node_obj = ChoosenNode(p, c, False)
                    node_obj.size = node['size']

                    answers = node['answers']
                    for ans_hash in answers:
                        answer = answers[ans_hash]
                        c, p = recognition_graphic(answer)

                        answer_obj = Answer(p, node_obj, c)
                        answer_obj.set_text(answer['text'])
                        final_nodes[ans_hash] = answer_obj
                        node_obj.answers.append(answer_obj)
                    node_obj.set_pos(node_obj.pos)

                case 4:
                    node_obj = VarNode(p, c, tuple(node['size']), centering=False)

            if node.get('text'):
                text: str = node['text']
                node_obj.text = text
            if node_hash == initial:
                node_obj.initial = True
            final_nodes[node_hash] = node_obj

        for arrow in arrows:
            c, _ = recognition_graphic(arrow)
            start_hash: str = arrow['start']
            end_hash: str = arrow['end']

            final_arrows.append(Arrow(final_nodes[start_hash].connector2, final_nodes[end_hash].connector1, c))
        editor.nodes = list(v for v in final_nodes.values() if not isinstance(v, Answer))
        editor.arrows = final_arrows
        return editor

    def close_editor(self) -> NoReturn:
        self.serialize()
        files = glob.glob(f'{config.get_dir_mini()}/*')
        for f in files:
            os.remove(f)

    def control(self, events: list[Event]) -> bool | str:
        if self.load_input:
            return self.image_app.control(events)

        pos: Tuple2D = pg.mouse.get_pos()
        mouse: tuple[bool, ...] = pg.mouse.get_pressed()
        keys = pg.key.get_pressed()

        not_change_state: tuple[int, ...] = (
            pg.MOUSEMOTION,
            pg.MOUSEBUTTONUP,
            pg.ACTIVEEVENT,
            pg.WINDOWLEAVE,
            pg.WINDOWENTER,
            pg.WINDOWCLOSE
        )

        def move_all_nodes(move: Tuple2D, pause: bool = False) -> NoReturn:
            if pause:
                time.sleep(0.0001)
            for node in self.nodes:
                node.set_pos((node.pos[0] + move[0], node.pos[1] + move[1]))

        for event in events:
            # print(event)
            # action bar
            if event.type not in not_change_state:
                if self.action_bar_focus:
                    if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                        self.action_bar_handler(pos)
                    self.clear_action_bar()
                    break

            match event.type:
                case pg.MOUSEBUTTONDOWN:
                    match event.button:
                        # выбор ноды или начало стрелки
                        case 1:
                            match self.node_handler(pos):
                                case Node() as node:
                                    mode: bool = True if keys[pg.K_LSHIFT] else False
                                    self.add_choosen_node(node, mode)
                                case Connector() as conn:
                                    self.choosen_arrow = Arrow(conn, conn)
                                case _:
                                    pass
                        case 2:
                            pass
                        # отмена выбора ноды и удаление связей с коннектором
                        case 3:
                            match self.node_handler(pos):
                                case Node() as node:
                                    self.activate_action_bar(pos, node)
                                    if node in self.choosen_nodes.keys():
                                        node.choosen = False
                                        self.choosen_nodes.pop(node)
                                case Connector() as conn:
                                    self.arrows = [arrow for arrow in self.arrows if
                                                   arrow.start is not conn and arrow.end is not conn]
                                case None:
                                    self.activate_action_bar(pos)

                case pg.MOUSEBUTTONUP:
                    match event.button:
                        case 1:
                            # отмена выбора ноды и завершение стрелки
                            if len(self.choosen_nodes) > 0:
                                self.choosen_nodes = dict((k, v) for k, v in self.choosen_nodes.items() if v)
                                for node in self.nodes:
                                    if node not in self.choosen_nodes.keys():
                                        node.choosen = False
                            if self.choosen_arrow is not None:
                                for node in self.nodes:
                                    connector: Connector = node.get_connector(pos)
                                    if connector:
                                        self.choosen_arrow.end = connector

                                        # Проверка на то, чтобы коннекторы не были оба входными или выходными
                                        if connector.is_receiver == self.choosen_arrow.start.is_receiver:
                                            break
                                        # Проверка на то, чтобы начало и конец не вели в одну ноду
                                        if connector.node is self.choosen_arrow.start.node:
                                            break
                                        # Проверка на то, что такой же линии ещё не существует
                                        if any(arrow == self.choosen_arrow for arrow in self.arrows):
                                            break

                                        if self.choosen_arrow.start.is_receiver:
                                            self.choosen_arrow.end = self.choosen_arrow.start
                                            self.choosen_arrow.start = connector
                                        self.arrows.append(self.choosen_arrow)
                                        break
                                self.choosen_arrow = None

                case pg.MOUSEMOTION:
                    # перемещение выбранных нод и перемещение конца стрелки и перемещение всего поля
                    if pg.mouse.get_focused():
                        if mouse[0]:

                            if len(self.choosen_nodes) > 0:
                                for cnode in self.choosen_nodes:
                                    cnode.set_pos((cnode.pos[0] + event.rel[0], cnode.pos[1] + event.rel[1]))

                            if self.choosen_arrow is not None:
                                self.choosen_arrow.end = pos

                        elif mouse[1]:
                            move_all_nodes(event.rel)

                case pg.MOUSEWHEEL:
                    def calculations(size: tuple[float, float], dy: float) -> tuple[float, float]:
                        x = size[0] + dy * 5
                        koef = (x - size[0]) / 100 / 2 + 1
                        return x, koef

                    for node in self.nodes:
                        if isinstance(node, ImageNode) and node.image_mini is not None:
                            x, koef = calculations(node.size, event.y)
                            y = x * 9 / 16
                            if y < 10:
                                continue
                            create_miniature(node.path_image, (x, y))
                            path_mini = f'{config.get_dir_mini()}/{node.path_image[node.path_image.rfind("/"): node.path_image.find(".")]}.jpeg'
                            node.image_mini = pg.image.load(path_mini).convert()
                            node.size = (x, y)
                            node.set_pos((node.pos[0] * koef, node.pos[1] * koef))
                        elif isinstance(node, ChoosenNode):
                            x, koef = calculations(node.answers[0].size, event.y)
                            node.size = (x, x / 3 * len(node.answers) + len(node.answers))
                            for answer in node.answers:
                                answer.size = (x, x / 3)
                            node.set_pos((node.pos[0] * koef, node.pos[1] * koef))
                    print(event.y)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                match event.ui_element:
                    case self.input_box.button_ok:
                        self.input_box.deactivate()
                        self.input_box.node.set_text(self.input_box.entry.get_text())
                    case self.input_box.button_cancel:
                        self.input_box.deactivate()
                    case self.button_menu:
                        return 'menu'

                    case self.var_box.button_ok:
                        self.var_box.deactivate()
                        self.var_box.node.set_text(f'{self.var_box.entry.get_text()} {"=" if self.var_box.mode.get_single_selection() == "Установить" else "+=" if self.var_box.mode.get_single_selection() == "Увеличить" else "-="} {self.var_box.input_value.get_text()}')
                    case self.var_box.button_cancel:
                        self.var_box.deactivate()

            self.ui_manager.process_events(event)

        if keys[pg.K_RIGHT] or keys[pg.K_LEFT] or keys[pg.K_UP] or keys[pg.K_DOWN]:
            speed: int = 20
            if keys[pg.K_RIGHT]:
                move_all_nodes((-speed, 0), True)

            if keys[pg.K_LEFT]:
                move_all_nodes((speed, 0), True)

            if keys[pg.K_UP]:
                move_all_nodes((0, speed), True)

            if keys[pg.K_DOWN]:
                move_all_nodes((0, -speed), True)
            return True

        # подсветка кнопок экшен бара
        if pg.mouse.get_focused():
            if self.action_bar is not None:
                self.action_bar.backlight(pos)

        if len(events) > 0:
            return True
        return False
