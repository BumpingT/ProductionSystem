"""
数据库连接管理 + 初始化
"""
import sqlite3
from utils.logger import logger
from config import DB_PATH


class Database:
    """连接管理，使用单例模式"""
    _conn: sqlite3.Connection | None = None

    @classmethod
    def get_conn(cls) -> sqlite3.Connection:
        if cls._conn is None:
            cls._conn = sqlite3.connect(DB_PATH)
            cls._conn.row_factory = sqlite3.Row
            cls._conn.execute("PRAGMA journal_mode=WAL")
            cls._conn.execute("PRAGMA foreign_keys=ON")
            logger.info(f'数据库已连接: {DB_PATH}')
        return cls._conn

    @classmethod
    def close(cls):
        if cls._conn:
            cls._conn.close()
            cls._conn = None
            logger.info('数据库已关闭')

    @classmethod
    def init_db(cls):
        """初始化数据库表结构和种子数据"""
        conn = cls.get_conn()
        c = conn.cursor()

        # 建表
        c.execute("""CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            group_name TEXT NOT NULL DEFAULT ''
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material TEXT NOT NULL,
            process_name TEXT NOT NULL,
            unit_price REAL NOT NULL DEFAULT 0,
            UNIQUE(material, process_name)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS worker_processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            process_id INTEGER NOT NULL,
            UNIQUE(worker_id, process_id)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL DEFAULT 0,
            process_id INTEGER NOT NULL DEFAULT 0,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            record_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'worker',
            worker_id INTEGER DEFAULT 0,
            group_name TEXT NOT NULL DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            perm_key TEXT NOT NULL,
            allowed INTEGER NOT NULL DEFAULT 0,
            UNIQUE(username, perm_key)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        # 种子数据
        seeded = c.execute("SELECT value FROM settings WHERE key=?", ("seeded",)).fetchone()
        if not seeded:
            cls._seed_data(c)
            c.execute("INSERT INTO settings (key,value) VALUES (?,?)", ("seeded", "1"))

        # 默认管理员
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            cls._seed_admin(c)

        # 兼容旧数据库：添加 group_name 列
        try:
            c.execute("ALTER TABLE users ADD COLUMN group_name TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass  # 列已存在，忽略

        conn.commit()
        logger.info('数据库初始化完成')

    @classmethod
    def _seed_data(cls, c):
        c.executemany("INSERT INTO workers (name,group_name) VALUES (?,?)", [
            ('张三','切割组'),('李四','组装组'),('王五','切割组'),
            ('赵六','上色组'),('孙七','包装组'),('吴九','检验组')
        ])
        c.executemany("INSERT OR IGNORE INTO materials (name,price) VALUES (?,?)", [
            ('A-1001',5.5),('A-1002',6.0),('B-2001',8.0),('B-2002',8.5),
            ('C-3001',6.0),('C-3002',7.0),('D-4001',12.0),('D-4002',10.0),
            ('E-5001',11.0),('E-5002',9.5)
        ])
        c.executemany("INSERT OR IGNORE INTO processes (material,process_name,unit_price) VALUES (?,?,?)", [
            ('A-1001','切割',1.5),('A-1001','打磨',2.0),('A-1001','组装',1.8),
            ('B-2001','切割',2.0),('B-2001','上色',2.5),('B-2001','包装',1.2),
            ('C-3001','切割',1.8),('C-3001','打磨',2.2),('C-3001','组装',2.0),
            ('D-4001','切割',2.5),('D-4001','打磨',3.0),('D-4001','抛光',2.8),
            ('E-5001','切割',3.0),('E-5001','组装',2.5),('E-5001','检验',1.5)
        ])
        c.executemany("INSERT OR IGNORE INTO worker_processes (worker_id,process_id) VALUES (?,?)", [
            (1,1),(1,2),(1,3),(2,4),(2,5),(3,1),(3,2),
            (4,5),(4,11),(5,6),(5,8),(6,9),(6,12),(6,15)
        ])
        c.executemany("INSERT INTO records (worker_id,process_id,quantity,unit_price,record_date) VALUES (?,?,?,?,?)", [
            (1,1,50,1.5,'2026-07-20'),(1,2,30,2.0,'2026-07-20'),
            (2,4,35,2.5,'2026-07-20'),(3,1,60,1.5,'2026-07-20'),
            (1,1,40,1.5,'2026-07-21'),(1,3,25,1.8,'2026-07-21'),
            (2,5,42,1.2,'2026-07-21'),(4,5,28,2.5,'2026-07-21'),
            (3,2,55,2.0,'2026-07-22'),(5,6,45,1.2,'2026-07-22'),
            (6,9,32,2.2,'2026-07-22'),(1,2,35,2.0,'2026-07-22'),
            (2,4,48,2.5,'2026-07-23'),(3,1,62,1.5,'2026-07-23'),
            (4,11,20,3.0,'2026-07-23'),(5,8,38,1.2,'2026-07-23')
        ])

    @classmethod
    def _seed_admin(cls, c):
        from utils.auth import hash_password
        pw = hash_password('admin123')
        c.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES (?,?,?,?)",
                  ('admin',pw,'系统管理员','admin'))
        from config import ALL_PERMS
        for pk in ALL_PERMS:
            c.execute("INSERT OR IGNORE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,1)",
                      ('admin',pk))
