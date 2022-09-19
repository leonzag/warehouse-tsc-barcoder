from typing import Any, Sequence
from pathlib import Path
import yaml

from .typing import (
    Label, LabelType, LabelSize, LabelQtyMode,
    LabelLayout, BoxLabelLayout, ProductLabelLayout,
    BarType, Font,
)
from barcoder.exceptions import LayoutsParsingError, FontsParsingError

__all__ = ['LayoutsParser']


class LayoutsParser:
    """
    Парсит директории с макетами этикеток и шрифтами,
    и предоставляет удобный интерфейс получения информации о них
    """
    def __init__(self, layouts_dir: Path | str, fonts: Sequence[Font]) -> None:
        self.layouts_dir = Path(layouts_dir)
        self._fonts = fonts
        self._box_layouts = self._parse_layouts(LabelType.BOX)
        self._product_layouts = self._parse_layouts(LabelType.PRODUCT)

    @property
    def box_labels(self) -> Sequence[Label]:
        """Список этикеток для маркировки коробов"""
        return self._box_layouts

    @property
    def product_labels(self) -> Sequence[Label]:
        """Список продуктовых этикеток"""
        return self._product_layouts

    @property
    def types(self) -> Sequence[LabelType]:
        """Список всех возможных типов этикеток"""
        return tuple(LabelType)

    @property
    def qty_modes(self) -> Sequence[LabelQtyMode]:
        """Список всех возможных колчественных режимов отрисовки этикеток"""
        return tuple(LabelQtyMode)

    def get_labels_by_type(self, label_type: LabelType) -> Sequence[Label]:
        """
        Список этикеток по их типу
        """
        return {LabelType.BOX: self.box_labels,
                LabelType.PRODUCT: self.product_labels}.get(label_type, [])

    def _parse_layouts(self, label_type: LabelType) -> tuple[Label]:
        """
        Парсинг пресетов этикеток
        """
        def load_label(fp: Path) -> Label:
            return self._parse_file(yaml.safe_load(fp.open()), label_type)

        files = (self.layouts_dir / label_type.name.lower()).iterdir()
        try:
            return tuple(load_label(f) for f in files
                         if f.is_file() and f.suffix in ('.yaml', '.yml'))
        except FontsParsingError:
            raise LayoutsParsingError('Check that fontname in layout files are correct')
        except Exception:
            raise LayoutsParsingError('Check that label layout files are correct')

    def _parse_file(self, data: dict[str, Any], label_type: LabelType) -> Label:
        """Возвращает информацию для построения этикетки"""
        name = data['name']
        size = LabelSize(data['size']['width'], data['size']['height'])
        data_layouts = data['layouts']

        layouts = {
            b: self._parse_label_layouts(layout[b.name], label_type)
            for layout in data_layouts for b in BarType if b.name in layout
        }
        return Label(name, label_type, size, layouts)

    def _parse_label_layouts(self, data: dict[str, Any], label_type: LabelType) -> LabelLayout:
        """
        Парсинг непосредственно скелета этикетки (Привязан к типу ШК)
        """
        # Общие свойства
        font = self._parse_font(data)
        bar_width = data['bar_width']
        bar_height_ratio = data['bar_height_ratio']
        margin = data['margin']

        if label_type is LabelType.BOX:
            barcode_value_font = self._parse_font(data, field='font_barcode_value')
            return BoxLabelLayout(font, barcode_value_font, bar_width, bar_height_ratio, margin)

        elif label_type is LabelType.PRODUCT:
            return ProductLabelLayout(font, bar_width, bar_height_ratio, margin)

    def _parse_font(self, data: dict[str, Any], field: str = 'font') -> Font:
        """
        Создает объект шрифта.
        field: имя поля макета (yaml), в котором указано имя и размер шрифта (По ум-ю 'font')
        """
        name, sz = data[field]['name'], data[field]['size']
        fonts = [*filter(lambda f: f.name == name, self._fonts)]
        if len(fonts) and (path := fonts[0].path):
            return Font(name, path, sz)
        raise LayoutsParsingError(f'Не найден шрифт {name}')
