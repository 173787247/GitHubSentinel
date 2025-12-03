"""
测试内置渠道实现
v1.0: 测试 GitHubChannel 和 HackerNewsChannel
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile


class TestGitHubChannel(unittest.TestCase):
    """测试 GitHubChannel"""
    
    @patch('src.channels.github_channel.GitHubClient')
    def setUp(self, mock_github_client):
        """设置测试环境"""
        self.mock_client = Mock()
        mock_github_client.return_value = self.mock_client
        
        from src.channels.github_channel import GitHubChannel
        self.channel = GitHubChannel(
            name="github",
            config={'token': 'test_token'}
        )
    
    def test_channel_initialization(self):
        """测试渠道初始化"""
        self.assertEqual(self.channel.name, "github")
        self.assertIsNotNone(self.channel.github_client)
    
    @patch('src.channels.github_channel.date')
    def test_fetch_data(self, mock_date):
        """测试获取数据"""
        from datetime import date
        mock_date.today.return_value = date(2024, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
        
        # 模拟 GitHub API 响应
        self.channel.github_client.fetch_updates = Mock(return_value={
            'commits': [
                {
                    'sha': 'abc123',
                    'commit': {
                        'message': 'Test commit',
                        'author': {'name': 'Test User', 'date': '2024-01-01'}
                    },
                    'html_url': 'https://github.com/test/repo/commit/abc123'
                }
            ],
            'issues': [],
            'pull_requests': []
        })
        
        data = self.channel.fetch_data(repo="test/repo", days=1)
        self.assertIsInstance(data, list)
        if data:
            self.assertEqual(data[0]['type'], 'commit')
            self.assertEqual(data[0]['repo'], 'test/repo')
    
    def test_export_data(self):
        """测试导出数据"""
        test_data = [
            {
                'type': 'commit',
                'repo': 'test/repo',
                'sha': 'abc123',
                'message': 'Test commit',
                'author': 'Test User',
                'date': '2024-01-01',
                'url': 'https://github.com/test/repo/commit/abc123'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            output_path = f.name
        
        try:
            result_path = self.channel.export_data(test_data, output_path=output_path)
            self.assertTrue(os.path.exists(result_path))
            
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('test/repo', content)
                self.assertIn('Test commit', content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


class TestHackerNewsChannel(unittest.TestCase):
    """测试 HackerNewsChannel"""
    
    @patch('src.channels.hacker_news_channel.HackerNewsClient')
    def setUp(self, mock_hn_client):
        """设置测试环境"""
        self.mock_client = Mock()
        mock_hn_client.return_value = self.mock_client
        
        from src.channels.hacker_news_channel import HackerNewsChannel
        self.channel = HackerNewsChannel(name="hacker_news")
    
    def test_channel_initialization(self):
        """测试渠道初始化"""
        self.assertEqual(self.channel.name, "hacker_news")
        self.assertIsNotNone(self.channel.hn_client)
    
    def test_fetch_data(self):
        """测试获取数据"""
        # 模拟 Hacker News 数据
        self.channel.hn_client.fetch_top_stories = Mock(return_value=[
            {'title': 'Test Story 1', 'link': 'https://example.com/1'},
            {'title': 'Test Story 2', 'link': 'https://example.com/2'}
        ])
        
        data = self.channel.fetch_data(limit=10)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['type'], 'story')
        self.assertEqual(data[0]['title'], 'Test Story 1')
    
    def test_export_data(self):
        """测试导出数据"""
        test_data = [
            {
                'type': 'story',
                'rank': 1,
                'title': 'Test Story',
                'link': 'https://example.com',
                'date': '2024-01-01'
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            output_path = f.name
        
        try:
            result_path = self.channel.export_data(test_data, output_path=output_path)
            self.assertTrue(os.path.exists(result_path))
            
            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Test Story', content)
                self.assertIn('https://example.com', content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == '__main__':
    unittest.main()

