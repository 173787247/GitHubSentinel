# src/github_client.py

import requests  # 导入requests库用于HTTP请求
from datetime import datetime, date, timedelta  # 导入日期处理模块
import os  # 导入os模块用于文件和目录操作
from logger import LOG  # 导入日志模块

class GitHubClient:
    def __init__(self, token):
        self.token = token  # GitHub API令牌
        self.headers = {'Authorization': f'token {self.token}'}  # 设置HTTP头部认证信息

    def fetch_updates(self, repo, since=None, until=None):
        # 获取指定仓库的更新，可以指定开始和结束日期
        updates = {
            'commits': self.fetch_commits(repo, since, until),  # 获取提交记录
            'issues': self.fetch_issues(repo, since, until),  # 获取问题
            'pull_requests': self.fetch_pull_requests(repo, since, until),  # 获取拉取请求
            'releases': self.fetch_releases(repo, since, until)  # 获取发布版本（新增）
        }
        return updates

    def fetch_commits(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Commits")
        url = f'https://api.github.com/repos/{repo}/commits'  # 构建获取提交的API URL
        params = {}
        if since:
            params['since'] = since  # 如果指定了开始日期，添加到参数中
        if until:
            params['until'] = until  # 如果指定了结束日期，添加到参数中

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            return response.json()  # 返回JSON格式的数据
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Commits 失败：{str(e)}")
            LOG.error(f"响应详情：{response.text if 'response' in locals() else '无响应数据可用'}")
            return []  # Handle failure case

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

    def fetch_releases(self, repo, since=None, until=None):
        """
        获取指定仓库的 Releases，支持时间段筛选。
        
        :param repo: 仓库名称，格式为 owner/repo
        :param since: 起始时间（ISO 8601 格式），可选
        :param until: 结束时间（ISO 8601 格式），可选
        :return: Releases 列表
        """
        LOG.debug(f"准备获取 {repo} 的 Releases")
        url = f'https://api.github.com/repos/{repo}/releases'  # 构建获取发布的API URL
        
        try:
            response = requests.get(url, headers=self.headers, params={'per_page': 100}, timeout=10)
            response.raise_for_status()
            releases = response.json()
            
            # 如果指定了时间段，进行筛选
            if since or until:
                filtered_releases = []
                for release in releases:
                    published_at = release.get('published_at')
                    if not published_at:
                        continue
                    
                    # 转换为 datetime 进行比较
                    from datetime import datetime
                    try:
                        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        since_date = datetime.fromisoformat(since.replace('Z', '+00:00')) if since else None
                        until_date = datetime.fromisoformat(until.replace('Z', '+00:00')) if until else None
                        
                        # 检查是否在时间范围内
                        if since_date and pub_date < since_date:
                            continue
                        if until_date and pub_date > until_date:
                            continue
                        
                        filtered_releases.append(release)
                    except (ValueError, AttributeError) as e:
                        LOG.warning(f"解析发布时间失败: {published_at}, 错误: {e}")
                        continue
                
                return filtered_releases
            
            return releases
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Releases 失败：{str(e)}")
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
