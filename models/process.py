"""工序数据访问"""
from .database import Database
from utils.logger import logger

class ProcessRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("""
            SELECT p.*, m.price AS material_price
            FROM processes p
            LEFT JOIN materials m ON p.material = m.name
            ORDER BY p.material, p.process_name
        """).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(material: str, process_name: str, unit_price: float) -> bool:
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO processes (material,process_name,unit_price) VALUES (?,?,?)",
                        (material, process_name, unit_price))
            conn.commit()
            logger.info(f'添加工序: {material}/{process_name}')
            return True
        except Exception as e:
            logger.warning(f'添加工序失败: {e}')
            return False

    @staticmethod
    def update(pid: int, material: str, process_name: str, unit_price: float):
        conn = Database.get_conn()
        conn.execute("UPDATE processes SET material=?,process_name=?,unit_price=? WHERE id=?",
                    (material, process_name, unit_price, pid))
        conn.commit()

    @staticmethod
    def delete(pid: int):
        conn = Database.get_conn()
        conn.execute("DELETE FROM processes WHERE id=?", (pid,))
        conn.execute("DELETE FROM worker_processes WHERE process_id=?", (pid,))
        conn.commit()
        logger.info(f'删除工序 ID={pid}')

    # ── 工人工序分配 ──
    @staticmethod
    def get_worker_processes(worker_id: int) -> list[int]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT process_id FROM worker_processes WHERE worker_id=?",
                           (worker_id,)).fetchall()
        return [r['process_id'] for r in rows]

    @staticmethod
    def assign_worker_process(worker_id: int, process_id: int):
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO worker_processes (worker_id,process_id) VALUES (?,?)",
                        (worker_id, process_id))
            conn.commit()
        except Exception:
            pass

    @staticmethod
    def unassign_worker_process(worker_id: int, process_id: int):
        conn = Database.get_conn()
        conn.execute("DELETE FROM worker_processes WHERE worker_id=? AND process_id=?",
                    (worker_id, process_id))
        conn.commit()
