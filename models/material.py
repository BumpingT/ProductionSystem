"""物料数据访问"""
from .database import Database
from utils.logger import logger


class MaterialRepository:
    @staticmethod
    def get_all() -> list[dict]:
        conn = Database.get_conn()
        rows = conn.execute("SELECT * FROM materials ORDER BY code").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(code: str, name: str, version: str = '') -> bool:
        if not code or not code.strip() or not name or not name.strip():
            logger.warning('添加物料失败: 编号和名称不能为空')
            return False
        conn = Database.get_conn()
        try:
            conn.execute("INSERT INTO materials (code,name,version) VALUES (?,?,?)",
                        (code, name, version))
            conn.commit()
            logger.info(f'添加物料: {code} ({name}-{version})')
            return True
        except Exception as e:
            logger.warning(f'添加物料失败 {code}: {e}')
            return False

    @staticmethod
    def update(mid: int, code: str, name: str, version: str):
        conn = Database.get_conn()
        # 获取旧code，用于同步工序表
        row = conn.execute("SELECT code FROM materials WHERE id=?", (mid,)).fetchone()
        if not row:
            logger.warning(f'更新物料失败: ID={mid} 不存在')
            return
        old_code = row['code']
        conn.execute("UPDATE materials SET code=?,name=?,version=? WHERE id=?",
                    (code, name, version, mid))
        # 同步更新工序表中的物料编号
        if old_code != code:
            conn.execute("UPDATE processes SET material_code=? WHERE material_code=?",
                        (code, old_code))
            logger.info(f'物料编号变更: {old_code} -> {code}，已同步工序表')
        conn.commit()

    @staticmethod
    def delete(mid: int):
        conn = Database.get_conn()
        # 获取物料编号，用于级联删除关联工序
        row = conn.execute("SELECT code FROM materials WHERE id=?", (mid,)).fetchone()
        if not row:
            return
        mat_code = row['code']
        # 先删除关联工序
        for p in conn.execute("SELECT id FROM processes WHERE material_code=?",
                             (mat_code,)).fetchall():
            conn.execute("DELETE FROM records WHERE process_id=?", (p['id'],))
        conn.execute("DELETE FROM processes WHERE material_code=?", (mat_code,))
        conn.execute("DELETE FROM materials WHERE id=?", (mid,))
        conn.commit()
        logger.info(f'删除物料 ID={mid} (code={mat_code})，已同步清理关联工序和记录')

    @staticmethod
    def get_by_code(code: str) -> dict | None:
        """按编号查询物料"""
        conn = Database.get_conn()
        row = conn.execute("SELECT * FROM materials WHERE code=?", (code,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def search(keyword: str) -> list[dict]:
        """按关键字搜索物料（匹配编号或名称）"""
        conn = Database.get_conn()
        like = f'%{keyword}%'
        rows = conn.execute(
            "SELECT * FROM materials WHERE code LIKE ? OR name LIKE ? ORDER BY code",
            (like, like)
        ).fetchall()
        return [dict(r) for r in rows]
