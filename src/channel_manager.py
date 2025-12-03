"""
信息渠道管理器
v1.0: 管理所有注册的信息渠道
"""
from typing import Dict, List, Optional, Type
from logger import LOG
from channel_base import BaseChannel


class ChannelManager:
    """
    信息渠道管理器
    负责注册、管理和调用各种信息渠道
    """
    
    def __init__(self):
        """初始化渠道管理器"""
        self._channels: Dict[str, BaseChannel] = {}
        self._channel_classes: Dict[str, Type[BaseChannel]] = {}
        LOG.info("初始化信息渠道管理器")
    
    def register_channel(self, channel: BaseChannel):
        """
        注册一个渠道实例
        
        Args:
            channel: 渠道实例
        """
        if not isinstance(channel, BaseChannel):
            raise TypeError(f"渠道必须是 BaseChannel 的实例，得到: {type(channel)}")
        
        if channel.name in self._channels:
            LOG.warning(f"渠道 {channel.name} 已存在，将被覆盖")
        
        self._channels[channel.name] = channel
        LOG.info(f"注册信息渠道: {channel.name}")
    
    def register_channel_class(self, name: str, channel_class: Type[BaseChannel], config: Optional[Dict] = None):
        """
        注册一个渠道类（延迟实例化）
        
        Args:
            name: 渠道名称
            channel_class: 渠道类
            config: 渠道配置
        """
        if not issubclass(channel_class, BaseChannel):
            raise TypeError(f"渠道类必须继承自 BaseChannel，得到: {type(channel_class)}")
        
        self._channel_classes[name] = (channel_class, config or {})
        LOG.info(f"注册信息渠道类: {name}")
    
    def get_channel(self, name: str) -> Optional[BaseChannel]:
        """
        获取渠道实例
        
        Args:
            name: 渠道名称
            
        Returns:
            BaseChannel: 渠道实例，如果不存在则返回 None
        """
        # 先查找已实例化的渠道
        if name in self._channels:
            return self._channels[name]
        
        # 如果不存在，尝试从类创建实例
        if name in self._channel_classes:
            channel_class, config = self._channel_classes[name]
            channel = channel_class(name=name, config=config)
            self._channels[name] = channel
            return channel
        
        LOG.warning(f"渠道 {name} 不存在")
        return None
    
    def list_channels(self) -> List[str]:
        """
        列出所有已注册的渠道名称
        
        Returns:
            List[str]: 渠道名称列表
        """
        all_channels = set(self._channels.keys()) | set(self._channel_classes.keys())
        return sorted(list(all_channels))
    
    def get_channel_info(self, name: str) -> Optional[Dict]:
        """
        获取渠道信息
        
        Args:
            name: 渠道名称
            
        Returns:
            Dict: 渠道信息，如果不存在则返回 None
        """
        channel = self.get_channel(name)
        if channel:
            return channel.get_channel_info()
        return None
    
    def fetch_data(self, channel_name: str, **kwargs) -> List[Dict]:
        """
        从指定渠道获取数据
        
        Args:
            channel_name: 渠道名称
            **kwargs: 传递给渠道的额外参数
            
        Returns:
            List[Dict]: 数据列表
        """
        channel = self.get_channel(channel_name)
        if not channel:
            raise ValueError(f"渠道 {channel_name} 不存在")
        
        LOG.info(f"从渠道 {channel_name} 获取数据")
        return channel.fetch_data(**kwargs)
    
    def export_data(self, channel_name: str, data: Optional[List[Dict]] = None, **kwargs) -> str:
        """
        从指定渠道导出数据
        
        Args:
            channel_name: 渠道名称
            data: 要导出的数据（如果为 None，则从渠道获取）
            **kwargs: 传递给渠道的额外参数
            
        Returns:
            str: 导出文件的路径
        """
        channel = self.get_channel(channel_name)
        if not channel:
            raise ValueError(f"渠道 {channel_name} 不存在")
        
        if data is None:
            data = channel.fetch_data(**kwargs)
        
        LOG.info(f"从渠道 {channel_name} 导出数据")
        return channel.export_data(data, **kwargs)
    
    def remove_channel(self, name: str) -> bool:
        """
        移除渠道
        
        Args:
            name: 渠道名称
            
        Returns:
            bool: 是否成功移除
        """
        removed = False
        if name in self._channels:
            del self._channels[name]
            removed = True
        if name in self._channel_classes:
            del self._channel_classes[name]
            removed = True
        
        if removed:
            LOG.info(f"移除信息渠道: {name}")
        
        return removed

