"""密码哈希与认证工具"""
import hashlib, secrets, base64, json, os
from config import LOGIN_CRED_PATH


def hash_password(pw: str) -> str:
    """PBKDF2-SHA256 哈希，返回 salt(32位hex) + hash(64位hex)"""
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return salt + h


def verify_password(pw: str, stored: str) -> bool:
    """验证密码"""
    salt = stored[:32]
    h = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return (salt + h) == stored


def save_credential(username: str, password: str):
    """记住密码（Base64 编码）"""
    try:
        data = json.dumps({'u': username, 'p': base64.b64encode(password.encode()).decode()})
        with open(LOGIN_CRED_PATH, 'w') as f:
            f.write(data)
    except Exception:
        pass


def load_credential() -> dict | None:
    """读取记住的密码"""
    try:
        d = json.loads(open(LOGIN_CRED_PATH).read())
        d['p'] = base64.b64decode(d['p']).decode()
        return d
    except Exception:
        return None


def clear_credential():
    """清除记住的密码"""
    try:
        if os.path.exists(LOGIN_CRED_PATH):
            os.remove(LOGIN_CRED_PATH)
    except Exception:
        pass
