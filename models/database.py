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
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '',
            UNIQUE(code, version)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            group_name TEXT NOT NULL DEFAULT ''
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_code TEXT NOT NULL,
            process_name TEXT NOT NULL,
            unit_price REAL NOT NULL DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
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
        c.execute("""CREATE TABLE IF NOT EXISTS leader_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            leader_username TEXT NOT NULL,
            worker_id INTEGER NOT NULL,
            UNIQUE(leader_username, worker_id)
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
            pass
        # 兼容旧数据库：创建 leader_workers 表（如果不存在）
        try:
            c.execute("""CREATE TABLE IF NOT EXISTS leader_workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leader_username TEXT NOT NULL,
                worker_id INTEGER NOT NULL,
                UNIQUE(leader_username, worker_id)
            )""")
        except Exception:
            pass
        # 兼容旧数据库：删除旧的 worker_processes 表
        try:
            c.execute("DROP TABLE IF EXISTS worker_processes")
        except Exception:
            pass
        # 兼容：确保 admin 拥有 ALL_PERMS 中所有权限
        from config import ALL_PERMS
        for pk in ALL_PERMS:
            c.execute("INSERT OR IGNORE INTO user_permissions (username,perm_key,allowed) VALUES (?,?,1)",
                      ('admin', pk))
        # 兼容旧数据库：processes 表 material -> material_code
        try:
            c.execute("SELECT material_code FROM processes LIMIT 1")
        except Exception:
            # 旧表没有 material_code 列，添加并迁移数据
            try:
                c.execute("ALTER TABLE processes ADD COLUMN material_code TEXT NOT NULL DEFAULT ''")
                c.execute("UPDATE processes SET material_code = material WHERE material_code = ''")
                logger.info('数据库迁移: processes.material -> material_code')
            except Exception:
                pass
        # 兼容旧数据库：materials 表添加 version 列
        try:
            c.execute("SELECT version FROM materials LIMIT 1")
        except Exception:
            try:
                c.execute("ALTER TABLE materials ADD COLUMN version TEXT NOT NULL DEFAULT ''")
                logger.info('数据库迁移: materials 添加 version 列')
            except Exception:
                pass
        # 兼容旧数据库：materials 表添加 code 列（旧版只有 name/price）
        try:
            c.execute("SELECT code FROM materials LIMIT 1")
        except Exception:
            try:
                c.execute("ALTER TABLE materials ADD COLUMN code TEXT NOT NULL DEFAULT ''")
                # 将 name 的值复制到 code（旧版 data.db 把物料编号存在 name 里）
                c.execute("UPDATE materials SET code = name WHERE code = ''")
                logger.info('数据库迁移: materials 添加 code 列')
            except Exception:
                pass
        # 兼容旧数据库：materials 表去掉 code UNIQUE 约束，改为 UNIQUE(code, version)
        try:
            # 检查是否是旧结构（有 UNIQUE(code) 约束则无法插入相同 code 不同 version）
            c.execute("INSERT INTO materials (code,name,version) VALUES ('@@migrate_test@@','@@migrate_test@@','v1')")
            c.execute("INSERT INTO materials (code,name,version) VALUES ('@@migrate_test@@','@@migrate_test@@','v2')")
            c.execute("DELETE FROM materials WHERE code='@@migrate_test@@'")
        except Exception:
            # 发生了 UNIQUE 冲突，说明是旧结构，需要重建表
            try:
                c.execute("DELETE FROM materials WHERE code='@@migrate_test@@'")
            except:
                pass
            try:
                c.execute("""CREATE TABLE materials_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '',
                    UNIQUE(code, version)
                )""")
                c.execute("INSERT INTO materials_new (id,code,name,version) SELECT id,code,name,version FROM materials")
                c.execute("DROP TABLE materials")
                c.execute("ALTER TABLE materials_new RENAME TO materials")
                logger.info('数据库迁移: materials 重建表(去掉 code UNIQUE)')
            except Exception as e:
                logger.warning(f'数据库迁移 materials 失败: {e}')
        # 兼容旧数据库：processes 表去掉 UNIQUE(material_code, process_name) 约束
        try:
            c.execute("INSERT INTO processes (material_code,process_name,unit_price) VALUES ('@@migrate_test@@','@@migrate_test@@',0)")
            c.execute("INSERT INTO processes (material_code,process_name,unit_price) VALUES ('@@migrate_test@@','@@migrate_test@@',0)")
            c.execute("DELETE FROM processes WHERE material_code='@@migrate_test@@'")
        except Exception:
            try:
                c.execute("DELETE FROM processes WHERE material_code='@@migrate_test@@'")
            except:
                pass
            try:
                c.execute("""CREATE TABLE processes_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    material_code TEXT NOT NULL,
                    process_name TEXT NOT NULL,
                    unit_price REAL NOT NULL DEFAULT 0
                )""")
                c.execute("INSERT INTO processes_new (id,material_code,process_name,unit_price) SELECT id,material_code,process_name,unit_price FROM processes")
                c.execute("DROP TABLE processes")
                c.execute("ALTER TABLE processes_new RENAME TO processes")
                logger.info('数据库迁移: processes 重建表(去掉 UNIQUE)')
            except Exception as e:
                logger.warning(f'数据库迁移 processes 失败: {e}')

        conn.commit()
        logger.info('数据库初始化完成')

    @classmethod
    def _seed_data(cls, c):
        # 班组
        groups = ['装配组', '绕线组', '测试组', '包装组', '质检组', '维修组']
        for g in groups:
            try:
                c.execute("INSERT INTO groups (name) VALUES (?)", (g,))
            except Exception:
                pass

        # 工人（关联班组）
        c.executemany("INSERT INTO workers (name,group_name) VALUES (?,?)", [
            ('张建国','装配组'),('李明辉','装配组'),('王大力','装配组'),
            ('赵振华','绕线组'),('陈志强','绕线组'),
            ('刘国栋','测试组'),('孙国平','测试组'),
            ('周建军','包装组'),('吴国良','包装组'),
            ('郑伟民','质检组'),('黄志刚','维修组')
        ])

        # 电气物料（编号 + 名称 + 版本）
        c.executemany("INSERT OR IGNORE INTO materials (code,name,version) VALUES (?,?,?)", [
            ('TR-001','变压器','V1.0'),('TR-002','变压器','V2.0'),
            ('CONT-01','接触器','A型'),('CONT-02','接触器','B型'),
            ('CB-001','断路器','1P'),('CB-002','断路器','2P'),('CB-003','断路器','3P'),
            ('RE-001','继电器','标准型'),('RE-002','继电器','加强型'),
            ('CAB-01','电缆','YJV-3×4'),('CAB-02','电缆','YJV-3×6'),
            ('SW-001','开关','单控'),('SW-002','开关','双控'),
            ('FUSE-01','熔断器','RT18-32'),('FUSE-02','熔断器','RT18-63'),
            ('CAP-01','电容器','BCMJ-0.45'),('CT-001','互感器','LMK-0.66'),
            ('BUS-01','母线','TMY-40×4'),('BOX-01','配电箱','PZ30-8'),
            ('CAB-03','电缆','YJV-4×10'),
        ])

        # 工序（关联物料编号）
        c.executemany("INSERT OR IGNORE INTO processes (material_code,process_name,unit_price) VALUES (?,?,?)", [
            ('TR-001','绕线',1.5),('TR-001','组装',2.0),('TR-001','测试',1.8),
            ('TR-002','绕线',1.8),('TR-002','组装',2.2),('TR-002','测试',2.0),
            ('CONT-01','组装',2.5),('CONT-01','测试',2.0),
            ('CB-001','组装',1.5),('CB-001','测试',1.8),
            ('CB-002','组装',1.8),('CB-002','测试',2.0),
            ('CB-003','组装',2.0),('CB-003','测试',2.2),
            ('RE-001','组装',1.2),('RE-001','测试',1.5),
            ('CAB-01','裁切',1.0),('CAB-01','剥线',1.2),
            ('SW-001','组装',1.5),('SW-001','测试',1.8),
            ('FUSE-01','组装',1.0),('FUSE-01','测试',1.2),
            ('CAP-01','组装',1.5),('CAP-01','测试',1.8),
            ('BOX-01','组装',3.0),('BOX-01','接线',2.5),('BOX-01','测试',2.0),
        ])

        # 生产记录（保持不变）
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
