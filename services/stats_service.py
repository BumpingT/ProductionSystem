"""统计业务服务"""
import calendar as cal_mod
from models.record import RecordRepository
from utils.logger import logger


class StatsService:
    @staticmethod
    def get_summary(start_date: str = None, end_date: str = None,
                    process_filter: int = None, worker_filter: int = None) -> dict:
        """获取统计数据，与 RecordRepository.get_stats 相同"""
        return RecordRepository.get_stats(start_date, end_date, process_filter, worker_filter)

    @staticmethod
    def get_monthly_stats(month: str) -> dict:
        """获取指定月份的统计数据，month 格式为 'YYYY-MM'"""
        try:
            y, mo = int(month.split('-')[0]), int(month.split('-')[1])
            _, last_day = cal_mod.monthrange(y, mo)
        except (ValueError, IndexError):
            logger.warning(f'无效的月份格式: {month}')
            return {'totals': {}, 'by_worker': [], 'by_process': [], 'by_date': []}
        start = f'{month}-01'
        end = f'{y}-{mo:02d}-{last_day:02d}'
        return RecordRepository.get_stats(start_date=start, end_date=end)

    @staticmethod
    def list_months() -> list[str]:
        """列出有记录的年月"""
        return RecordRepository.list_months()
