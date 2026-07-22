"""Remove _change_pw from login, add _change_pw method + button to main UI."""
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()

# 1. Remove _change_pw from login (between line 449 and "e_un.focus()")
old1_start = "        Label(bf, text='  |  ', bg=CARD, fg='#ddd', font=('Microsoft YaHei',8)).pack(side=LEFT)\n"
old1_end = "        e_un.focus()"

start_idx = src.find(old1_start)
end_idx = src.find(old1_end, start_idx)
if start_idx >= 0:
    # Find the last occurrence near e_un.focus()
    # Remove everything from the separator through the _change_pw function and label
    before = src[:start_idx]
    after = src[end_idx:]
    src = before + after

# 2. Replace the bottom bar logout line to add change password button
src = src.replace(
    "Button(bt, text='退出登录', bg=DARK, fg='white', font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, pady=2, cursor='hand2', command=self._logout).pack(side=RIGHT, padx=(4,0))",
    "Button(bt, text='修改密码', bg='#2980b9', fg='white', font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, pady=2, cursor='hand2', command=self._change_pw).pack(side=RIGHT, padx=(4,0))\n        Button(bt, text='退出登录', bg=DARK, fg='white', font=('Microsoft YaHei',9,'bold'), relief='flat', padx=10, pady=2, cursor='hand2', command=self._logout).pack(side=RIGHT, padx=(4,0))"
)

# 3. Add _change_pw method to App class (before _logout)
src = src.replace(
    "    def _logout(self):",
    """    def _change_pw(self):
        un = self.current_user['username'] if self.current_user else ''
        if not un: return
        cp = Toplevel(self.root); cp.title('修改密码'); cp.geometry('320x230')
        cp.configure(bg=CARD); cp.resizable(False, False); cp.grab_set(); cp.transient(self.root)
        xp = self.root.winfo_x()+self.root.winfo_width()//2-160; yp = self.root.winfo_y()+self.root.winfo_height()//2-115
        cp.geometry(f'+{xp}+{yp}')
        Label(cp, text='修改密码', font=('Microsoft YaHei',12,'bold'), bg=CARD, fg=DARK).pack(pady=(12,10))
        ff = Frame(cp, bg=CARD); ff.pack(padx=24)
        Label(ff, text='用户名：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=0,column=0,sticky=W,pady=3)
        eu = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1)
        eu.insert(0, un); eu.config(state='readonly'); eu.grid(row=0,column=1,pady=3)
        Label(ff, text='旧密码：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=1,column=0,sticky=W,pady=3)
        eo = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1, show='*'); eo.grid(row=1,column=1,pady=3)
        Label(ff, text='新密码：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=2,column=0,sticky=W,pady=3)
        en = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1, show='*'); en.grid(row=2,column=1,pady=3)
        Label(ff, text='确认密码：', bg=CARD, font=('Microsoft YaHei',10)).grid(row=3,column=0,sticky=W,pady=3)
        ec = Entry(ff, width=20, font=('Microsoft YaHei',10), relief='solid', bd=1, show='*'); ec.grid(row=3,column=1,pady=3)
        err2 = Label(cp, text='', bg=CARD, fg=RED, font=('Microsoft YaHei',9))
        err2.pack(pady=(4,0))
        def do_change():
            opw = eo.get().strip(); npw = en.get().strip(); cpw = ec.get().strip()
            if not opw or not npw: err2.config(text='请填写完整'); return
            if npw != cpw: err2.config(text='两次新密码不一致'); return
            if len(npw) < 4: err2.config(text='新密码至少4位'); return
            conn = get_conn()
            r = conn.execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
            if not r: err2.config(text='用户不存在'); conn.close(); return
            if not _verify_pw(opw, r['password_hash']): err2.config(text='旧密码错误'); conn.close(); return
            h = _hash_pw(npw)
            conn.execute("UPDATE users SET password_hash=[redacted] WHERE username=?", (h, un))
            conn.commit(); conn.close()
            messagebox.showinfo('成功', '密码修改成功'); cp.destroy()
        Button(cp, text='确认修改', bg=ACCENT, fg='white', font=('Microsoft YaHei',10,'bold'), relief='flat', padx=20, pady=2, cursor='hand2', command=do_change).pack(pady=(6,0))
        eo.focus()

    def _logout(self):"""
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("Done")
