"""
GitHub 信息渠道适配器
将 GitHubClient 包装为 BaseChannel 实现
"""
from typing import List, Dict, Optional
import os
from datetime import datetime, date, timedelta
from channel_base import BaseChannel
from github_client import GitHubClient
from logger import LOG


class GitHubChannel(BaseChannel):
    """GitHub 信息渠道"""
    
    def __init__(self, name: str = "github", config: Optional[Dict] = None):
        """
        初始化 GitHub 渠道
        
        Args:
            name: 渠道名称
            config: 配置字典，应包含 'token' 键
        """
        super().__init__(name, config)
        token = config.get('token') if config else None
        if not token:
            raise ValueError("GitHub 渠道需要配置 'token'")
        self.github_client = GitHubClient(token)
    
    def fetch_data(self, repo: Optional[str] = None, since: Optional[str] = None, 
                   until: Optional[str] = None, days: int = 1, **kwargs) -> List[Dict]:
        """
        获取 GitHub 仓库更新数据
        
        Args:
            repo: 仓库名称（格式：owner/repo），如果为 None 则从配置读取
            since: 开始日期（ISO 格式）
            until: 结束日期（ISO 格式）
            days: 天数（如果 since 为 None，则使用此参数）
            **kwargs: 其他参数
            
        Returns:
            List[Dict]: 更新数据列表
        """
        if repo is None:
            repo = self.config.get('default_repo')
            if not repo:
                raise ValueError("需要指定仓库名称或配置 'default_repo'")
        
        # 如果没有指定日期，使用 days 参数
        if since is None and days:
            since_date = date.today() - timedelta(days=days)
            since = since_date.isoformat()
        
        updates = self.github_client.fetch_updates(repo, since, until)
        
        # 转换为统一格式
        data = []
        for commit in updates.get('commits', [])[:10]:  # 限制数量
            data.append({
                'type': 'commit',
                'repo': repo,
                'sha': commit.get('sha', '')[:7],
                'message': commit.get('commit', {}).get('message', ''),
                'author': commit.get('commit', {}).get('author', {}).get('name', ''),
                'date': commit.get('commit', {}).get('author', {}).get('date', ''),
                'url': commit.get('html_url', '')
            })
        
        for issue in updates.get('issues', [])[:10]:
            data.append({
                'type': 'issue',
                'repo': repo,
                'number': issue.get('number'),
                'title': issue.get('title', ''),
                'state': issue.get('state', ''),
                'user': issue.get('user', {}).get('login', ''),
                'date': issue.get('closed_at', issue.get('updated_at', '')),
                'url': issue.get('html_url', '')
            })
        
        for pr in updates.get('pull_requests', [])[:10]:
            data.append({
                'type': 'pull_request',
                'repo': repo,
                'number': pr.get('number'),
                'title': pr.get('title', ''),
                'state': pr.get('state', ''),
                'user': pr.get('user', {}).get('login', ''),
                'date': pr.get('merged_at', pr.get('closed_at', pr.get('updated_at', ''))),
                'url': pr.get('html_url', '')
            })
        
        LOG.info(f"从 GitHub 渠道获取了 {len(data)} 条数据")
        return data
    
    def export_data(self, data: List[Dict], output_path: Optional[str] = None, 
                   repo: Optional[str] = None, **kwargs) -> str:
        """
        导出 GitHub 数据到 Markdown 文件
        
        Args:
            data: 要导出的数据
            output_path: 输出文件路径
            repo: 仓库名称
            **kwargs: 其他参数
            
        Returns:
            str: 导出文件路径
        """
        if not data:
            LOG.warning("没有数据可导出")
            return None
        
        if repo is None:
            repo = data[0].get('repo', 'unknown') if data else 'unknown'
        
        if output_path is None:
            today = datetime.now().date().isoformat()
            repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))
            os.makedirs(repo_dir, exist_ok=True)
            output_path = os.path.join(repo_dir, f'{today}.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# GitHub Updates for {repo} ({datetime.now().date()})\n\n")
            
            # 按类型分组
            commits = [d for d in data if d.get('type') == 'commit']
            issues = [d for d in data if d.get('type') == 'issue']
            prs = [d for d in data if d.get('type') == 'pull_request']
            
            if commits:
                f.write("## Commits\n\n")
                for item in commits:
                    f.write(f"- [{item.get('sha', '')}] {item.get('message', '')[:80]} - {item.get('author', '')}\n")
            
            if issues:
                f.write("\n## Issues\n\n")
                for item in issues:
                    f.write(f"- #{item.get('number')} {item.get('title', '')} - {item.get('user', '')}\n")
            
            if prs:
                f.write("\n## Pull Requests\n\n")
                for item in prs:
                    f.write(f"- #{item.get('number')} {item.get('title', '')} - {item.get('user', '')}\n")
        
        LOG.info(f"GitHub 数据已导出到: {output_path}")
        return output_path

