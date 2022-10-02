"""
Базовая конфигурация приложения
"""
from pathlib import Path

ROOT_DIR = Path(__file__).parent
HOME_DIR = Path.home()
APP_NAME = 'Barcoder'
APP_ICON = 'favicon.ico'
THEME_NAME = 'dark_lightgreen'

LAYOUTS_DIRNAME = 'layouts'
FONT_DIRNAME = 'fonts'

FONT_DIR = ROOT_DIR / 'assets' / FONT_DIRNAME
LAYOUTS_DIR = ROOT_DIR / 'assets' / LAYOUTS_DIRNAME
