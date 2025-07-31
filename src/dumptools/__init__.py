#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dump Tools Package
用于处理dump文件夹中JSON数据的工具包
"""

from .json_to_markdown import JSONToMarkdownConverter

try:
    from .json_to_pdf import JSONToPDFConverter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    JSONToPDFConverter = None

try:
    from .json_to_docx import JSONToDocxConverter
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    JSONToDocxConverter = None

__all__ = ['JSONToMarkdownConverter']

if PDF_AVAILABLE:
    __all__.append('JSONToPDFConverter')

if DOCX_AVAILABLE:
    __all__.append('JSONToDocxConverter')
