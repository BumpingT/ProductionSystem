"""
pytest 配置 — 共享 fixture
"""
import sys, os
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """使用临时数据库进行测试"""
    db_path = str(tmp_path / "test.db")
    # Monkey patch config.DB_PATH
    import config
    monkeypatch.setattr(config, "DB_PATH", db_path)
    # 确保 Database 使用新路径
    from models.database import Database
    Database._conn = None  # 重置连接
    Database.init_db()
    yield
    Database.close()
