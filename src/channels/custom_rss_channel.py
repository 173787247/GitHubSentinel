"""
自定义 RSS 信息渠道示例
v1.0: 演示如何创建自定义信息渠道
"""
from typing import List, Dict, Optional
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from channel_base import BaseChannel
from logger import LOG


class CustomRSSChannel(BaseChannel):
    """
    自定义 RSS 信息渠道示例
    可以从任何 RSS Feed 获取信息
    """
    
    def __init__(self, name: str = "rss", config: Optional[Dict] = None):
        """
        初始化 RSS 渠道
        
        Args:
            name: 渠道名称
            config: 配置字典，应包含 'feed_url' 键
        """
        super().__init__(name, config)
        self.feed_url = config.get('feed_url') if config else None
        if not self.feed_url:
            raise ValueError("RSS 渠道需要配置 'feed_url'")
    
    def fetch_data(self, limit: int = 20, **kwargs) -> List[Dict]:
        """
        从 RSS Feed 获取数据
        
        Args:
            limit: 获取数量限制
            **kwargs: 其他参数
            
        Returns:
            List[Dict]: 数据列表
        """
        try:
            response = requests.get(self.feed_url, timeout=10)
            response.raise_for_status()
            
            # 解析 RSS XML
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:limit]
            
            data = []
            for idx, item in enumerate(items, start=1):
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')
                
                data.append({
                    'type': 'rss_item',
                    'rank': idx,
                    'title': title.text if title else '',
                    'link': link.text if link else '',
                    'description': description.text if description else '',
                    'date': pub_date.text if pub_date else datetime.now().isoformat(),
                    'source': self.name
                })
            
            LOG.info(f"从 RSS 渠道 {self.name} 获取了 {len(data)} 条数据")
            return data
            
        except Exception as e:
            LOG.error(f"获取 RSS 数据失败: {str(e)}")
            return []
    
    def export_data(self, data: List[Dict], output_path: Optional[str] = None, **kwargs) -> str:
        """
        导出 RSS 数据到 Markdown 文件
        
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
            dir_path = os.path.join('rss_feeds', self.name, date_str)
            os.makedirs(dir_path, exist_ok=True)
            hour_str = datetime.now().strftime('%H')
            output_path = os.path.join(dir_path, f'{hour_str}.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# RSS Feed: {self.name} ({datetime.now().strftime('%Y-%m-%d %H:00')})\n\n")
            f.write(f"Source: {self.feed_url}\n\n")
            for item in data:
                rank = item.get('rank', '')
                title = item.get('title', '')
                link = item.get('link', '')
                description = item.get('description', '')
                f.write(f"{rank}. [{title}]({link})\n")
                if description:
                    f.write(f"   {description[:200]}...\n")
                f.write("\n")
        
        LOG.info(f"RSS 数据已导出到: {output_path}")
        return output_path

