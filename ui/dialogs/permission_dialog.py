"""
权限管理对话框 — 从 DashboardView 拆分为独立组件
"""
from tkinter import Toplevel, Label, Frame, Canvas, Scrollbar, Checkbutton, IntVar, VERTICAL, HORIZONTAL, BOTTOM, RIGHT, LEFT, X, Y, BOTH
from config import CARD, DARK
from models.user import UserRepository
from config import ROLE_NAMES
from utils.logger import logger


class PermissionDialog:
    """细粒度用户权限管理"""

    def __init__(self, parent_root):
        self.root = parent_root
        self._perm_vars = {}
        self._build()

    def _build(self):
        top = Toplevel(self.root)
        top.title('权限管理')
        top.geometry('1000x500')
        top.configure(bg=CARD)
        top.grab_set()
        Label(top, text='权限管理', font=('Microsoft YaHei', 12, 'bold'),
              bg=CARD, fg=DARK).pack(anchor='w', padx=16, pady=(10, 4))
        Label(top, text='点击复选框切换权限', font=('Microsoft YaHei', 9),
              bg=CARD, fg='#888').pack(anchor='w', padx=16)

        canvas = Canvas(top, bg=CARD, highlightthickness=0)
        vsb = Scrollbar(top, orient=VERTICAL, command=canvas.yview)
        hsb = Scrollbar(top, orient=HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT, fill='y')
        hsb.pack(side=BOTTOM, fill='x')
        canvas.pack(side=LEFT, fill='both', expand=True)

        frame = Frame(canvas, bg=CARD)
        canvas.create_window((0, 0), window=frame, anchor='nw')
        frame.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # 获取用户和权限数据
        try:
            users = UserRepository.get_all()
            logger.info(f'权限管理: 加载了 {len(users)} 个用户')
        except Exception as e:
            logger.error(f'加载用户列表失败: {e}')
            Label(top, text=f'加载数据失败: {e}', bg=CARD, fg='red',
                  font=('Microsoft YaHei', 10)).pack(pady=20)
            return

        if not users:
            logger.warning('权限管理: 没有用户可显示')
            Label(top, text='暂无用户数据，请先添加用户', bg=CARD, fg='#888',
                  font=('Microsoft YaHei', 10)).pack(pady=20)
            return

        perm_labels = [
            ('record_add', '添加记录'), ('record_delete', '删除记录'),
            ('record_edit', '编辑记录'), ('material_manage', '管理物料'),
            ('worker_manage', '管理工人'), ('process_manage', '管理工序'),
            ('assignment_manage', '工序分配'), ('chart_view', '查看图表'),
            ('summary_view', '查看汇总'), ('monthly_view', '月度汇总'),
            ('export_excel', '导出Excel'), ('user_manage', '用户管理'),
        ]
        perms_keys = [p[0] for p in perm_labels]

        Label(frame, text='用户', bg=CARD, fg=DARK, font=('Microsoft YaHei', 9, 'bold'),
              width=10, anchor='w').grid(row=0, column=0, padx=4, pady=2, sticky='w')
        Label(frame, text='角色', bg=CARD, fg=DARK, font=('Microsoft YaHei', 9, 'bold'),
              width=8, anchor='w').grid(row=0, column=1, padx=4, pady=2, sticky='w')
        for ci, (pk, pl) in enumerate(perm_labels, 2):
            Label(frame, text=pl, bg=CARD, fg='#555', font=('Microsoft YaHei', 8),
                  width=7, anchor='w').grid(row=0, column=ci, padx=2, pady=2)

        for ri, u in enumerate(users, 1):
            un = u['username']
            try:
                Label(frame, text=un, bg=CARD, fg=DARK, font=('Microsoft YaHei', 9),
                      width=10, anchor='w').grid(row=ri, column=0, padx=4, pady=1, sticky='w')
                role_cn = ROLE_NAMES.get(u.get('role', ''), u.get('role', ''))
                Label(frame, text=role_cn, bg=CARD, fg='#555', font=('Microsoft YaHei', 9),
                      width=8, anchor='w').grid(row=ri, column=1, padx=4, pady=1, sticky='w')
                perms_dict = UserRepository.get_permissions(un)
                for ci, pk in enumerate(perms_keys, 2):
                    var = IntVar(value=perms_dict.get(pk, 0))
                    self._perm_vars[(un, pk)] = var

                    def make_cmd(u_name, p_key):
                        return lambda: UserRepository.set_permission(
                            u_name, p_key, self._perm_vars[(u_name, p_key)].get())

                    cb = Checkbutton(frame, variable=var, bg=CARD,
                                     command=make_cmd(un, pk))
                    cb.grid(row=ri, column=ci)
            except Exception as e:
                logger.error(f'加载用户 {un} 的权限失败: {e}')
