"""
AuthService 单元测试
"""
import pytest
from services.auth_service import AuthService
from models.user import UserRepository
from config import ALL_PERMS


class TestAuthService:
    """认证服务测试"""

    def test_login_admin_success(self):
        """测试管理员登录成功"""
        user = AuthService.login('admin', 'admin123')
        assert user is not None
        assert user['username'] == 'admin'
        assert user['role'] == 'admin'

    def test_login_wrong_password(self):
        """测试密码错误"""
        user = AuthService.login('admin', 'wrong_password')
        assert user is None

    def test_login_nonexistent_user(self):
        """测试不存在的用户"""
        user = AuthService.login('nonexistent', 'password')
        assert user is None

    def test_login_empty_username(self):
        """测试空用户名"""
        user = AuthService.login('', 'password')
        assert user is None

    def test_login_empty_password(self):
        """测试空密码"""
        user = AuthService.login('admin', '')
        assert user is None

    def test_change_password_success(self):
        """测试修改密码成功"""
        success, msg = AuthService.change_password('admin', 'admin123', 'newpass123')
        assert success
        assert '成功' in msg
        # 验证新密码可用
        user = AuthService.login('admin', 'newpass123')
        assert user is not None
        # 旧密码不可用
        user = AuthService.login('admin', 'admin123')
        assert user is None
        # 恢复密码
        AuthService.change_password('admin', 'newpass123', 'admin123')

    def test_change_password_wrong_old(self):
        """测试旧密码错误"""
        success, msg = AuthService.change_password('admin', 'wrong_old', 'newpass123')
        assert not success
        assert '旧密码错误' in msg

    def test_change_password_too_short(self):
        """测试新密码太短"""
        success, msg = AuthService.change_password('admin', 'admin123', '12')
        assert not success
        assert '至少4位' in msg

    def test_admin_has_all_permissions(self):
        """测试管理员拥有所有权限"""
        for perm in ALL_PERMS:
            assert AuthService.has_permission('admin', perm), f"admin should have {perm}"

    def test_nonexistent_user_no_permission(self):
        """测试不存在用户无权限"""
        assert not AuthService.has_permission('nonexistent', 'record_add')

    def test_login_returns_correct_data(self):
        """测试登录返回正确的数据结构"""
        user = AuthService.login('admin', 'admin123')
        assert 'id' in user
        assert 'username' in user
        assert 'password_hash' in user
        assert 'display_name' in user
        assert 'role' in user
        assert user['role'] == 'admin'

    def test_get_permissions_admin(self):
        """测试获取管理员权限"""
        perms = AuthService.get_permissions('admin')
        assert isinstance(perms, dict)
        for perm in ALL_PERMS:
            assert perm in perms
