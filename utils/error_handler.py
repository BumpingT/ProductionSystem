"""
全局异常处理
"""
import sys
import traceback
from tkinter import messagebox
from .logger import logger


def setup_global_handler():
    """设置 tkinter 全局异常钩子"""
    import tkinter
    def handle_exception(exc_type, exc_value, exc_tb):
        msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical(f'未捕获异常:\n{msg}')
        try:
            messagebox.showerror('系统错误', f'发生未预期的错误:\n{exc_value}')
        except Exception:
            pass
    sys.excepthook = handle_exception
    tkinter.Tk.report_callback_exception = lambda self, exc, val, tb: handle_exception(exc, val, tb)


def safe_call(fn, *args, **kwargs):
    """安全调用函数，捕获异常并记录日志"""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.error(f'调用 {fn.__name__} 失败: {e}', exc_info=True)
        raise
