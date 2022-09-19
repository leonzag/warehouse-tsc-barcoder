#!/bin/env python

import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon

from barcoder.gui import MainWindow, rc_resources
from barcoder.parser import LayoutsParser, parse_fonts
from barcoder.exceptions import FontsParsingError, LayoutsParsingError

from config import APP_ICON, THEME_NAME, FONT_DIR, LAYOUTS_DIR
from qt_material import apply_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(f':/assets/img/{APP_ICON}'))
    apply_stylesheet(app, f'{THEME_NAME}.xml')

    try:
        fonts = parse_fonts(FONT_DIR)
        layouts = LayoutsParser(LAYOUTS_DIR, fonts)
    except LayoutsParsingError:
        app = QMessageBox(QMessageBox.Critical, 'Ошибка получения шаблонов этикеток',
                          f'Один или несколько макетов этикеток некорректны.\nПроверьте директорию {LAYOUTS_DIR}')
    except FontsParsingError:
        app = QMessageBox(QMessageBox.Critical, 'Ошибка получения списка шрифтов',
                          f'Не удалось корректно распознать список шрифтов в директории {LAYOUTS_DIR}.')
    else:
        win = MainWindow(layouts, fonts)
        win.show()

    sys.exit(app.exec())
