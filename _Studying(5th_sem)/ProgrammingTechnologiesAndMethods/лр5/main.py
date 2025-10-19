# -*- coding: utf-8 -*-

"""
Главный исполняемый файл программы.
Точка входа, которая запускает пользовательский интерфейс.
"""

import sys
from ui import console_ui, gui_ui

def main():
    """
    Основная функция программы.
    Запускает GUI по умолчанию или консольный UI, если указан флаг --console.
    """
    if '--console' in sys.argv:
        print("Запуск в консольном режиме...")
        console_ui.start_ui()
    else:
        print("Запуск графического интерфейса...")
        gui_ui.start_ui()

if __name__ == "__main__":
    main()