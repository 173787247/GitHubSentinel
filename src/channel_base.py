"""
信息渠道基类
v1.0: 支持自定义信息渠道的扩展系统
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from logger import LOG


class BaseChannel(ABC):
    """
    信息渠道基类
    所有自定义信息渠道都应该继承此类并实现抽象方法
    """
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        """
        初始化渠道
        
        Args:
            name: 渠道名称（唯一标识）
            config: 渠道配置字典
        """
        self.name = name
        self.config = config or {}
        LOG.info(f"初始化信息渠道: {name}")
    
    @abstractmethod
    def fetch_data(self, **kwargs) -> List[Dict]:
        """
        获取数据（抽象方法，必须实现）
        
        Args:
            **kwargs: 额外的参数（如日期范围、数量限制等）
            
        Returns:
            List[Dict]: 数据列表，每个字典包含获取的信息
        """
        pass
    
    @abstractmethod
    def export_data(self, data: List[Dict], output_path: Optional[str] = None) -> str:
        """
        导出数据到文件（抽象方法，必须实现）
        
        Args:
            data: 要导出的数据列表
            output_path: 输出文件路径（可选）
            
        Returns:
            str: 导出文件的路径
        """
        pass
    
    def get_channel_info(self) -> Dict:
        """
        获取渠道信息
        
        Returns:
            Dict: 渠道信息字典
        """
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'config': self.config
        }
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        return True
    
    def __str__(self):
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self):
        return self.__str__()

