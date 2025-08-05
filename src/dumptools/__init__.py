#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dump Tools Package
用于处理dump文件夹中JSON数据的工具包
"""

from .json_to_markdown import JSONToMarkdownConverter

try:
    from .md2pdf import MarkdownToPDFConverter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    MarkdownToPDFConverter = None

try:
    from .md2docx import MarkdownToDocxConverter
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    MarkdownToDocxConverter = None

__all__ = ['JSONToMarkdownConverter']

if PDF_AVAILABLE:
    __all__.append('MarkdownToPDFConverter')

if DOCX_AVAILABLE:
    __all__.append('MarkdownToDocxConverter')
