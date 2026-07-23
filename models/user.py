"""用户和权限数据访问"""
from .database import Database
from utils.logger import logger
from utils.auth import hash_password
from config import ALL_PERMS

class UserRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_username(username: str) -> dict | None:
        conn = Database.get_conn()
        r = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(r) if r else None

    @staticmethod
    def get_by_worker_id(worker_id: int) -> dict | None:
        conn = Database.get_conn()
        r = conn.execute("SELECT * FROM users WHERE worker_id=?", (worker_id,)).fetchone()
        return dict(r) if r else None

    @staticmethod
    def add(username: str, password: str, display_name: str = '',
            role: str = 'worker', worker_id: int = 0, group_name: str = '') -> bool:
        conn = Database.get_conn()
        try:
            h = hash_password(password)
            conn.execute("""INSERT INTO users
                (username, password_hash, display_name, role, worker_id, group_name)
                VALUES (?,?,?,?,?,?)""", (username, h, display_name, role, worker_id, group_name))
            for pk in ALL_PERMS:
                allowed = 1 if pk in ROLE_DEFAULT_PERMS.get(role, []) else 0
                conn.execute("INSERT OR IGNORE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,?)",
                            (username, pk, allowed))
            conn.commit()
            logger.info(f'添加用户: {username}')
            return True
        except Exception as e:
            logger.warning(f'添加用户失败 {username}: {e}')
            return False

    @staticmethod
    def update_password(username: str, new_password: str):
        conn = Database.get_conn()
        h = hash_password(new_password)
        conn.execute("UPDATE users SET password_hash=? WHERE username=?", (h, username))
        conn.commit()
        logger.info(f'用户 {username} 密码已修改')

    @staticmethod
    def update_profile(username: str, display_name: str, role: str, worker_id: int = 0, group_name: str = ''):
        conn = Database.get_conn()
        conn.execute("UPDATE users SET display_name=?,role=?,worker_id=?,group_name=? WHERE username=?",
                    (display_name, role, worker_id, group_name, username))
        conn.commit()

    @staticmethod
    def delete(username: str) -> bool:
        if username == 'admin':
            return False
        conn = Database.get_conn()
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.execute("DELETE FROM user_permissions WHERE username=?", (username,))
        conn.execute("DELETE FROM leader_workers WHERE leader_username=?", (username,))
        conn.commit()
        logger.info(f'删除用户: {username}')
        return True

    @staticmethod
    def get_permissions(username: str) -> dict:
        conn = Database.get_conn()
        rows = conn.execute("SELECT perm_key,allowed FROM user_permissions WHERE username=?",
                           (username,)).fetchall()
        return {r['perm_key']: r['allowed'] for r in rows}

    @staticmethod
    def set_permission(username: str, perm_key: str, allowed: int):
        conn = Database.get_conn()
        conn.execute("INSERT OR REPLACE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,?)",
                    (username, perm_key, allowed))
        conn.commit()

    # ── 组长关联工人 ──
    @staticmethod
    def get_leader_workers(leader_username: str) -> list[int]:
        """获取组长关联的工人ID列表"""
        conn = Database.get_conn()
        rows = conn.execute("SELECT worker_id FROM leader_workers WHERE leader_username=?",
                           (leader_username,)).fetchall()
        return [r['worker_id'] for r in rows]

    @staticmethod
    def set_leader_workers(leader_username: str, worker_ids: list[int]):
        """设置组长关联的工人列表（先清空后写入）"""
        conn = Database.get_conn()
        conn.execute("DELETE FROM leader_workers WHERE leader_username=?", (leader_username,))
        for wid in worker_ids:
            conn.execute("INSERT INTO leader_workers (leader_username,worker_id) VALUES (?,?)",
                        (leader_username, wid))
        conn.commit()
        logger.info(f'组长 {leader_username} 关联工人: {worker_ids}')

    @staticmethod
    def rename(old_username: str, new_username: str) -> bool:
        """重命名用户（同步更新关联表）"""
        if old_username == 'admin':
            return False
        conn = Database.get_conn()
        try:
            conn.execute("UPDATE users SET username=? WHERE username=?", (new_username, old_username))
            conn.execute("UPDATE user_permissions SET username=? WHERE username=?", (new_username, old_username))
            conn.execute("UPDATE leader_workers SET leader_username=? WHERE leader_username=?", (new_username, old_username))
            conn.commit()
            logger.info(f'用户重命名: {old_username} -> {new_username}')
            return True
        except Exception as e:
            logger.warning(f'用户重命名失败: {e}')
            return False
