"""
测试信息渠道基类
v1.0: 测试 BaseChannel 和 ChannelManager
"""
import unittest
import os
import tempfile
from unittest.mock import Mock, patch
from src.channel_base import BaseChannel
from src.channel_manager import ChannelManager


class MockChannel(BaseChannel):
    """测试用的模拟渠道"""
    
    def fetch_data(self, **kwargs):
        return [
            {'type': 'test', 'title': 'Test Item 1', 'content': 'Content 1'},
            {'type': 'test', 'title': 'Test Item 2', 'content': 'Content 2'}
        ]
    
    def export_data(self, data, output_path=None, **kwargs):
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), 'test_export.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Test Export\n\n")
            for item in data:
                f.write(f"- {item.get('title', 'N/A')}\n")
        
        return output_path


class TestBaseChannel(unittest.TestCase):
    """测试 BaseChannel 基类"""
    
    def setUp(self):
        self.channel = MockChannel(name="test_channel", config={'key': 'value'})
    
    def test_channel_initialization(self):
        """测试渠道初始化"""
        self.assertEqual(self.channel.name, "test_channel")
        self.assertEqual(self.channel.config, {'key': 'value'})
    
    def test_get_channel_info(self):
        """测试获取渠道信息"""
        info = self.channel.get_channel_info()
        self.assertEqual(info['name'], "test_channel")
        self.assertEqual(info['type'], "MockChannel")
        self.assertIn('config', info)
    
    def test_validate_config(self):
        """测试配置验证"""
        self.assertTrue(self.channel.validate_config())
    
    def test_fetch_data(self):
        """测试获取数据"""
        data = self.channel.fetch_data()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['title'], 'Test Item 1')
    
    def test_export_data(self):
        """测试导出数据"""
        data = self.channel.fetch_data()
        output_path = self.channel.export_data(data)
        self.assertTrue(os.path.exists(output_path))
        
        # 清理
        if os.path.exists(output_path):
            os.remove(output_path)


class TestChannelManager(unittest.TestCase):
    """测试 ChannelManager"""
    
    def setUp(self):
        self.manager = ChannelManager()
        self.channel = MockChannel(name="test_channel")
    
    def test_register_channel(self):
        """测试注册渠道"""
        self.manager.register_channel(self.channel)
        self.assertIn("test_channel", self.manager.list_channels())
    
    def test_get_channel(self):
        """测试获取渠道"""
        self.manager.register_channel(self.channel)
        retrieved = self.manager.get_channel("test_channel")
        self.assertEqual(retrieved, self.channel)
    
    def test_list_channels(self):
        """测试列出渠道"""
        self.manager.register_channel(self.channel)
        channels = self.manager.list_channels()
        self.assertIn("test_channel", channels)
    
    def test_fetch_data(self):
        """测试从渠道获取数据"""
        self.manager.register_channel(self.channel)
        data = self.manager.fetch_data("test_channel")
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
    
    def test_export_data(self):
        """测试导出数据"""
        self.manager.register_channel(self.channel)
        output_path = self.manager.export_data("test_channel")
        self.assertTrue(os.path.exists(output_path))
        
        # 清理
        if os.path.exists(output_path):
            os.remove(output_path)
    
    def test_remove_channel(self):
        """测试移除渠道"""
        self.manager.register_channel(self.channel)
        self.assertTrue(self.manager.remove_channel("test_channel"))
        self.assertNotIn("test_channel", self.manager.list_channels())
    
    def test_get_nonexistent_channel(self):
        """测试获取不存在的渠道"""
        channel = self.manager.get_channel("nonexistent")
        self.assertIsNone(channel)


if __name__ == '__main__':
    unittest.main()

