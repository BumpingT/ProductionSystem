"""工序业务服务"""
from models.process import ProcessRepository
from models.record import RecordRepository
from utils.logger import logger


class ProcessService:
    @staticmethod
    def get_all() -> list[dict]:
        return ProcessRepository.get_all()

    @staticmethod
    def add(material: str, process_name: str, unit_price: float) -> bool:
        result = ProcessRepository.add(material, process_name, unit_price)
        if result:
            logger.info(f'工序添加成功: {material}/{process_name}')
        else:
            logger.warning(f'工序添加失败: {material}/{process_name}')
        return result

    @staticmethod
    def update(pid: int, material: str, process_name: str, unit_price: float):
        """更新工序信息"""
        ProcessRepository.update(pid, material, process_name, unit_price)
        logger.info(f'工序更新: ID={pid}')

    @staticmethod
    def delete(pid: int):
        ProcessRepository.delete(pid)
        logger.info(f'工序删除: ID={pid}')

    @staticmethod
    def get_worker_processes(worker_id: int) -> list[int]:
        return RecordRepository.get_worker_processes(worker_id)

    @staticmethod
    def assign_worker(worker_id: int, process_id: int):
        RecordRepository.assign_worker_process(worker_id, process_id)
        logger.info(f'工人工序分配: worker={worker_id}, process={process_id}')

    @staticmethod
    def unassign_worker(worker_id: int, process_id: int):
        RecordRepository.unassign_worker_process(worker_id, process_id)
        logger.info(f'工人工序取消分配: worker={worker_id}, process={process_id}')
