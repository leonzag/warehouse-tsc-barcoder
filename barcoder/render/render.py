from typing import Sequence

from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.renderPDF import Drawing
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

from barcoder.parser import (
    Label, LabelType, LabelQtyMode, LabelLayout, BoxLabelLayout, ProductLabelLayout,
    Data, BoxData, ProductData,
    BarType, Font
)
from barcoder.exceptions import RenderDrawError, RenderSaveError

Millimeters = float
Coord_Y = float


class RenderLabel:
    def __init__(self,
                 filepath: str,
                 label: Label,
                 label_type: LabelType,
                 qty_mode: LabelQtyMode,
                 fonts: Sequence[Font]) -> None:

        """
        Создание документа и отрисовка одиночной этикетки (или партии одинаковых на разных листах)
        по вызову <draw>
        """
        self._register_fonts(fonts)

        self.type = label_type
        self.qty_mode = qty_mode
        self.layouts: dict[BarType, LabelLayout] = label.layouts
        self.width: Millimeters = label.size.width * mm
        self.height: Millimeters = label.size.height * mm

        self.doc = Canvas(
            filename=filepath,
            pagesize=(self.width, self.height)
        )

    def draw(self, data: Data):
        try:
            self._draw_label(data)
        except Exception:
            raise RenderDrawError('Ошибка отрисовки этикетки')

    def save(self):
        try:
            self.doc.save()
        except Exception:
            raise RenderSaveError('Ошибка при сохранении готового PDF документа')

    def _draw_label(self, data: Data) -> None:
        """
        Отрисовка одиночной этикетки, либо несколько экземпляров одинаковых этикеток
        """
        bar_type = BarType.CODE128  # ШК на короба всегда имеют тип Code128
        if self.type is LabelType.PRODUCT:
            bar_type = self.recognize_bar_by_value(data.barcode)

        layout = self.layouts[bar_type]  # Основные параметры для отрисовки
        barWidth = layout.bar_width * mm  # Ширина тончайшего элемента ШК (Полоса)
        barHeight = (self.height * layout.bar_height_ratio)  # Высота ШК
        margin = layout.margin * mm  # Отступ от краев

        copies = 1
        if self.qty_mode is LabelQtyMode.FULL:
            copies = data.quantity  # кол-во отрисовок ШК такое, как указано в файле, а не по одной на наимен-е

        for _ in range(copies):
            self.doc.setPageSize((self.width, self.height))
            self.doc.setFont(layout.font.name, layout.font.size)
            bar = createBarcodeDrawing(
                codeName=bar_type.value,
                value=data.barcode,
                fontSize=layout.font.size,
                barWidth=barWidth, barHeight=barHeight
            )
            x_coord = (self.width - bar.width) / 2
            y_coord = margin

            y_coord = self._draw_label_details(bar, bar_type, data, layout, margin, y_coord)
            bar.drawOn(self.doc, x_coord, y_coord)
            self.doc.showPage()  # Сохранить страницу с этикеткой

    def _draw_label_details(self,
                            bar: Drawing,
                            barType: BarType,
                            data: Data,
                            layout: LabelLayout,
                            margin: Millimeters,
                            y_coord: Millimeters) -> Coord_Y:
        """
        Отрисовка на этикетке дополнительной текстовой информации:
            артикул, наименование и кол-во,
        Возвращает новую координату по Y для корректной отрисовки ШК
        """
        if self.type is LabelType.BOX and type(layout) is BoxLabelLayout and type(data) is BoxData:
            return self._draw_box_label_details(bar, data, layout, margin, y_coord)

        elif self.type is LabelType.PRODUCT and type(layout) is ProductLabelLayout and type(data) is ProductData:
            return self._draw_product_label_details(bar, barType, data, layout, margin, y_coord)

        return y_coord

    def _draw_box_label_details(self,
                                bar: Drawing,
                                data: BoxData,
                                layout: BoxLabelLayout,
                                margin: Millimeters,
                                y_coord: Millimeters) -> Coord_Y:
        """
        Текстовая инф-я для этикетки на короба
        """
        bar_y_coord = y_coord + layout.font.size
        value = str(data.barcode)
        y_coord = (bar.height + bar_y_coord + margin / 2)
        val, val_end = value[:-4] + ' ', value[-4:]  # последние 4 цифры отдельно
        ft = layout.barcode_value_font
        ft_end = Font(ft.name, ft.path, ft.size * 1.8)
        # ширина будущей надписи
        vwidth = sum(stringWidth(v, f.name, f.size) for v, f
                     in zip((val, val_end), (ft, ft_end)))
        # Координаты будущей надписи
        vy = int(y_coord)
        vx = int((self.width - vwidth) / 2)

        text = self.doc.beginText(int(vx), int(vy))
        text.textOut(val + ' ')
        text.setFont(ft.name, ft.size)
        self.doc.drawText(text)  # Отрисовка значения ШК (без посл. 4х цифр)

        text_end = self.doc.beginText(text.getX(), int(vy))
        text_end.setFont(ft_end.name, ft_end.size)  # Размер последних 4 цифр больше остальных
        text_end.textLine(val_end)
        self.doc.drawText(text_end)  # Отрисовка последних 4х цифр
        # Строка: количества и артикул под ШК
        self.doc.drawCentredString(self.width / 2, margin, f'{data.quantity} шт. Арт.:{data.sku}')
        return bar_y_coord

    def _draw_product_label_details(self,
                                    bar: Drawing,
                                    barType: BarType,
                                    data: ProductData,
                                    layout: ProductLabelLayout,
                                    margin: Millimeters,
                                    y_coord: Millimeters) -> Coord_Y:
        """
        Текстовая инф-я для продуктовой этикетки
        """
        bar_y_coord = y_coord
        if barType is BarType.CODE128:  # расположить Код под ШК
            self.doc.drawCentredString(self.width / 2, margin, text=str(data.barcode))
            bar_y_coord += layout.font.size

        lines = [f'Арт.:{data.sku}', *self._split(data.product, self.width - 3 * margin, layout.font)]
        lines[-1] += f' {data.quantity} шт.'
        y_coord = bar_y_coord + bar.height + layout.font.size * len(lines)
        for n, ln in enumerate(lines):
            self.doc.drawCentredString(
                x=(self.width / 2), y=(y_coord - layout.font.size * n),
                text=ln
            )
        return bar_y_coord

    @staticmethod
    def _split(text: str, width_limit: Millimeters, font: Font, lines_count: int = 3) -> Sequence[str]:
        """
        Разбиение текста на строки в зависимости от возможной длины каждой строки
        Также с учетом указания Кол-Ва ед. на конце строки
        """
        words = [s.strip() for s in text.split()]
        lines, curr_line = [], []

        for w in words:
            if stringWidth(' '.join(curr_line + [w]) + ' XXXшт.',
                           font.name, font.size) < width_limit:
                curr_line += [w]
            else:
                lines += [' '.join(curr_line)]
                curr_line = [w]
            if len(lines) == lines_count:
                return lines

        if stringWidth(' '.join(curr_line) + ' XXXшт.', font.name, font.size) < width_limit:
            lines += [' '.join(curr_line)]
        return lines

    @staticmethod
    def _register_fonts(fonts: Sequence[Font]) -> int:
        """Регистрация шрифтов для reportlab"""
        return len([registerFont(TTFont(f.name, f.path)) for f in fonts])

    @staticmethod
    def recognize_bar_by_value(barcode_value: str | int) -> BarType:
        """Определение типа ШК по его значение (кол-во цифр или сиволов)"""
        string_value = str(barcode_value)
        if all(s.isdigit() for s in string_value):
            return {
                8: BarType.EAN8, 12: BarType.UPCA, 13: BarType.EAN13
            }.get(len(string_value), BarType.CODE128)

        return BarType.CODE128
