"""工序业务服务"""
from models.process import ProcessRepository
from utils.logger import logger


class ProcessService:
    @staticmethod
    def get_all() -> list[dict]:
        return ProcessRepository.get_all()

    @staticmethod
    def add(material_code: str, process_name: str, unit_price: float) -> bool:
        result = ProcessRepository.add(material_code, process_name, unit_price)
        if result:
            logger.info(f'工序添加成功: {material_code}/{process_name}')
        else:
            logger.warning(f'工序添加失败: {material_code}/{process_name}')
        return result

    @staticmethod
    def update(pid: int, material_code: str, process_name: str, unit_price: float):
        ProcessRepository.update(pid, material_code, process_name, unit_price)
        logger.info(f'工序更新: ID={pid}')

    @staticmethod
    def delete(pid: int):
        ProcessRepository.delete(pid)
        logger.info(f'工序删除: ID={pid}')

    @staticmethod
    def get_process_names() -> list[str]:
        """获取所有不重复的工序名称"""
        return ProcessRepository.get_process_names()
