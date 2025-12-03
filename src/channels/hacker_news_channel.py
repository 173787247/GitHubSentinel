"""
Hacker News 信息渠道适配器
将 HackerNewsClient 包装为 BaseChannel 实现
"""
from typing import List, Dict, Optional
import os
from datetime import datetime
from channel_base import BaseChannel
from hacker_news_client import HackerNewsClient
from logger import LOG


class HackerNewsChannel(BaseChannel):
    """Hacker News 信息渠道"""
    
    def __init__(self, name: str = "hacker_news", config: Optional[Dict] = None):
        """
        初始化 Hacker News 渠道
        
        Args:
            name: 渠道名称
            config: 配置字典
        """
        super().__init__(name, config)
        self.hn_client = HackerNewsClient()
    
    def fetch_data(self, limit: int = 30, **kwargs) -> List[Dict]:
        """
        获取 Hacker News 热门新闻
        
        Args:
            limit: 获取数量限制
            **kwargs: 其他参数
            
        Returns:
            List[Dict]: 新闻数据列表
        """
        stories = self.hn_client.fetch_top_stories()
        
        # 转换为统一格式
        data = []
        for idx, story in enumerate(stories[:limit], start=1):
            data.append({
                'type': 'story',
                'rank': idx,
                'title': story.get('title', ''),
                'link': story.get('link', ''),
                'date': datetime.now().isoformat()
            })
        
        LOG.info(f"从 Hacker News 渠道获取了 {len(data)} 条数据")
        return data
    
    def export_data(self, data: List[Dict], output_path: Optional[str] = None, **kwargs) -> str:
        """
        导出 Hacker News 数据到 Markdown 文件
        
        Args:
            data: 要导出的数据
            output_path: 输出文件路径
            **kwargs: 其他参数
            
        Returns:
            str: 导出文件路径
        """
        if not data:
            LOG.warning("没有数据可导出")
            return None
        
        if output_path is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            hour_str = datetime.now().strftime('%H')
            dir_path = os.path.join('hacker_news', date_str)
            os.makedirs(dir_path, exist_ok=True)
            output_path = os.path.join(dir_path, f'{hour_str}.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Hacker News Top Stories ({datetime.now().strftime('%Y-%m-%d %H:00')})\n\n")
            for item in data:
                rank = item.get('rank', '')
                title = item.get('title', '')
                link = item.get('link', '')
                f.write(f"{rank}. [{title}]({link})\n")
        
        LOG.info(f"Hacker News 数据已导出到: {output_path}")
        return output_path

