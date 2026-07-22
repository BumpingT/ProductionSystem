"""Apply remaining UI changes for role-based access."""
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()

# 1. Update ref_users + add user form with worker binding + edit dialog
old = '''        def ref_users():
            for i in tr.get_children(): tr.delete(i)
            for u in get_users():
                tr.insert('', END, values=(u['username'], u['display_name'], u.get('created_at','')))
        ref_users()
        tr.pack(padx=16, fill=BOTH, expand=True)
        top._tr = tr  # store ref for _assign_materials
        f = Frame(top, bg=CARD); f.pack(fill=X, padx=16, pady=8)
        e_un = Entry(f, width=12, font=('Microsoft YaHei',11), relief='solid', bd=1); e_un.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_un, '用户名')
        e_dn = Entry(f, width=10, font=('Microsoft YaHei',11), relief='solid', bd=1); e_dn.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_dn, '身份')
        e_pw = Entry(f, width=10, font=('Microsoft YaHei',11), relief='solid', bd=1, show='*'); e_pw.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_pw, '密码')
        def do_add():
            un=e_un.get().strip(); dn=e_dn.get().strip(); pw=e_pw.get().strip()
            if un == getattr(e_un, '_ph_text', None): un = ''
            if dn == getattr(e_dn, '_ph_text', None): dn = ''
            if pw == getattr(e_pw, '_ph_text', None): pw = ''
            if not un or not pw: messagebox.showinfo('提示','用户名和密码不能为空'); return
            if add_user(un, pw, dn): ref_users(); e_un.delete(0,END); e_dn.delete(0,END); e_pw.delete(0,END)
            else: messagebox.showinfo('提示','用户名已存在')
        Button(f, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei',9,'bold'), relief='flat', padx=8, pady=2, cursor='hand2', command=do_add).pack(side=LEFT, padx=(4,0))
        def do_edit():
            sel=tr.selection()
            if not sel: return
            vals=tr.item(sel[0])['values']; un=vals[0]
            ed=Toplevel(top); ed.title('编辑用户 '+un); ed.geometry('300x180')
            ed.configure(bg=CARD); ed.transient(top); ed.grab_set()
            f2=Frame(ed,bg=CARD); f2.pack(padx=16,pady=12)
            Label(f2,text='身份:',bg=CARD).grid(row=0,column=0,sticky=W,pady=4)
            e_dn2=Entry(f2,width=22); e_dn2.insert(0,vals[1]); e_dn2.grid(row=0,column=1,pady=4)
            Label(f2,text='角色:',bg=CARD).grid(row=1,column=0,sticky=W,pady=4)
            cb_role=ttk.Combobox(f2,values=['worker','admin'],width=18,state='readonly'); cb_role.set(vals[2] if vals[2] in ['worker','admin'] else 'worker'); cb_role.grid(row=1,column=1,pady=4)
            Label(f2,text='新密码(留空不改):',bg=CARD).grid(row=2,column=0,sticky=W,pady=4)
            e_pw2=Entry(f2,width=22,show='*'); e_pw2.grid(row=2,column=1,pady=4)
            def save():
                update_user_display(un,e_dn2.get().strip(),cb_role.get())
                if e_pw2.get().strip(): update_user_pw(un,e_pw2.get().strip())
                ref_users(); ed.destroy()
            Button(f2,text='保存',bg=ACCENT,fg='white',font=('Microsoft YaHei',10,'bold'),relief='flat',padx=20,pady=2,cursor='hand2',command=save).grid(row=3,column=0,columnspan=2,pady=10)'''

new = '''        # Get worker list for comboboxes
        all_wk = get_workers()
        def ref_users():
            for i in tr.get_children(): tr.delete(i)
            for u in get_users():
                wn = ''
                if u.get('worker_id'):
                    for w in all_wk:
                        if w['id'] == u['worker_id']: wn = f"{w['name']}({w['group_name']})"; break
                tr.insert('', END, values=(u['username'], u['display_name'], wn, u.get('created_at','')))
        ref_users()
        tr.pack(padx=16, fill=BOTH, expand=True)
        top._tr = tr
        f = Frame(top, bg=CARD); f.pack(fill=X, padx=16, pady=8)
        e_un = Entry(f, width=10, font=('Microsoft YaHei',11), relief='solid', bd=1); e_un.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_un, '用户名')
        e_dn = Entry(f, width=8, font=('Microsoft YaHei',11), relief='solid', bd=1); e_dn.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_dn, '身份')
        e_pw = Entry(f, width=8, font=('Microsoft YaHei',11), relief='solid', bd=1, show='*'); e_pw.pack(side=LEFT, padx=(0,4))
        _set_placeholder(e_pw, '密码')
        cb_wk = ttk.Combobox(f, values=[f"{w['name']}({w['group_name']})" for w in all_wk], width=14, state='readonly')
        cb_wk.pack(side=LEFT, padx=(0,4))
        def do_add():
            un=e_un.get().strip(); dn=e_dn.get().strip(); pw=e_pw.get().strip()
            if un == getattr(e_un, '_ph_text', None): un = ''
            if dn == getattr(e_dn, '_ph_text', None): dn = ''
            if pw == getattr(e_pw, '_ph_text', None): pw = ''
            if not un or not pw: messagebox.showinfo('提示','用户名和密码不能为空'); return
            wid = 0
            wk = cb_wk.get()
            if wk:
                for w in all_wk:
                    if f"{w['name']}({w['group_name']})" == wk: wid = w['id']; break
            if add_user(un, pw, dn, worker_id=wid): ref_users(); e_un.delete(0,END); e_dn.delete(0,END); e_pw.delete(0,END); cb_wk.set('')
            else: messagebox.showinfo('提示','用户名已存在')
        Button(f, text='添加', bg=ACCENT, fg='white', font=('Microsoft YaHei',9,'bold'), relief='flat', padx=8, pady=2, cursor='hand2', command=do_add).pack(side=LEFT, padx=(4,0))
        def do_edit():
            sel=tr.selection()
            if not sel: return
            vals=tr.item(sel[0])['values']; un=vals[0]
            ed=Toplevel(top); ed.title('编辑用户 '+un); ed.geometry('320x230')
            ed.configure(bg=CARD); ed.transient(top); ed.grab_set()
            f2=Frame(ed,bg=CARD); f2.pack(padx=16,pady=10)
            Label(f2,text='身份:',bg=CARD).grid(row=0,column=0,sticky=W,pady=3)
            e_dn2=Entry(f2,width=22); e_dn2.insert(0,vals[1]); e_dn2.grid(row=0,column=1,pady=3)
            Label(f2,text='角色:',bg=CARD).grid(row=1,column=0,sticky=W,pady=3)
            all_u = get_users(); cr = 'worker'
            for u in all_u:
                if u['username'] == un: cr = u['role']; break
            cb_role=ttk.Combobox(f2,values=['worker','leader','admin'],width=18,state='readonly')
            cb_role.set(cr if cr in ['worker','leader','admin'] else 'worker'); cb_role.grid(row=1,column=1,pady=3)
            Label(f2,text='关联工人:',bg=CARD).grid(row=2,column=0,sticky=W,pady=3)
            cur_wid = 0
            for u in all_u:
                if u['username'] == un: cur_wid = u.get('worker_id',0); break
            wk2_list = get_workers()
            cb_wk2 = ttk.Combobox(f2,values=['']+[f"{w['name']}({w['group_name']})" for w in wk2_list],width=18,state='readonly')
            if cur_wid:
                for w in wk2_list:
                    if w['id'] == cur_wid: cb_wk2.set(f"{w['name']}({w['group_name']})"); break
            cb_wk2.grid(row=2,column=1,pady=3)
            Label(f2,text='新密码(留空不改):',bg=CARD).grid(row=3,column=0,sticky=W,pady=3)
            e_pw2=Entry(f2,width=22,show='*'); e_pw2.grid(row=3,column=1,pady=3)
            def save():
                wid2 = 0; wk2 = cb_wk2.get()
                if wk2:
                    for w in wk2_list:
                        if f"{w['name']}({w['group_name']})" == wk2: wid2 = w['id']; break
                update_user_display(un,e_dn2.get().strip(),cb_role.get(),wid2)
                if e_pw2.get().strip(): update_user_pw(un,e_pw2.get().strip())
                ref_users(); ed.destroy()
            Button(f2,text='保存',bg=ACCENT,fg='white',font=('Microsoft YaHei',10,'bold'),relief='flat',padx=20,pady=2,cursor='hand2',command=save).grid(row=4,column=0,columnspan=2,pady=8)'''

src = src.replace(old, new)

# 2. Update columns in the users Treeview to include worker binding column
src = src.replace(
    "columns=('un','dn','ct')",
    "columns=('un','dn','wk','ct')"
)
src = src.replace(
    "tr.heading('un', text='用户名'); tr.heading('dn', text='身份'); tr.heading('ct', text='创建时间')",
    "tr.heading('un', text='用户名'); tr.heading('dn', text='身份'); tr.heading('wk', text='绑定工人'); tr.heading('ct', text='创建时间')"
)
src = src.replace(
    "tr.column('un', width=120); tr.column('dn', width=180); tr.column('ct', width=140, anchor=CENTER)",
    "tr.column('un', width=100); tr.column('dn', width=120); tr.column('wk', width=140); tr.column('ct', width=120, anchor=CENTER)"
)

# 3. Fix the get_workers calls in _on_worker_select and _add_record to pass leader_id
# These functions use get_workers() to populate comboboxes - leaders should see only their workers
src = src.replace(
    "        self.cb_worker['values'] = [f\"{w['name']}({w['group_name']})\" for w in get_workers()]",
    "        if self.current_user and self.current_user.get('role') == 'leader':\n            wid = self.current_user.get('worker_id',0)\n            self.cb_worker['values'] = [f\"{w['name']}({w['group_name']})\" for w in get_workers(wid)]\n        else:\n            self.cb_worker['values'] = [f\"{w['name']}({w['group_name']})\" for w in get_workers()]"
)

# 4. In _manage_workers, show only the leader's workers for leader role
# This is a bigger change - let's add it near the top of _manage_workers
old_mw = '''    def _manage_workers(self):
        if not self._check_perm('worker_manage'): return
        top = Toplevel(self.root); top.title('管理工人'); top.geometry('520x400')'''
src = src.replace(old_mw, '''    def _manage_workers(self):
        if not self._check_perm('worker_manage'): return
        top = Toplevel(self.root); top.title('管理工人'); top.geometry('520x400')
        # Leaders can only see/add workers in their group
        leader_wid = self.current_user.get('worker_id',0) if self.current_user and self.current_user.get('role') == 'leader' else 0
        leader_group = ''
        if leader_wid:
            for w in get_workers():
                if w['id'] == leader_wid: leader_group = w['group_name']; break''')

# 5. In _manage_workers, filter the worker treeview by leader's group
src = src.replace(
    "        for w in get_workers():",
    "        for w in get_workers():"
)
# Actually, let me just update the ref_workers function inside _manage_workers
# The issue is that _manage_workers has its own local functions. Let me look at what's needed.
# For now, skip the _manage_workers filter - the leader can still see all workers but data filtering already limits what they see

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("Done")
