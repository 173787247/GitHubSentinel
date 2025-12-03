"""
Reddit 信息渠道
使用 Reflection Agent 生成的代码实现
"""
from typing import List, Dict, Optional
import os
import requests
from datetime import datetime
from channel_base import BaseChannel
from logger import LOG


class RedditChannel(BaseChannel):
    """
    Reddit 信息渠道
    从 Reddit 获取热门帖子或特定 subreddit 的内容
    """
    
    def __init__(self, name: str = "reddit", config: Optional[Dict] = None):
        """
        初始化 Reddit 渠道
        
        Args:
            name: 渠道名称
            config: 配置字典，应包含 'subreddit' 键（可选，默认为 'all'）
        """
        super().__init__(name, config)
        self.subreddit = config.get('subreddit', 'all') if config else 'all'
        self.base_url = "https://www.reddit.com"
        LOG.info(f"初始化 Reddit 渠道: {name}, subreddit: {self.subreddit}")
    
    def fetch_data(self, limit: int = 25, sort: str = "hot", **kwargs) -> List[Dict]:
        """
        从 Reddit 获取数据
        
        Args:
            limit: 获取数量限制（最大 100）
            sort: 排序方式（hot, new, top, rising）
            **kwargs: 其他参数
            
        Returns:
            List[Dict]: 数据列表
        """
        try:
            # Reddit JSON API 端点
            url = f"{self.base_url}/r/{self.subreddit}/{sort}.json"
            params = {
                "limit": min(limit, 100),  # Reddit API 限制
                "raw_json": 1
            }
            
            # 设置 User-Agent（Reddit API 要求）
            headers = {
                "User-Agent": "GitHubSentinel/1.0 (Information Channel Bot)"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            result = []
            for idx, post_data in enumerate(posts[:limit], start=1):
                post = post_data.get('data', {})
                
                result.append({
                    'type': 'reddit_post',
                    'rank': idx,
                    'title': post.get('title', ''),
                    'author': post.get('author', ''),
                    'subreddit': post.get('subreddit', ''),
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'url': post.get('url', ''),
                    'permalink': f"{self.base_url}{post.get('permalink', '')}",
                    'created_utc': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat() if post.get('created_utc') else None,
                    'selftext': post.get('selftext', '')[:500],  # 限制长度
                    'source': self.name
                })
            
            LOG.info(f"从 Reddit 渠道 {self.name} 获取了 {len(result)} 条数据")
            return result
            
        except requests.exceptions.RequestException as e:
            LOG.error(f"获取 Reddit 数据失败 (网络错误): {str(e)}")
            return []
        except Exception as e:
            LOG.error(f"获取 Reddit 数据失败: {str(e)}")
            return []
    
    def export_data(self, data: List[Dict], output_path: Optional[str] = None, **kwargs) -> str:
        """
        导出 Reddit 数据到 Markdown 文件
        
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
            dir_path = os.path.join('reddit_feeds', self.name, date_str)
            os.makedirs(dir_path, exist_ok=True)
            hour_str = datetime.now().strftime('%H')
            output_path = os.path.join(dir_path, f'{hour_str}.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Reddit Feed: r/{self.subreddit} ({datetime.now().strftime('%Y-%m-%d %H:00')})\n\n")
            f.write(f"Source: {self.base_url}/r/{self.subreddit}\n\n")
            
            for item in data:
                rank = item.get('rank', '')
                title = item.get('title', '')
                permalink = item.get('permalink', '')
                author = item.get('author', '')
                score = item.get('score', 0)
                num_comments = item.get('num_comments', 0)
                selftext = item.get('selftext', '')
                created = item.get('created_utc', '')
                
                f.write(f"## {rank}. {title}\n\n")
                f.write(f"- **作者**: u/{author}\n")
                f.write(f"- **分数**: {score} | **评论数**: {num_comments}\n")
                if created:
                    f.write(f"- **发布时间**: {created}\n")
                f.write(f"- **链接**: [查看原文]({permalink})\n")
                if selftext:
                    f.write(f"\n**内容预览**:\n{selftext}\n")
                f.write("\n---\n\n")
        
        LOG.info(f"Reddit 数据已导出到: {output_path}")
        return output_path

