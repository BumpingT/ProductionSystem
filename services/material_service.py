"""物料业务服务"""
from models.material import MaterialRepository
from utils.logger import logger


class MaterialService:
    @staticmethod
    def get_all() -> list[dict]:
        return MaterialRepository.get_all()

    @staticmethod
    def add(code: str, name: str, version: str = '') -> bool:
        result = MaterialRepository.add(code, name, version)
        if result:
            logger.info(f'物料添加成功: {code} ({name}-{version})')
        else:
            logger.warning(f'物料添加失败(可能已存在): {code}')
        return result

    @staticmethod
    def update(mid: int, code: str, name: str, version: str):
        MaterialRepository.update(mid, code, name, version)
        logger.info(f'物料更新: ID={mid}')

    @staticmethod
    def delete(mid: int):
        MaterialRepository.delete(mid)
        logger.info(f'物料删除: ID={mid}')

    @staticmethod
    def search(keyword: str) -> list[dict]:
        """搜索物料"""
        return MaterialRepository.search(keyword)

    @staticmethod
    def get_by_code(code: str) -> dict | None:
        return MaterialRepository.get_by_code(code)
