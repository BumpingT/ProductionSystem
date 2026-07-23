"""
权限服务 — 集中管理数据访问权限过滤逻辑
消除 RecordRepository.get_all/get_stats 与 UI 层之间重复的权限判断
"""
from models.database import Database
from models.user import UserRepository


class PermissionService:
    """数据权限工具，根据用户角色计算可查看的 worker_id 列表"""

    @staticmethod
    def get_visible_worker_ids(user: dict | None) -> list[int]:
        """
        根据用户角色返回可查看的工人 ID 列表。
        - admin/manager: 空列表 = 全部可见
        - leader: leader_workers 或同组工人
        - worker: 仅自己
        - None/其他: 全部可见
        """
        if not user:
            return []  # 空 = 无限制

        role = user.get('role', '')
        conn = Database.get_conn()

        if role == 'admin' or role == 'manager':
            return []  # 全部可见

        if role == 'worker':
            wid = user.get('worker_id')
            return [wid] if wid else [-1]  # -1 表示看不到任何数据

        if role == 'leader':
            username = user.get('username', '')
            # 优先使用 leader_workers 精确关联
            lw = conn.execute(
                "SELECT worker_id FROM leader_workers WHERE leader_username=?",
                (username,)).fetchall()
            if lw:
                return [r['worker_id'] for r in lw]
            # 降级：按组别过滤
            group_name = user.get('group_name', '')
            if group_name:
                rows = conn.execute(
                    "SELECT id FROM workers WHERE group_name=?", (group_name,)).fetchall()
                return [r['id'] for r in rows]
            return [-1]  # 无关联无组别，看不到数据

        return []  # 未知角色，全部可见

    @staticmethod
    def build_worker_filter_clause(user: dict | None, table_alias: str = 'r') -> tuple:
        """
        构建 SQL WHERE 子句片段和参数。
        返回 (where_clause_str, params_list)
        """
        wids = PermissionService.get_visible_worker_ids(user)
        if not wids:
            return '', []  # 无限制
        if len(wids) == 1 and wids[0] == -1:
            return f'1=0', []  # 看不到任何数据
        placeholders = ','.join(['?'] * len(wids))
        return f'{table_alias}.worker_id IN ({placeholders})', wids
