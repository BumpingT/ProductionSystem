"""工人数据访问"""
from .database import Database
from utils.logger import logger

class WorkerRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT * FROM workers ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(name: str, group: str = '') -> bool:
        if not name or not name.strip():
            logger.warning('添加工人失败: 名称不能为空')
            return False
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO workers (name,group_name) VALUES (?,?)", (name, group))
            conn.commit()
            logger.info(f'添加工人: {name}')
            return True
        except Exception as e:
            logger.warning(f'添加工人失败 {name}: {e}')
            return False

    @staticmethod
    def update(wid: int, name: str, group: str):
        conn = Database.get_conn()
        conn.execute("UPDATE workers SET name=?,group_name=? WHERE id=?", (name, group, wid))
        conn.commit()

    @staticmethod
    def delete(wid: int):
        conn = Database.get_conn()
        conn.execute("UPDATE users SET worker_id=0 WHERE worker_id=?", (wid,))
        conn.execute("DELETE FROM workers WHERE id=?", (wid,))
        conn.execute("DELETE FROM worker_processes WHERE worker_id=?", (wid,))
        conn.commit()
        logger.info(f'删除工人 ID={wid}')
