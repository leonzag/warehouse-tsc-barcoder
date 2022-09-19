from pathlib import Path
from .typing import Font

from barcoder.exceptions import FontsParsingError

__all__ = ['parse_fonts']


def parse_fonts(fonts_dir: Path | str) -> tuple[Font, ...]:
    """
    Парсит шрифты из дирректории шрифтов
    """
    def mk_font(f: Path):
        name, sz = f.name.removesuffix(f.suffix), 10
        return Font(name, str(f), sz)

    try:
        return tuple(mk_font(f) for f in Path(fonts_dir).iterdir() if f.suffix == '.ttf')
    except Exception:
        raise FontsParsingError
