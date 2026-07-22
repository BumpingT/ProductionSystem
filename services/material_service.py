"""物料业务服务"""
from models.material import MaterialRepository
from utils.logger import logger


class MaterialService:
    @staticmethod
    def get_all() -> list[dict]:
        return MaterialRepository.get_all()

    @staticmethod
    def add(name: str, price: float = 0) -> bool:
        result = MaterialRepository.add(name, price)
        if result:
            logger.info(f'物料添加成功: {name}')
        else:
            logger.warning(f'物料添加失败(可能已存在): {name}')
        return result

    @staticmethod
    def update(mid: int, name: str, price: float):
        MaterialRepository.update(mid, name, price)
        logger.info(f'物料更新: ID={mid}')

    @staticmethod
    def delete(mid: int):
        MaterialRepository.delete(mid)
        logger.info(f'物料删除: ID={mid}')
