"""工人业务服务"""
from models.worker import WorkerRepository
from utils.logger import logger


class WorkerService:
    @staticmethod
    def get_all() -> list[dict]:
        return WorkerRepository.get_all()

    @staticmethod
    def add(name: str, group: str = '') -> bool:
        result = WorkerRepository.add(name, group)
        if result:
            logger.info(f'工人添加成功: {name} ({group})')
        else:
            logger.warning(f'工人添加失败(可能已存在): {name}')
        return result

    @staticmethod
    def update(wid: int, name: str, group: str):
        WorkerRepository.update(wid, name, group)
        logger.info(f'工人更新: ID={wid}')

    @staticmethod
    def delete(wid: int):
        WorkerRepository.delete(wid)
        logger.info(f'工人删除: ID={wid}')

    # ── 班组管理 ──
    @staticmethod
    def get_groups() -> list[str]:
        return WorkerRepository.get_groups()

    @staticmethod
    def add_group(group_name: str) -> bool:
        result = WorkerRepository.add_group(group_name)
        if result:
            logger.info(f'班组添加成功: {group_name}')
        else:
            logger.warning(f'班组添加失败: {group_name}')
        return result

    @staticmethod
    def delete_group(group_name: str) -> bool:
        result = WorkerRepository.delete_group(group_name)
        if result:
            logger.info(f'班组删除成功: {group_name}')
        else:
            logger.warning(f'班组删除失败: {group_name}')
        return result
