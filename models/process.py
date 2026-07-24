"""工序数据访问"""
from .database import Database
from utils.logger import logger


class ProcessRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("""
            SELECT p.id, p.material_code, p.process_name, p.unit_price,
                   m.name AS material_name, m.version AS material_version
            FROM processes p
            LEFT JOIN materials m ON p.material_code = m.code
            GROUP BY p.id
            ORDER BY p.material_code, p.process_name
        """).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(material_code: str, process_name: str, unit_price: float) -> bool:
        if not material_code or not material_code.strip() or not process_name or not process_name.strip():
            logger.warning('添加工序失败: 物料编号和工序名称不能为空')
            return False
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO processes (material_code,process_name,unit_price) VALUES (?,?,?)",
                        (material_code, process_name, unit_price))
            conn.commit()
            logger.info(f'添加工序: {material_code}/{process_name}')
            return True
        except Exception as e:
            logger.warning(f'添加工序失败: {e}')
            return False

    @staticmethod
    def update(pid: int, material_code: str, process_name: str, unit_price: float):
        conn = Database.get_conn()
        conn.execute("UPDATE processes SET material_code=?,process_name=?,unit_price=? WHERE id=?",
                    (material_code, process_name, unit_price, pid))
        conn.commit()

    @staticmethod
    def delete(pid: int):
        conn = Database.get_conn()
        conn.execute("DELETE FROM records WHERE process_id=?", (pid,))
        conn.execute("DELETE FROM processes WHERE id=?", (pid,))
        conn.commit()
        logger.info(f'删除工序 ID={pid}，已同步清理关联记录')

    @staticmethod
    def get_process_names() -> list[str]:
        """获取所有不重复的工序名称"""
        conn = Database.get_conn()
        rows = conn.execute("SELECT DISTINCT process_name FROM processes ORDER BY process_name").fetchall()
        return [r['process_name'] for r in rows]
