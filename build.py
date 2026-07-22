"""
一键构建脚本：提交 → 推送 → 打包
用法: python build.py "提交信息"
"""
import os, sys, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
SPEC = os.path.join(ROOT, 'ProductionSystem_v44.spec')

def run(cmd, cwd=ROOT):
    print(f'>> {cmd}')
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-500:] if result.stdout else '')
        print(result.stderr[-500:] if result.stderr else '')
    return result.returncode == 0

def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else '自动更新'

    # 1. 验证编译
    print('=' * 50)
    print('1. 验证编译...')
    if not run(f'python -c "import py_compile; py_compile.compile(\'main.py\', doraise=True); print(\'OK\')"'):
        print('❌ 编译失败'); sys.exit(1)

    # 2. Git 提交
    print('=' * 50)
    print('2. Git 提交...')
    run('git add -A')
    if not run(f'git commit -m "{msg}"'):
        print('⚠️  没有变更需要提交')
    
    # 3. Git 推送
    print('=' * 50)
    print('3. 推送至 GitHub...')
    retry = 3
    while retry > 0:
        if run('git push origin master'):
            break
        retry -= 1
        if retry > 0:
            print('重试中...')
    if retry == 0:
        print('⚠️  推送失败，继续打包')

    # 4. 清理旧构建
    print('=' * 50)
    print('4. 清理旧构建...')
    for d in ['build', 'dist']:
        p = os.path.join(ROOT, d)
        if os.path.exists(p):
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                try:
                    if os.path.isdir(fp): shutil.rmtree(fp)
                    else: os.remove(fp)
                except: pass

    # 5. PyInstaller 打包
    print('=' * 50)
    print('5. 打包 exe...')
    if not run(f'python -m PyInstaller --onefile --windowed --name ProductionSystem_v44 '
               f'--add-data "echarts.min.js;." '
               f'--hidden-import ui.dialogs.material_dialog '
               f'--hidden-import ui.dialogs.worker_dialog '
               f'--hidden-import ui.dialogs.process_dialog '
               f'--hidden-import ui.widgets.crud_dialog_base '
               f'--hidden-import ui.login_view --hidden-import ui.dashboard_view '
               f'--hidden-import services.auth_service --hidden-import services.chart_service '
               f'--hidden-import services.export_service --hidden-import services.stats_service '
               f'--hidden-import services.material_service --hidden-import services.worker_service '
               f'--hidden-import services.process_service '
               f'--hidden-import utils.auth --hidden-import utils.logger '
               f'--hidden-import utils.error_handler main.py'):
        print('❌ 打包失败'); sys.exit(1)

    # 6. 复制 data.db
    shutil.copy2(os.path.join(ROOT, 'data.db'), os.path.join(DIST, 'data.db'))
    
    exe_size = os.path.getsize(os.path.join(DIST, 'ProductionSystem_v44.exe'))
    print(f'=' * 50)
    print(f'✅ 完成！dist/ProductionSystem_v44.exe ({exe_size/1024/1024:.1f} MB)')

if __name__ == '__main__':
    main()
