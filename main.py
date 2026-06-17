import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout


# ---------------- BANCO ----------------

conn = sqlite3.connect("diario_ultra.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS notas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    conteudo TEXT,
    data TEXT
)
""")

conn.commit()


# ---------------- LOGIN ----------------

class Login(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        layout.add_widget(Label(text="Diário Ultra", font_size=32))

        self.user = TextInput(hint_text="Usuário", multiline=False)
        self.pwd = TextInput(hint_text="Senha", password=True, multiline=False)

        layout.add_widget(self.user)
        layout.add_widget(self.pwd)

        btn = Button(text="Entrar")
        btn.bind(on_press=self.login)

        layout.add_widget(btn)

        self.add_widget(layout)

    def login(self, instance):
        if self.user.text == "admin" and self.pwd.text == "test":
            self.manager.current = "app"


# ---------------- APP ----------------

class Diario(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.nota_atual = None

        main = BoxLayout(orientation="horizontal")

        # LEFT
        self.left = BoxLayout(orientation="vertical", size_hint=(0.3, 1))

        self.search = TextInput(hint_text="Buscar", size_hint_y=None, height=40)
        self.left.add_widget(self.search)

        btn_search = Button(text="Buscar", size_hint_y=None, height=40)
        btn_search.bind(on_press=self.pesquisar)
        self.left.add_widget(btn_search)

        btn_new = Button(text="Nova Nota", size_hint_y=None, height=40)
        btn_new.bind(on_press=self.nova_nota)
        self.left.add_widget(btn_new)

        self.scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))

        self.scroll.add_widget(self.list_layout)
        self.left.add_widget(self.scroll)

        # RIGHT
        right = BoxLayout(orientation="vertical")

        self.titulo = TextInput(hint_text="Título", size_hint_y=None, height=40)
        self.conteudo = TextInput()

        right.add_widget(self.titulo)
        right.add_widget(self.conteudo)

        btn_save = Button(text="Salvar", size_hint_y=None, height=50)
        btn_save.bind(on_press=self.salvar)

        btn_del = Button(text="Excluir", size_hint_y=None, height=50)
        btn_del.bind(on_press=self.excluir)

        right.add_widget(btn_save)
        right.add_widget(btn_del)

        main.add_widget(self.left)
        main.add_widget(right)

        self.add_widget(main)

        self.carregar()

    # ----------------

    def nova_nota(self, instance):
        self.nota_atual = None
        self.titulo.text = ""
        self.conteudo.text = ""

    # ----------------

    def salvar(self, instance):

        titulo = self.titulo.text or "Sem título"
        conteudo = self.conteudo.text
        data = datetime.now().strftime("%d/%m/%Y %H:%M")

        if self.nota_atual:
            cursor.execute("""
                UPDATE notas
                SET titulo=?, conteudo=?
                WHERE id=?
            """, (titulo, conteudo, self.nota_atual))
        else:
            cursor.execute("""
                INSERT INTO notas (titulo, conteudo, data)
                VALUES (?,?,?)
            """, (titulo, conteudo, data))

        conn.commit()
        self.carregar()

    # ----------------

    def abrir(self, id_nota):

        cursor.execute("SELECT titulo, conteudo FROM notas WHERE id=?", (id_nota,))
        nota = cursor.fetchone()

        if nota:
            self.nota_atual = id_nota
            self.titulo.text = nota[0]
            self.conteudo.text = nota[1]

    # ----------------

    def carregar(self):

        self.list_layout.clear_widgets()

        cursor.execute("SELECT id, titulo FROM notas ORDER BY id DESC")

        for n in cursor.fetchall():
            btn = Button(text=n[1], size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, i=n[0]: self.abrir(i))
            self.list_layout.add_widget(btn)

    # ----------------

    def pesquisar(self, instance):

        termo = self.search.text

        self.list_layout.clear_widgets()

        cursor.execute("SELECT id, titulo FROM notas WHERE titulo LIKE ?", (f"%{termo}%",))

        for n in cursor.fetchall():
            btn = Button(text=n[1], size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, i=n[0]: self.abrir(i))
            self.list_layout.add_widget(btn)

    # ----------------

    def excluir(self, instance):

        if not self.nota_atual:
            return

        cursor.execute("DELETE FROM notas WHERE id=?", (self.nota_atual,))
        conn.commit()

        self.nova_nota(None)
        self.carregar()


# ---------------- APP ROOT ----------------

class DiarioApp(App):

    def build(self):

        sm = ScreenManager()

        sm.add_widget(Login(name="login"))
        sm.add_widget(Diario(name="app"))

        return sm


if __name__ == "__main__":
    DiarioApp().run()