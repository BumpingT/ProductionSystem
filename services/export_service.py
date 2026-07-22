"""Excel 导出服务"""
import os
from config import YEN
from utils.logger import logger


def export_excel(stats, filepath, title=''):
    """导出统计数据到 Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    except ImportError:
        from tkinter import messagebox
        messagebox.showinfo('\u63d0\u793a', '\u8bf7\u5148\u5b89\u88c5 openpyxl: pip install openpyxl')
        return False
    wb = openpyxl.Workbook()
    ws = wb.active
    title_str = title or '\u751f\u4ea7\u8bb0\u5f55'
    ws.cell(row=1, column=1, value=title_str).font = Font(bold=True, size=13)
    ws.merge_cells('A1:H1')
    t = stats.get('totals', {})
    ws.cell(row=2, column=1, value=f'\u5de5\u4eba\u6570: {t.get("w",0)}  |  \u603b\u4ea7\u91cf: {t.get("q",0)}  |  \u603b\u5de5\u8d44: {YEN}{round(t.get("e",0),2)}')
    headers = ['\u5de5\u4eba', '\u7ec4\u522b', '\u4ef6\u6570', '\u5de5\u8d44']
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=ci, value=h)
        cell.font = Font(bold=True, color='00ffffff')
        cell.fill = PatternFill('solid', fgColor='001a73e8')
        cell.alignment = Alignment(horizontal='center')
    for ri, r in enumerate(stats.get('by_worker', []), 5):
        ws.cell(row=ri, column=1, value=r.get('worker', ''))
        ws.cell(row=ri, column=2, value=r.get('group_name', ''))
        ws.cell(row=ri, column=3, value=r.get('q', 0))
        ws.cell(row=ri, column=4, value=round(r.get('e', 0), 2))
    wb.save(filepath)
    logger.info(f'Excel \u5df2\u5bfc\u51fa: {filepath}')
    return True
