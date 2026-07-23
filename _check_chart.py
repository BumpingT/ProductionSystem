"""快速检查图表HTML"""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
config.DB_PATH = os.path.join(tempfile.gettempdir(), 'chk.db')
from models.database import Database
Database._conn = None
Database.init_db()

from services.chart_service import _chart_html
from services.stats_service import StatsService

stats = StatsService.get_summary()
html = _chart_html(stats, '测试')

for chart_id in ['id="w"', 'id="d"', 'id="p"']:
    if chart_id in html:
        print(f'OK: 找到图表容器 {chart_id}')
    else:
        print(f'BUG: 缺少图表容器 {chart_id}')

if 'echarts' in html:
    print('OK: 包含 echarts 引用')

Database.close()
if os.path.exists(config.DB_PATH):
    os.remove(config.DB_PATH)
