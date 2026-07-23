"""生产记录数据访问"""
from .database import Database
from utils.logger import logger

class RecordRepository:
    @staticmethod
    def get_all(user: dict = None) -> list[dict]:
        conn = Database.get_conn()
        base_sql = """SELECT r.*, w.name AS worker_name, w.group_name,
                       p.material, p.process_name
                FROM records r
                LEFT JOIN workers w ON r.worker_id = w.id
                LEFT JOIN processes p ON r.process_id = p.id"""

        if user and user.get('role') == 'worker':
            wid = user.get('worker_id')
            if wid:
                rows = conn.execute(base_sql + """
                    WHERE r.worker_id = ?
                    ORDER BY r.id DESC LIMIT 500
                """, (wid,)).fetchall()
            else:
                rows = []
        elif user and user.get('role') == 'leader':
            # 组长：优先使用 leader_workers 精确关联
            leader_workers = conn.execute(
                "SELECT worker_id FROM leader_workers WHERE leader_username=?",
                (user['username'],)).fetchall()
            lw_ids = [rw['worker_id'] for rw in leader_workers]
            if lw_ids:
                placeholders = ','.join(['?'] * len(lw_ids))
                rows = conn.execute(base_sql + f"""
                    WHERE r.worker_id IN ({placeholders})
                    ORDER BY r.id DESC LIMIT 500
                """, lw_ids).fetchall()
            elif user.get('group_name'):
                # 降级：按组别过滤
                rows = conn.execute(base_sql + """
                    WHERE w.group_name = ?
                    ORDER BY r.id DESC LIMIT 500
                """, (user['group_name'],)).fetchall()
            else:
                # 无关联无组别，看不到数据
                rows = []
        else:
            rows = conn.execute(base_sql + """
                ORDER BY r.id DESC LIMIT 500
            """).fetchall()
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
        # 组长只能看本组数据（用子查询避免 JOIN 别名冲突）
        if user and user.get('role') == 'worker':
            wid = user.get('worker_id')
            if wid:
                wh.append("r.worker_id=?")
                pa.append(wid)
            else:
                # 无关联工人，看不到数据
                wh.append("1=0")  # 永假条件
        elif user and user.get('role') == 'leader':
            # 优先使用 leader_workers 精确关联
            lw = conn.execute("SELECT worker_id FROM leader_workers WHERE leader_username=?",
                             (user['username'],)).fetchall()
            lw_ids = [r['worker_id'] for r in lw]
            if lw_ids:
                wh.append("r.worker_id IN (" + ','.join(['?'] * len(lw_ids)) + ")")
                pa.extend(lw_ids)
            elif user.get('group_name'):
                # 降级到按组别过滤
                wh.append("r.worker_id IN (SELECT id FROM workers WHERE group_name=?)")
                pa.append(user['group_name'])
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

