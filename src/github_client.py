# src/github_client.py

import requests  # 导入requests库用于HTTP请求
from datetime import datetime, date, timedelta  # 导入日期处理模块
import os  # 导入os模块用于文件和目录操作
import time  # 导入time模块用于处理速率限制
from logger import LOG  # 导入日志模块

class GitHubClient:
    def __init__(self, token):
        self.token = token  # GitHub API令牌
        # 支持两种认证格式：Bearer（推荐）和 token（兼容旧格式）
        if token.startswith('ghp_') or token.startswith('github_pat_'):
            # 新的个人访问令牌格式
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            # 兼容旧格式
            self.headers = {'Authorization': f'token {self.token}'}
        # 添加Accept头，使用最新API版本
        self.headers['Accept'] = 'application/vnd.github.v3+json'

    def fetch_updates(self, repo, since=None, until=None):
        # 获取指定仓库的更新，可以指定开始和结束日期
        updates = {
            'commits': self.fetch_commits(repo, since, until),  # 获取提交记录
            'issues': self.fetch_issues(repo, since, until),  # 获取问题
            'pull_requests': self.fetch_pull_requests(repo, since, until)  # 获取拉取请求
        }
        return updates

    def _handle_rate_limit(self, response):
        """处理GitHub API速率限制"""
        if response.status_code == 403:
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
            rate_limit_reset = response.headers.get('X-RateLimit-Reset', '0')
            if rate_limit_remaining == '0':
                reset_time = datetime.fromtimestamp(int(rate_limit_reset))
                wait_seconds = int(rate_limit_reset) - int(time.time())
                LOG.warning(f"GitHub API速率限制，将在 {wait_seconds} 秒后重置（{reset_time}）")
                if wait_seconds > 0 and wait_seconds < 3600:  # 最多等待1小时
                    time.sleep(wait_seconds + 1)
                    return True
        return False

    def _format_date(self, date_str):
        """将日期字符串格式化为ISO 8601格式（带时间）"""
        if not date_str:
            return None
        # 如果已经是完整的ISO格式，直接返回
        if 'T' in date_str:
            return date_str
        # 否则添加时间部分
        return f"{date_str}T00:00:00Z"

    def fetch_commits(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Commits")
        url = f'https://api.github.com/repos/{repo}/commits'  # 构建获取提交的API URL
        params = {'per_page': 100}  # 增加每页返回数量
        if since:
            params['since'] = self._format_date(since)  # 格式化日期
        if until:
            params['until'] = self._format_date(until)  # 格式化日期

        all_commits = []
        page = 1
        
        try:
            while True:
                params['page'] = page
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                # 处理速率限制
                if self._handle_rate_limit(response):
                    continue
                
                response.raise_for_status()  # 检查请求是否成功
                commits = response.json()
                
                if not commits:  # 没有更多数据
                    break
                    
                all_commits.extend(commits)
                
                # 检查是否还有更多页面
                if 'rel="next"' not in response.headers.get('Link', ''):
                    break
                    
                page += 1
                
            LOG.info(f"成功获取 {repo} 的 {len(all_commits)} 条 Commits")
            return all_commits
        except requests.exceptions.RequestException as e:
            LOG.error(f"从 {repo} 获取 Commits 失败：{str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                LOG.error(f"响应状态码：{e.response.status_code}")
                LOG.error(f"响应详情：{e.response.text[:500]}")
            return []  # Handle failure case
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Commits 时发生未知错误：{str(e)}")
            return []

    def fetch_issues(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Issues。")
        url = f'https://api.github.com/repos/{repo}/issues'  # 构建获取问题的API URL
        params = {'state': 'closed', 'since': since, 'until': until}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Issues 失败：{str(e)}")
            LOG.error(f"响应详情：{response.text if 'response' in locals() else '无响应数据可用'}")
            return []

    def fetch_pull_requests(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Pull Requests。")
        url = f'https://api.github.com/repos/{repo}/pulls'  # 构建获取拉取请求的API URL
        params = {'state': 'closed', 'since': since, 'until': until}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()  # 确保成功响应
            return response.json()
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Pull Requests 失败：{str(e)}")
            LOG.error(f"响应详情：{response.text if 'response' in locals() else '无响应数据可用'}")
            return []

    def export_daily_progress(self, repo):
        LOG.debug(f"[准备导出项目进度]：{repo}")
        today = datetime.now().date().isoformat()  # 获取今天的日期
        updates = self.fetch_updates(repo, since=today)  # 获取今天的更新数据
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))  # 构建存储路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        
        file_path = os.path.join(repo_dir, f'{today}.md')  # 构建文件路径
        with open(file_path, 'w') as file:
            file.write(f"# Daily Progress for {repo} ({today})\n\n")
            file.write("\n## Issues Closed Today\n")
            for issue in updates['issues']:  # 写入今天关闭的问题
                file.write(f"- {issue['title']} #{issue['number']}\n")
        
        LOG.info(f"[{repo}]项目每日进展文件生成： {file_path}")  # 记录日志
        return file_path

    def export_progress_by_date_range(self, repo, days):
        today = date.today()  # 获取当前日期
        since = today - timedelta(days=days)  # 计算开始日期
        
        updates = self.fetch_updates(repo, since=since.isoformat(), until=today.isoformat())  # 获取指定日期范围内的更新
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))  # 构建目录路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        
        # 更新文件名以包含日期范围
        date_str = f"{since}_to_{today}"
        file_path = os.path.join(repo_dir, f'{date_str}.md')  # 构建文件路径
        
        with open(file_path, 'w') as file:
            file.write(f"# Progress for {repo} ({since} to {today})\n\n")
            file.write(f"\n## Issues Closed in the Last {days} Days\n")
            for issue in updates['issues']:  # 写入在指定日期内关闭的问题
                file.write(f"- {issue['title']} #{issue['number']}\n")
        
        LOG.info(f"[{repo}]项目最新进展文件生成： {file_path}")  # 记录日志
        return file_path
