"""
Lior Fun Time
Creating a Maze
"""
from itertools import product
from contextlib import suppress
from random import shuffle, choice
from collections import namedtuple, OrderedDict, deque

from pygame import display, draw, Surface, init, event as events
from pygame.time import Clock
from pygame.key import get_pressed
from pygame.font import SysFont, get_default_font
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE


class Coordinates(namedtuple('Coordinates', 'width, height')):
    @property
    def up(self):
        return self.__class__(self.width, self.height - 1)

    @property
    def down(self):
        return self.__class__(self.width, self.height + 1)

    @property
    def left(self):
        return self.__class__(self.width - 1, self.height)

    @property
    def right(self):
        return self.__class__(self.width + 1, self.height)


class MazeCell:
    def __init__(self):
        self.south = True
        self.east = True
        self.visited = False


class Maze:
    def __init__(self, width=40, height=30):
        self.width = width
        self.height = height
        self.table = OrderedDict(
            (coordinates, MazeCell()) for coordinates in self.coordinates_iter)

    @property
    def coordinates_iter(self):
        for width, height in product(range(self.width), range(self.height)):
            yield Coordinates(width, height)

    def generate(self):
        """ Generates a random maze using a magical simple recursive function. """
        cell_queue = deque([self.table[0, 0]])
        while len(cell_queue) != 0:
            cell = cell_queue.pop()
            neighbors = self._cell_neighbors(cell)
            shuffle(neighbors)
            for neighbor in neighbors:
                if neighbor.visited:
                    continue
                neighbor.visited = True
                cell_queue.append(neighbor)
                self._knock_wall(cell, neighbor)

    def _cell_neighbors(self, cell):
        row, column = self._cell_coordinates(cell)
        neighbors = []
        with suppress(KeyError):
            neighbors.append(self.table[row, column - 1])
        with suppress(KeyError):
            neighbors.append(self.table[row, column + 1])
        with suppress(KeyError):
            neighbors.append(self.table[row + 1, column])
        with suppress(KeyError):
            neighbors.append(self.table[row - 1, column])
        return neighbors

    def _cell_coordinates(self, cell):
        for coordinates, maze_cell in self.table.items():
            if maze_cell is cell:
                return coordinates
        raise Exception('Cell is not in maze table')

    def _knock_wall(self, cell, neighbor):
        row, column = self._cell_coordinates(cell)
        neighbor_row, neighbor_column = self._cell_coordinates(neighbor)
        if row == neighbor_row and column == neighbor_column + 1:
            neighbor.south = False
            return
        if row == neighbor_row and column == neighbor_column - 1:
            cell.south = False
            return
        if row == neighbor_row + 1 and column == neighbor_column:
            neighbor.east = False
            return
        if row == neighbor_row - 1 and column == neighbor_column:
            cell.east = False
            return
        raise Exception('neighbor is not really a cell neighbor')


class GameBoard:
    def __init__(self, game, *, width=800, height=600):
        self.game = game
        self.game.generate()
        self.width = width
        self.height = height
        self.cell_width = self.width / self.game.width
        self.cell_height = self.height / self.game.height

        init()
        self.screen = display.set_mode((self.width, self.height))
        display.set_caption('Maze Demo')

        font = SysFont(get_default_font(), 55)
        text = font.render("Loading...", 1, (255, 255, 255))
        rect = text.get_rect()
        rect.center = self.width / 2, self.height / 2
        self.screen.blit(text, rect)
        display.update(rect)

    def draw_game(self):
        self.screen.fill((255, 255, 255))
        for (column, row), cell in self.game.table.items():
            if cell.south:
                draw.line(
                    self.screen,
                    (0, 0, 0),
                    (column * self.cell_width, (row + 1) * self.cell_height),
                    ((column + 1) * self.cell_width, (row + 1) * self.cell_height))
            if cell.east:
                draw.line(
                    self.screen,
                    (0, 0, 0),
                    ((column + 1) * self.cell_width, row * self.cell_height),
                    ((column + 1) * self.cell_width, (row + 1) * self.cell_height))
        draw.rect(
            self.screen,
            (0, 0, 0),
            (0, 0, self.width, self.height),
            1)
        display.update()


class PlayerCell:
    def __init__(self):
        self.visited = False


class Player:
    def __init__(self, game_board):
        assert isinstance(game_board, GameBoard)
        self.game_board = game_board
        self.width = self.game_board.cell_width - 3
        self.height = self.game_board.cell_height - 3
        self.table = OrderedDict()

        self.steps = 0
        self.last_step = None
        self._current_step = None

        self._base = Surface((self.width, self.height))
        self._base.fill((255, 255, 255))
        self._red_p = self._base.copy()
        self._green_p = self._base.copy()
        self._blue_p = self._base.copy()
        self._goldy = self._base.copy()

    @property
    def current_step(self):
        cell = self.table[self._current_step]
        cell.visited = True
        return self._current_step

    @current_step.setter
    def current_step(self, coordinates):
        if coordinates == self._current_step:
            return
        self.steps += 1
        self.last_step = self._current_step
        self._current_step = coordinates


        # coordinates, current_cell = next(reversed(self.table.items()))
        # current_cell.visited = True
        # return coordinates

    @property
    def finish_line(self):
        return next(iter(self.table))

    def reset_player(self):
        rectangle = 0, 0, self.width, self.height
        draw.ellipse(self._red_p, (255, 0, 0), rectangle)
        draw.ellipse(self._green_p, (0, 255, 0), rectangle)
        draw.ellipse(self._blue_p, (0, 0, 255), rectangle)
        draw.ellipse(self._goldy, (0xc5, 0x93, 0x48), rectangle)
        self.table.clear()
        for coordinates in reversed(list(self.game_board.game.coordinates_iter)):
            self.table[coordinates] = PlayerCell()
            self.game_board.screen.blit(
                self._base,
                (coordinates.width * self.game_board.cell_width + 2, coordinates.height * self.game_board.cell_height + 2))
        self.current_step = coordinates
        coordinates = self.finish_line
        self.game_board.screen.blit(
            self._goldy,
            (coordinates.width * self.game_board.cell_width + 2, coordinates.height * self.game_board.cell_height + 2))
        self.draw_player()

    def draw_player(self):
        for coordinates in self.game_board.game.coordinates_iter:
            if self.table[coordinates].visited:
                self.game_board.screen.blit(
                    self._green_p,
                    (coordinates.width * self.game_board.cell_width + 2, coordinates.height * self.game_board.cell_height + 2))
        self.game_board.screen.blit(
            self._blue_p,
            (self.current_step.width * self.game_board.cell_width + 2, self.current_step.height * self.game_board.cell_height + 2))

    def solve_game(self):
        clock = Clock()
        directions = ['up', 'down', 'left', 'right']
        while self.current_step != self.finish_line:
            clock.tick(10)
            direction = choice(directions)
            self.move_player(direction)
            self.draw_player()
            display.update()
        print('Congratulations, you beat this maze.')

    def move_player(self, direction):
        current_step = self.current_step
        with suppress(KeyError):
            if direction == 'up':
                if not self.game_board.game.table[current_step.up].south:
                    self.current_step = self.current_step.up
            elif direction == 'down':
                if not self.game_board.game.table[current_step].south:
                    self.current_step = self.current_step.down
            elif direction == 'left':
                if not self.game_board.game.table[current_step.left].east:
                    self.current_step = self.current_step.left
            elif direction == 'right':
                if not self.game_board.game.table[self.current_step].east:
                    self.current_step = self.current_step.right


if __name__ == '__main__':
    game_board = GameBoard(game=Maze())
    game_board.draw_game()
    player = Player(game_board)
    player.reset_player()
    player.draw_player()
    player.solve_game()
    # event loop
    clock = Clock()
    while True:
        clock.tick(10)
        for event in events.get():
            if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                break
            print(event)
        keys = get_pressed()
        print(keys)
        display.update()
