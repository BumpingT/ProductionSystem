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
                conn.execute("INSERT OR IGNORE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,0)",
                            (username, pk))
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
