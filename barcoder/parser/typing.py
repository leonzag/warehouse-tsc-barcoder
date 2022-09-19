from enum import Enum
from typing import NamedTuple, Sequence, Type, Union

__all__ = ['BoxData', 'ProductData', 'Data', 'Dataset',
           'LabelType', 'LabelQtyMode', 'LabelSize', 'Label',
           'LabelLayout', 'BoxLabelLayout', 'ProductLabelLayout',
           'BarType', 'Font']

ColNum = int
ColName = str
RowNum = int

Millimeters = float
RatioFactor = float


class BoxData(NamedTuple):
    """Данные для этикетки на короба"""
    quantity: int
    sku: str
    barcode: Union[str, int]

class ProductData(NamedTuple):
    """Данные для продуктовой этикетки"""
    n: int
    sku: str
    product: str
    quantity: int
    barcode: Union[str, int]


Data = Union[BoxData, ProductData]
Dataset = Sequence[Data]


class DocModel:
    """
    Описание модели данных Excel таблицы
    columns: словрь:
        ключ: номер колонки
        значение: имя колонки (не анализируется при парсинге)
    start_row: номер строки, с которой начинаются нужные данные
    """
    columns: dict[ColNum, ColName]
    start_row: RowNum
    datamaker: Type[Data]


class ProductDocModel(DocModel):
    """Excel-file c данными для продуктовых этикеток"""
    columns = {
        1: '№',
        2: 'Артикул',
        3: 'Товары',
        4: 'Количество',
        6: 'ШК'
    }
    start_row = 5
    datamaker: Type[ProductData] = ProductData

class BoxDocModel(DocModel):
    """Excel-file c данными для этикетки на короба"""
    columns = {
        2: 'Количество',
        3: 'Артикул',
        4: 'ШК'
    }
    start_row = 2
    datamaker: Type[BoxData] = BoxData


class BarType(Enum):
    """Перечисление типов ШК, где значение (value) - BarName известное ReportLab"""
    CODE128 = 'Code128'
    EAN13 = 'EAN13'
    UPCA = 'UPCA'
    EAN8 = 'EAN8'

class Font(NamedTuple):
    """Именованный кортеж: (Имя шрифта, путь до него, размер шрифта)"""
    name: str
    path: str
    size: float


class LabelType(Enum):
    """Перечисление Типов этикетирования - Товарные этикетки либо Этикетки на короба (маркировка)"""
    PRODUCT = 'Товарная этикетка'
    BOX = 'Маркировка коробов'

class LabelQtyMode(Enum):
    """Перечисление количественного режима отрисовки документа"""
    SHORT = 'Печать без учета кол-ва наименования'
    FULL = 'Печать с учетом кол-ва наименований (По файлу)'

class LabelSize(NamedTuple):
    """Размер: ширина * высота (в миллиметрах)"""
    width: Millimeters
    height: Millimeters


class ProductLabelLayout(NamedTuple):
    """Макет товарной этикетки"""
    font: Font
    bar_width: float
    bar_height_ratio: RatioFactor
    margin: float

class BoxLabelLayout(NamedTuple):
    """Макет этикетки на короба"""
    font: Font
    barcode_value_font: Font
    bar_width: float
    bar_height_ratio: RatioFactor
    margin: float


LabelLayout = ProductLabelLayout | BoxLabelLayout

class Label(NamedTuple):
    """
    Все данные по этикетке:
        Имя
        Тип этикетирования (к кот. она принадлежит),
        Размер
        Скелеты - словарь (ключ: Тип ШК, знач: Скелет этикетки)
    """
    name: str
    type: LabelType
    size: LabelSize
    layouts: dict[BarType, LabelLayout]
