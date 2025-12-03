"""
信息渠道模块
v1.0: 包含所有内置信息渠道的实现
"""
from .github_channel import GitHubChannel
from .hacker_news_channel import HackerNewsChannel
from .reddit_channel import RedditChannel

__all__ = ['GitHubChannel', 'HackerNewsChannel', 'RedditChannel']

