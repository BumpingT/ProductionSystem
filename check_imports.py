"""检查所有模块的导入"""
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

modules = [
    'config',
    'utils.auth',
    'utils.logger',
    'utils.error_handler',
    'models.database',
    'models.material',
    'models.worker',
    'models.process',
    'models.record',
    'models.user',
    'services.auth_service',
    'services.material_service',
    'services.worker_service',
    'services.process_service',
    'services.stats_service',
    'services.chart_service',
    'services.export_service',
    'ui.widgets.crud_dialog_base',
    'ui.dialogs.material_dialog',
    'ui.dialogs.worker_dialog',
    'ui.dialogs.process_dialog',
    'ui.dialogs.user_dialog',
    'ui.login_view',
    'ui.dashboard_view',
    'main',
]

for m in modules:
    try:
        __import__(m)
        print(f'[OK] {m}')
    except Exception as e:
        print(f'[FAIL] {m}: {e}')
