import os
from enum import Enum, auto
from typing import NoReturn, TypeVar, Final, Self, Optional

import pygame as pg
import pygame_gui
from pygame import Surface, Event

from app import Screen
from config import Config, resource_path
from editor import Editor, Node, ImageNode, ChoosenNode, Answer

config: Final[Config] = Config()

pg.font.init()


EN = TypeVar("EN", bound=Node)


class GameNode:
    def __init__(self, node: EN) -> NoReturn:
        self.editor_node: EN = node
        self.nexts: list[Transition | Self] = []

        if isinstance(node, Answer):
            self.initial: bool = node.node.initial
        else:
            self.initial: bool = node.initial


class TransitionType(Enum):
    null = auto()
    press_button = auto()
    expression = auto()


class Transition:
    def __init__(self, result: GameNode, t_type: TransitionType = TransitionType.null,
                 button_text: str = None) -> NoReturn:
        self.condition = None
        self.result: GameNode = result
        self.t_type: TransitionType = t_type
        self.button_text: str = button_text

    def __repr__(self):
        return f'{self.result}, {self.t_type}, {self.button_text}'


class ImageGameNode(GameNode):
    def __init__(self, node: ImageNode, manager: pygame_gui.UIManager) -> NoReturn:
        super().__init__(node)
        self.manager: pygame_gui.UIManager = manager

        self.image: Optional[Surface] = None
        self.textbox = None

        self.setup()
        assert self.textbox is not None

        self.textbox.hide()

        self.buttons = []

    def setup(self) -> NoReturn:
        if self.textbox is not None:
            self.textbox.kill()
        if self.editor_node.path_image is not None and os.path.exists(self.editor_node.path_image):
            self.image: Surface = pg.image.load(self.editor_node.path_image).convert()
            self.image: Surface = pg.transform.scale(self.image, config.screen_size)

        text: str = f"<font face='freesans' size=6.5> {self.editor_node.text} </font>"
        self.textbox = pygame_gui.elements.UITextBox(html_text=text,
                                                     relative_rect=pg.Rect(0, config.screen_size[1] * 0.8, config.screen_size[0], config.screen_size[1] * 0.2),
                                                     manager=self.manager,
                                                     anchors={
                                                         'left': 'left',
                                                         'right': 'right',
                                                         'top': 'top',
                                                         'bottom': 'bottom'})
        if self.editor_node.text == '':
            self.textbox.hide()

    def setup_buttons(self) -> NoReturn:
        for but in self.buttons:
            but.kill()
        if self.is_have_buttons():
            x = 0
            h = 40
            y = (config.screen_size[1] - h) / 2
            indent = 10
            w = (config.screen_size[0] - (len(self.nexts) + 1) * indent) / len(self.nexts)
            for tr in self.nexts:
                self.buttons.append(pygame_gui.elements.UIButton(relative_rect=pg.Rect(x + indent, y, w, h),
                                                                 text=tr.button_text,
                                                                 manager=self.manager,
                                                                 object_id=f'button-{self.nexts.index(tr)}',
                                                                 anchors={
                                                                     'left': 'left',
                                                                     'right': 'right',
                                                                     'top': 'top',
                                                                     'bottom': 'bottom'}
                                                                 ))
                x += w + indent

    def is_have_buttons(self) -> bool:
        return len(tuple(filter(lambda tr: tr.t_type is TransitionType.press_button, self.nexts))) > 0

    def draw(self, surface: Surface) -> NoReturn:
        if self.image is not None:
            surface.blit(self.image, self.image.get_rect(center=surface.get_rect().center))
        else:
            surface.fill('white')
        if self.editor_node.text != '':
            self.textbox.show()

        if len(self.buttons) <= 0:
            self.setup_buttons()


class ChoosenGameNode(GameNode):
    def __init__(self, node: ChoosenNode, editor: Editor) -> NoReturn:
        super().__init__(node)
        self.game_answers: list[tuple[str, Node]] = []
        for ans in node.answers:
            cur_arrows = tuple(filter(lambda ar: ans is ar.start.node, editor.arrows))
            if len(cur_arrows) <= 0:
                continue
            arrow = cur_arrows[0]

            self.game_answers.append((ans.text, arrow.end.node))


N = TypeVar("N", bound=GameNode)


class GameScreen(Screen):
    def __init__(self) -> NoReturn:
        super().__init__()
        self.ui_manager = pygame_gui.UIManager(self.surface.get_size(), resource_path('theme1.json'))
        self.editor: Editor = Editor.deserialize(False)
        self.initial_node: GameNode = None
        self.nodes: list[N] = []
        self.buttons: list[pygame_gui.elements.UIButton]

        for arrow in self.editor.arrows:
            start: tuple[N] = tuple(filter(lambda node: node.editor_node is arrow.start.node, self.nodes))
            end: tuple[N] = tuple(filter(lambda node: node.editor_node is arrow.end.node, self.nodes))

            if len(start) <= 0:
                s_node = self._craft_node(arrow.start.node)
                if bool(s_node):
                    self.nodes.append(s_node)
            else:
                s_node = start[0]

            if len(end) <= 0:
                e_node = self._craft_node(arrow.end.node)
                self.nodes.append(e_node)
            else:
                e_node = end[0]

            if bool(s_node):
                s_node.nexts.append(e_node)

        for node in self.nodes:
            next_choosen = tuple(filter(lambda next: isinstance(next, ChoosenGameNode), node.nexts))
            if len(next_choosen) <= 0:
                new_nexts = [Transition(n) for n in node.nexts]
                node.nexts = new_nexts
                continue

            choosen: ChoosenGameNode = next_choosen[0]
            node.nexts = []

            for text, next_n in choosen.game_answers:
                result = tuple(filter(lambda n: n.editor_node is next_n, self.nodes))
                node.nexts.append(Transition(result[0], TransitionType.press_button, button_text=text))

        self.nodes = list(filter(lambda n: isinstance(n, ImageGameNode), self.nodes))

        initials = tuple(filter(lambda node: node.initial, self.nodes))
        self.current_node: ImageGameNode = initials[0] if len(initials) > 0 else None

    def _craft_node(self, node: Node) -> N | bool:
        match node:
            case ImageNode() as node:
                return ImageGameNode(node, self.ui_manager)
            case ChoosenNode() as node:
                return ChoosenGameNode(node, self.editor)
            case _:
                return False

    def step(self, id_result: int = 0) -> NoReturn:
        if len(self.current_node.nexts) <= 0:
            return

        self.current_node.textbox.hide()
        if self.current_node.is_have_buttons():
            for but in self.current_node.buttons:
                but.kill()
            self.current_node.buttons = []

        self.current_node = self.current_node.nexts[id_result].result

    def update(self) -> NoReturn:
        if self.current_node is None:
            return
        self.current_node.draw(self.surface)

        self.ui_manager.update(1.371)
        self.ui_manager.draw_ui(self.surface)
        pg.display.update()

    def control(self, events: list[Event]) -> bool | str:
        if self.current_node is None:
            return 'menu'
        for event in events:
            match event.type:
                case pg.KEYDOWN:
                    if event.key == pg.K_h:
                        if not self.current_node.is_have_buttons():
                            self.step()
                            return True

                case pygame_gui.UI_BUTTON_PRESSED:
                    index: int = int(event.ui_object_id[event.ui_object_id.index('-') + 1:])
                    self.step(index)
                    return True

                case pg.VIDEORESIZE:
                    self.current_node.setup()
                    self.current_node.setup_buttons()
                    return True

            self.ui_manager.process_events(event)

        if len(events) > 0:
            return True
        return True
