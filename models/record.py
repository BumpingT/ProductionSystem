"""生产记录数据访问"""
from .database import Database
from utils.logger import logger
from services.permission_service import PermissionService

class RecordRepository:
    @staticmethod
    def get_all(user: dict = None) -> list[dict]:
        conn = Database.get_conn()
        where_clause, params = PermissionService.build_worker_filter_clause(user, 'r')
        where_sql = f' WHERE {where_clause}' if where_clause else ''
        rows = conn.execute(f"""SELECT r.*, w.name AS worker_name, w.group_name,
                       p.material, p.process_name
                FROM records r
                LEFT JOIN workers w ON r.worker_id = w.id
                LEFT JOIN processes p ON r.process_id = p.id{where_sql}
                ORDER BY r.id DESC LIMIT 500""", params).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(worker_id: int, process_id: int, quantity: float, unit_price: float, record_date: str) -> bool:
        conn = Database.get_conn()
        try:
            conn.execute("""INSERT INTO records
                (worker_id, process_id, quantity, unit_price, record_date)
                VALUES (?,?,?,?,?)""", (worker_id, process_id, quantity, unit_price, record_date))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f'添加记录失败: {e}')
            return False

    @staticmethod
    def update(rid: int, worker_id: int, process_id: int, quantity: float, unit_price: float, record_date: str):
        conn = Database.get_conn()
        conn.execute("""UPDATE records SET
            worker_id=?, process_id=?, quantity=?, unit_price=?, record_date=?
            WHERE id=?""", (worker_id, process_id, quantity, unit_price, record_date, rid))
        conn.commit()

    @staticmethod
    def delete(rid: int):
        conn = Database.get_conn()
        conn.execute("DELETE FROM records WHERE id=?", (rid,))
        conn.commit()

    @staticmethod
    def get_stats(start_date: str = None, end_date: str = None,
                  process_filter: int = None, worker_filter: int = None,
                  user: dict = None) -> dict:
        conn = Database.get_conn()
        wh = []
        pa = []
        # 使用 PermissionService 统一处理数据权限过滤
        perm_where, perm_params = PermissionService.build_worker_filter_clause(user, 'r')
        if perm_where:
            wh.append(perm_where)
            pa.extend(perm_params)
        if start_date:
            wh.append("r.record_date >= ?")
            pa.append(start_date)
        if end_date:
            wh.append("r.record_date <= ?")
            pa.append(end_date)
        if process_filter:
            wh.append("r.process_id=?")
            pa.append(process_filter)
        if worker_filter:
            wh.append("r.worker_id=?")
            pa.append(worker_filter)
        ws = " WHERE " + " AND ".join(wh) if wh else ""
        totals = conn.execute(f"""SELECT COUNT(*) AS r,
            COUNT(DISTINCT r.worker_id) AS w,
            COALESCE(SUM(r.quantity),0) AS q,
            COALESCE(SUM(r.quantity*r.unit_price),0) AS e
            FROM records r{ws}""", pa).fetchone()
        by_worker = conn.execute(f"""SELECT w.name AS worker, w.group_name,
            SUM(r.quantity) AS q, SUM(r.quantity*r.unit_price) AS e
            FROM records r LEFT JOIN workers w ON r.worker_id=w.id{ws}
            GROUP BY r.worker_id ORDER BY e DESC""", pa).fetchall()
        by_process = conn.execute(f"""SELECT p.material, p.process_name,
            SUM(r.quantity) AS q, SUM(r.quantity*r.unit_price) AS e
            FROM records r LEFT JOIN processes p ON r.process_id=p.id{ws}
            GROUP BY r.process_id ORDER BY q DESC""", pa).fetchall()
        by_date = conn.execute(f"""SELECT r.record_date,
            SUM(r.quantity) AS q, SUM(r.quantity*r.unit_price) AS e, COUNT(*) AS c
            FROM records r{ws}
            GROUP BY r.record_date ORDER BY r.record_date""", pa).fetchall()
        return {
            'totals': dict(totals),
            'by_worker': [dict(r) for r in by_worker],
            'by_process': [dict(r) for r in by_process],
            'by_date': [dict(r) for r in by_date],
        }

    @staticmethod
    def list_months() -> list[str]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT DISTINCT substr(record_date,1,7) AS m FROM records ORDER BY m DESC").fetchall()
        return [r['m'] for r in rows]

