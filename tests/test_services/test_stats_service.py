"""
StatsService 单元测试
"""
import pytest
from services.stats_service import StatsService
from models.database import Database


class TestStatsService:
    """统计服务测试"""

    def test_get_summary_returns_correct_structure(self):
        """测试统计返回正确结构"""
        stats = StatsService.get_summary()
        assert 'totals' in stats
        assert 'by_worker' in stats
        assert 'by_process' in stats
        assert 'by_date' in stats

    def test_get_summary_totals(self):
        """测试统计数据正确性"""
        stats = StatsService.get_summary()
        totals = stats['totals']
        assert 'w' in totals  # 工人数
        assert 'q' in totals  # 总产量
        assert 'e' in totals  # 总工资
        assert 'r' in totals  # 记录数

    def test_get_summary_with_date_filter(self):
        """测试日期筛选"""
        stats = StatsService.get_summary(start_date='2026-07-20', end_date='2026-07-22')
        totals = stats['totals']
        assert totals['r'] > 0

    def test_get_summary_no_results(self):
        """测试无结果的情况"""
        stats = StatsService.get_summary(start_date='2020-01-01', end_date='2020-01-31')
        totals = stats['totals']
        assert totals['r'] == 0
        assert totals['q'] == 0

    def test_get_summary_by_worker_format(self):
        """测试按工人统计格式"""
        stats = StatsService.get_summary()
        for worker in stats['by_worker']:
            assert 'worker' in worker
            assert 'group_name' in worker
            assert 'q' in worker
            assert 'e' in worker

    def test_list_months(self):
        """测试月份列表"""
        months = StatsService.list_months()
        assert isinstance(months, list)
        if months:
            assert len(months[0]) == 7  # YYYY-MM

    def test_get_monthly_stats(self):
        """测试月度统计"""
        months = StatsService.list_months()
        if months:
            stats = StatsService.get_monthly_stats(months[0])
            assert 'totals' in stats
            assert 'by_worker' in stats
