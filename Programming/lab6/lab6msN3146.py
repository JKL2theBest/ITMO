import re
from collections import deque

class FormatError(Exception): pass
class UndoError(Exception): pass
class RedoError(Exception): pass

class MyDeque(deque):
    def __init__(self, iterable=()):
        super().__init__()
        self.history = []
        self.future = []
        for item in iterable:
            self._check_format(item)
            super().append(item)
        self._save_state(initial=True)

    def _check_format(self, item):
        if not isinstance(item, str):
            raise TypeError("Только стринги дозволены") # Кек
        pattern = r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2,3}\d{2,3}$'
        if not re.match(pattern, item):
            raise FormatError("Неверный формат Автомобильного номера")

    def append(self, item):
        self._check_format(item)
        super().append(item)
        self._save_state()

    def appendleft(self, item):
        self._check_format(item)
        super().appendleft(item)
        self._save_state()

    def pop(self):
        item = super().pop()
        self._save_state()
        return item

    def popleft(self):
        item = super().popleft()
        self._save_state()
        return item

    def insert(self, index, item):
        self._check_format(item)
        super().insert(index, item)
        self._save_state()

    def remove(self, value):
        super().remove(value)
        self._save_state()

    def clear(self):
        super().clear()
        self._save_state()

    def _save_state(self, initial=False):
        if not initial:
            self.history.append(list(self))
        else:
            self.history.append(list(self))
        self.future.clear()

    def undo(self):
        if len(self.history) <= 1:
            raise UndoError("Нет истории для отмены")
        self.future.append(self.history.pop())
        last_state = self.history[-1]
        self._restore_state(last_state)

    def redo(self):
        if not self.future:
            raise RedoError("Нет действий для повтора")
        next_state = self.future.pop()
        self.history.append(next_state)
        self._restore_state(next_state)

    def _restore_state(self, state):
        super().clear()
        super().extend(state)
