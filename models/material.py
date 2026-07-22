"""物料数据访问"""
from .database import Database
from utils.logger import logger

class MaterialRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT * FROM materials ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(name: str, price: float = 0) -> bool:
        if not name or not name.strip():
            logger.warning('添加物料失败: 名称不能为空')
            return False
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO materials (name,price) VALUES (?,?)", (name, price))
            conn.commit()
            logger.info(f'添加物料: {name}')
            return True
        except Exception as e:
            logger.warning(f'添加物料失败 {name}: {e}')
            return False

    @staticmethod
    def update(mid: int, name: str, price: float):
        conn = Database.get_conn()
        # 获取旧名称
        row = conn.execute("SELECT name FROM materials WHERE id=?", (mid,)).fetchone()
        if not row:
            logger.warning(f'更新物料失败: ID={mid} 不存在')
            return
        old_name = row['name']
        # 更新物料表
        conn.execute("UPDATE materials SET name=?,price=? WHERE id=?", (name, price, mid))
        # 同步更新工序表中的物料名称
        if old_name != name:
            conn.execute("UPDATE processes SET material=? WHERE material=?", (name, old_name))
            logger.info(f'物料改名: {old_name} -> {name}，已同步工序表')
        conn.commit()

    @staticmethod
    def delete(mid: int):
        conn = Database.get_conn()
        # 获取物料名称，用于级联删除关联工序
        row = conn.execute("SELECT name FROM materials WHERE id=?", (mid,)).fetchone()
        if not row:
            return
        name = row['name']
        # 先删除关联工序（及工序的工人分配）
        for p in conn.execute("SELECT id FROM processes WHERE material=?", (name,)).fetchall():
            conn.execute("DELETE FROM worker_processes WHERE process_id=?", (p['id'],))
        conn.execute("DELETE FROM processes WHERE material=?", (name,))
        conn.execute("DELETE FROM materials WHERE id=?", (mid,))
        conn.commit()
        logger.info(f'删除物料 ID={mid}，已同步清理关联工序')
