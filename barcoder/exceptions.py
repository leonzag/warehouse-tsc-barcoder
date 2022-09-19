__all__ = [
    'LayoutsParsingError', 'FontsParsingError', 'ExcelParsingError',
    'RenderDrawError', 'RenderSaveError'
]

class LayoutsParsingError(Exception):
    """Error while parsing label layouts"""

class FontsParsingError(Exception):
    """Error while parsing fonts"""

class ExcelParsingError(Exception):
    """Can't parse excel-file with data"""

class RenderDrawError(Exception):
    """Can't render page of PDF-document"""

class RenderSaveError(Exception):
    """Can't save rendered PDF-document"""
