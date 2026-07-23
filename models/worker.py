"""工人数据访问"""
from .database import Database
from utils.logger import logger


class WorkerRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT * FROM workers ORDER BY group_name, name").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(name: str, group: str = '') -> bool:
        if not name or not name.strip():
            logger.warning('添加工人失败: 名称不能为空')
            return False
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO workers (name,group_name) VALUES (?,?)", (name, group))
            if group:
                conn.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (group,))
            conn.commit()
            logger.info(f'添加工人: {name} ({group})')
            return True
        except Exception:
            # 工人已存在，检查是否已有组别
            existing = conn.execute("SELECT group_name FROM workers WHERE name=?", (name,)).fetchone()
            if existing and existing['group_name']:
                return False  # 已有组别，不覆盖
            # 无组别则自动更新
            try:
                conn.execute("UPDATE workers SET group_name=? WHERE name=?", (group, name))
                if group:
                    conn.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (group,))
                conn.commit()
                logger.info(f'工人已存在(无组别)，更新组别: {name} -> {group}')
                return True
            except Exception as e:
                logger.warning(f'更新工人组别失败 {name}: {e}')
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
        # 将生产记录中的 worker_id 置为 0，避免显示为 none
        conn.execute("UPDATE records SET worker_id=0 WHERE worker_id=?", (wid,))
        conn.execute("DELETE FROM workers WHERE id=?", (wid,))
        conn.commit()
        logger.info(f'删除工人 ID={wid}')

    # ── 班组管理 ──

    @staticmethod
    def get_groups() -> list[str]:
        """获取所有班组名称（合并 groups 表和 workers 表）"""
        conn = Database.get_conn()
        rows = conn.execute("SELECT name FROM groups ORDER BY name").fetchall()
        groups = set(r['name'] for r in rows)
        # 合并 workers 表中的组别
        rows = conn.execute(
            "SELECT DISTINCT group_name FROM workers WHERE group_name != '' ORDER BY group_name"
        ).fetchall()
        groups.update(r['group_name'] for r in rows)
        return sorted(groups)

    @staticmethod
    def add_group(group_name: str) -> bool:
        """添加班组"""
        if not group_name or not group_name.strip():
            return False
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
            conn.commit()
            logger.info(f'添加班组: {group_name}')
            return True
        except Exception as e:
            logger.warning(f'添加班组失败 {group_name}: {e}')
            return False

    @staticmethod
    def delete_group(group_name: str) -> bool:
        """删除班组（仅清空工人的组别，不删除工人）"""
        conn = Database.get_conn()
        try:
            # 清空该班组下所有工人的 group_name
            conn.execute("UPDATE workers SET group_name='' WHERE group_name=?", (group_name,))
            # 删除班组
            conn.execute("DELETE FROM groups WHERE name=?", (group_name,))
            conn.commit()
            logger.info(f'删除班组: {group_name}（已清空工人的组别）')
            return True
        except Exception as e:
            logger.warning(f'删除班组失败 {group_name}: {e}')
            return False
