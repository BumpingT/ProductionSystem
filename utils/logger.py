"""
日志工具
"""
import logging
import sys

# 根日志器
logger = logging.getLogger('prod_sys')
logger.setLevel(logging.INFO)

# 控制台输出
console = logging.StreamHandler(sys.stderr)
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
))
logger.addHandler(console)

# 文件输出（如果可写）
try:
    fh = logging.FileHandler('app.log', encoding='utf-8', mode='a')
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
    ))
    logger.addHandler(fh)
except Exception:
    pass  # 文件不可写时仅控制台输出
