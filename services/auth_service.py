"""认证与授权服务"""
from models.user import UserRepository
from utils.auth import verify_password, hash_password
from utils.logger import logger


class AuthService:
    @staticmethod
    def login(username: str, password: str) -> dict | None:
        """验证登录，成功返回用户信息，失败返回 None"""
        user = UserRepository.get_by_username(username)
        if not user:
            logger.warning(f'登录失败：用户 {username} 不存在')
            return None
        if not verify_password(password, user['password_hash']):
            logger.warning(f'登录失败：用户 {username} 密码错误')
            return None
        logger.info(f'用户 {username} 登录成功')
        return user

    @staticmethod
    def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """修改密码，返回 (是否成功, 消息)"""
        user = UserRepository.get_by_username(username)
        if not user:
            return False, '用户不存在'
        if not verify_password(old_password, user['password_hash']):
            return False, '旧密码错误'
        if len(new_password) < 4:
            return False, '新密码至少4位'
        if verify_password(new_password, user['password_hash']):
            return False, '新密码不能与旧密码相同'
        UserRepository.update_password(username, new_password)
        logger.info(f'用户 {username} 密码已修改')
        return True, '密码修改成功'

    @staticmethod
    def get_permissions(username: str) -> dict:
        """获取用户权限字典"""
        return UserRepository.get_permissions(username)

    @staticmethod
    def has_permission(username: str, perm_key: str) -> bool:
        """检查用户是否有某项权限"""
        user = UserRepository.get_by_username(username)
        if user and user['role'] == 'admin':
            return True
        perms = UserRepository.get_permissions(username)
        return bool(perms.get(perm_key, 0))
