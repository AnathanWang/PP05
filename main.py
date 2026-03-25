import tkinter as tk
from tkinter import messagebox
import threading

from db import (
    authenticate_user,
    list_users,
    add_user,
    delete_user,
    unlock_user,
    ensure_schema,
    increment_failed,
    update_user,
    get_user,
)
import random

from PIL import Image, ImageTk
_HAS_PIL = True

TILE_SIZE = 100


class PuzzleCaptcha(tk.Frame):
    def __init__(self, parent, image_dir='capchaImage'):
        super().__init__(parent)
        self.image_dir = image_dir
        self.correct = [0, 1, 2, 3]
        self.state = list(self.correct)
        self.images = []
        self.buttons = []
        self.selected = None
        self.solved = False
        self.tile_size = TILE_SIZE
        self._load_images()
        self._build_ui()
        self.shuffle()
        self.bind('<Configure>', self._on_resize)

    def _load_images(self):
        self.images.clear()
        for i in range(1, 5):
            path = f"{self.image_dir}/{i}.png"
            try:
                if _HAS_PIL:
                    pil = Image.open(path).convert('RGBA')
                    pil = pil.resize((self.tile_size, self.tile_size), Image.LANCZOS)
                    img = ImageTk.PhotoImage(pil)
                else:
                    raw = tk.PhotoImage(file=path)
                    w = raw.width()
                    h = raw.height()
                    factor = max(1, int(max(w, h) / max(1, self.tile_size)))
                    if factor > 1:
                        img = raw.subsample(factor, factor)
                    else:
                        img = raw
            except Exception:
                img = None
            self.images.append(img)

    def _build_ui(self):
        for pos in range(4):
            btn = tk.Button(self, command=lambda p=pos: self.on_click(p))
            r = pos // 2
            c = pos % 2
            btn.grid(row=r, column=c, padx=2, pady=2, ipadx=2, ipady=2, sticky='nsew')
            self.buttons.append(btn)
        sh = tk.Button(self, text='Перемешать', command=self.shuffle)
        sh.grid(row=2, column=0, columnspan=2, pady=(6, 0), sticky='ew')
        for i in range(2):
            self.grid_columnconfigure(i, weight=1)
            self.grid_rowconfigure(i, weight=1)

    def _update_buttons(self):
        for pos, btn in enumerate(self.buttons):
            tile = self.state[pos]
            img = self.images[tile]
            if img:
                btn.config(image=img, text='')
                btn.image = img
            else:
                btn.config(text=str(tile + 1), image='')

            if self.selected is not None and self.selected == pos:
                btn.config(relief='sunken')
            else:
                btn.config(relief='raised')

    def on_click(self, pos):
        if self.solved:
            return
        if self.selected is None:
            self.selected = pos
            self._update_buttons()
            return
        if self.selected == pos:
            self.selected = None
            self._update_buttons()
            return
        self.state[self.selected], self.state[pos] = self.state[pos], self.state[self.selected]
        self.selected = None
        self._update_buttons()
        self._check_solved()

    def shuffle(self):
        import random as _r
        _r.shuffle(self.state)
        if self.state == self.correct:
            _r.shuffle(self.state)
        self.solved = False
        self.selected = None
        self._update_buttons()

    def _check_solved(self):
        if self.state == self.correct:
            self.solved = True
            for b in self.buttons:
                b.config(state='disabled')

    def is_solved(self):
        return self.solved

    def _on_resize(self, event):
        try:
            w = max(1, self.winfo_width())
            h = max(1, self.winfo_height())
            avail_w = max(20, (w - 8) // 2)
            avail_h = max(20, (h - 40) // 2)
            new_size = min(avail_w, avail_h)
            if abs(new_size - getattr(self, 'tile_size', TILE_SIZE)) >= 8:
                self.tile_size = new_size
                self._load_images()
                self._update_buttons()
        except Exception:
            pass


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Авторизация")
        self.minsize(360, 240)
        self.resizable(True, True)
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Логин:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.e_user = tk.Entry(self)
        self.e_user.grid(row=0, column=1, padx=10, pady=(10, 0), sticky='ew')

        tk.Label(self, text="Пароль:").grid(row=1, column=0, sticky="w", padx=10, pady=(6, 0))
        self.e_pass = tk.Entry(self, show='*')
        self.e_pass.grid(row=1, column=1, padx=10, pady=(6, 0), sticky='ew')
        self.captcha = PuzzleCaptcha(self)
        self.captcha.grid(row=2, column=0, columnspan=2, pady=(8, 0), sticky='nsew')

        self.login_btn = tk.Button(self, text="Войти", command=self.do_Login)
        self.login_btn.grid(row=3, column=0, columnspan=2, pady=12, sticky='ew')

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

    def do_Login(self):
        username = self.e_user.get().strip()
        password = self.e_pass.get().strip()
        if not username or not password:
            messagebox.showwarning("Внимание", "Пожалуйста, введите логин и пароль")
            return
        if not getattr(self, 'captcha', None) or not self.captcha.is_solved():
            messagebox.showwarning('Капча', 'Пожалуйста, соберите пазл')
            if username:
                try:
                    attempts, blocked = increment_failed(username)
                    if blocked:
                        messagebox.showerror('Заблокировано', 'Вы заблокированы. Обратитесь к администратору')
                except Exception:
                    pass
            return

        self.login_btn.config(state='disabled')

        def worker(u, p):
            try:
                res = authenticate_user(u, p)
                self.after(0, self._on_auth_result, u, res)
            except Exception as e:
                self.after(0, self._on_result, False, e)

        threading.Thread(target=worker, args=(username, password), daemon=True).start()

    def _on_result(self, ok, error):
        self.login_btn.config(state='normal')
        if error:
            messagebox.showerror('Ошибка БД', str(error))
            return

    def _on_auth_result(self, username, res: dict):
        self.login_btn.config(state='normal')
        if not res:
            messagebox.showerror('Ошибка', 'Ошибка аутентификации')
            return
        if res.get('blocked'):
            messagebox.showerror('Заблокировано', 'Вы заблокированы. Обратитесь к администратору')
            return
        if res.get('ok'):
            messagebox.showinfo('Успех', 'Вы успешно авторизовались')
            if res.get('role') == 'admin':
                self.open_user_manager()
            return
        reason = res.get('reason')
        attempts = res.get('attempts', 0)
        if reason == 'wrong_password':
            if attempts >= 3:
                messagebox.showerror('Заблокировано', 'Вы заблокированы. Обратитесь к администратору')
            else:
                messagebox.showerror('Ошибка', 'Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные')
            return
        if reason == 'no_user':
            messagebox.showerror('Ошибка', 'Вы ввели неверный логин или пароль. Пожалуйста проверьте ещё раз введенные данные')
            return

    def _gen_captcha(self):
        return ''.join(str(random.randint(0, 9)) for _ in range(4))

    def open_user_manager(self):
        um = UserManager(self)
        um.grab_set()


class UserManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('Управление пользователями')
        self.minsize(380, 240)
        self.resizable(True, True)
        self.create_widgets()
        self.refresh()

    def create_widgets(self):
        self.user_listbox = tk.Listbox(self)
        self.user_listbox.pack(fill='both', expand=True, padx=10, pady=10)

        frm = tk.Frame(self)
        frm.pack(fill='x', padx=10)
        tk.Label(frm, text='Логин').grid(row=0, column=0)
        self.nu = tk.Entry(frm)
        self.nu.grid(row=0, column=1)
        tk.Label(frm, text='Пароль').grid(row=1, column=0)
        self.np = tk.Entry(frm)
        self.np.grid(row=1, column=1)
        tk.Label(frm, text='Роль').grid(row=2, column=0)
        self.role_var = tk.StringVar(value='user')
        self.role_menu = tk.OptionMenu(frm, self.role_var, 'user', 'admin')
        self.role_menu.grid(row=2, column=1)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=8)
        tk.Button(btn_frame, text='Добавить', command=self.add_user_ui).pack(side='left')
        tk.Button(btn_frame, text='Загрузить', command=self.load_user_ui).pack(side='left')
        tk.Button(btn_frame, text='Изменить', command=self.update_user_ui).pack(side='left')
        tk.Button(btn_frame, text='Удалить', command=self.delete_user_ui).pack(side='left')
        tk.Button(btn_frame, text='Разблокировать', command=self.unblock_user_ui).pack(side='left')
        tk.Button(btn_frame, text='Обновить', command=self.refresh).pack(side='left')

    def refresh(self):
        try:
            users = list_users()
        except Exception as e:
            messagebox.showerror('DB error', str(e))
            return
        self.user_listbox.delete(0, 'end')
        for u in users:
            self.user_listbox.insert('end', u)

    def add_user_ui(self):
        username = self.nu.get().strip()
        password = self.np.get().strip()
        role = self.role_var.get()
        if not username or not password:
            messagebox.showwarning('Ввод', 'Введите логин и пароль')
            return
        try:
            ok = add_user(username, password, role)
            if ok:
                messagebox.showinfo('Добавлено', 'Пользователь добавлен')
                self.refresh()
            else:
                messagebox.showwarning('Существует', 'Пользователь с таким логином уже существует')
        except Exception as e:
            messagebox.showerror('Ошибка БД', str(e))

    def unblock_user_ui(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showwarning('Select', 'Select a user to unblock')
            return
        username = self.user_listbox.get(sel[0])
        try:
            unlock_user(username)
            messagebox.showinfo('ОК', 'Пользователь разблокирован')
            self.refresh()
        except Exception as e:
            messagebox.showerror('Ошибка БД', str(e))

    def load_user_ui(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showwarning('Select', 'Select a user to load')
            return
        username = self.user_listbox.get(sel[0])
        try:
            u = get_user(username)
            if not u:
                messagebox.showwarning('Не найден', 'Пользователь не найден')
                return
            self.nu.delete(0, 'end')
            self.nu.insert(0, u['username'])
            self.np.delete(0, 'end')
            self.role_var.set(u.get('role') or 'user')
        except Exception as e:
            messagebox.showerror('Ошибка БД', str(e))

    def update_user_ui(self):
        username = self.nu.get().strip()
        password = self.np.get().strip()
        role = self.role_var.get()
        if not username:
            messagebox.showwarning('Ввод', 'Введите логин')
            return
        try:
            pwd = password if password else None
            ok = update_user(username, password=pwd, role=role)
            if ok:
                messagebox.showinfo('Обновлено', 'Данные пользователя обновлены')
                self.refresh()
            else:
                messagebox.showwarning('Не изменено', 'Нет изменений или пользователь не найден')
        except Exception as e:
            messagebox.showerror('Ошибка БД', str(e))

    def delete_user_ui(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showwarning('Выбор', 'Выберите пользователя для удаления')
            return
        username = self.user_listbox.get(sel[0])
        if not messagebox.askyesno('Подтвердите', f'Удалить пользователя {username}?'):
            return
        try:
            ok = delete_user(username)
            if ok:
                messagebox.showinfo('Удалено', 'Пользователь удалён')
                self.refresh()
            else:
                messagebox.showwarning('Не найден', 'Пользователь не найден')
        except Exception as e:
            messagebox.showerror('Ошибка БД', str(e))


if __name__ == "__main__":
    try:
        ensure_schema()
    except Exception as e:
        print('Failed to ensure DB schema:', e)
    app = LoginWindow()
    app.mainloop()
