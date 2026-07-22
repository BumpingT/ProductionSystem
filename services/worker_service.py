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
            logger.info(f'工人添加成功: {name}')
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
