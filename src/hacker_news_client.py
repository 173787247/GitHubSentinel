import requests  # 导入requests库用于HTTP请求
from bs4 import BeautifulSoup  # 导入BeautifulSoup库用于解析HTML内容
from datetime import datetime  # 导入datetime模块用于获取日期和时间
import os  # 导入os模块用于文件和目录操作
from logger import LOG  # 导入日志模块

class HackerNewsClient:
    def __init__(self):
        self.url = 'https://news.ycombinator.com/'  # Hacker News的URL

    def fetch_top_stories(self):
        """获取Hacker News的热门新闻"""
        LOG.debug("准备获取Hacker News的热门新闻。")
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            top_stories = self.parse_stories(response.text)  # 解析新闻数据
            return top_stories
        except Exception as e:
            LOG.error(f"获取Hacker News的热门新闻失败：{str(e)}")
            return []

    def parse_stories(self, html_content):
        """解析Hacker News的HTML内容"""
        LOG.debug("解析Hacker News的HTML内容。")
        soup = BeautifulSoup(html_content, 'html.parser')
        stories = soup.find_all('tr', class_='athing')  # 查找所有包含新闻的<tr>标签

        top_stories = []
        for story in stories:
            title_tag = story.find('span', class_='titleline')
            if title_tag:
                link_tag = title_tag.find('a')
                if link_tag:
                    title = link_tag.text
                    link = link_tag['href']
                    # 处理相对链接
                    if link.startswith('item?'):
                        link = f"https://news.ycombinator.com/{link}"
                    elif not link.startswith('http'):
                        link = f"https://news.ycombinator.com/{link}"
                    top_stories.append({'title': title, 'link': link})

        LOG.info(f"成功解析 {len(top_stories)} 条Hacker News新闻。")
        return top_stories

    def export_top_stories(self, date=None, hour=None):
        """导出Hacker News的热门新闻到Markdown文件"""
        LOG.debug("准备导出Hacker News的热门新闻。")
        top_stories = self.fetch_top_stories()  # 获取新闻数据

        if not top_stories:
            LOG.warning("未找到任何Hacker News的新闻。")
            return None

        # 如果没有提供date和hour参数，使用当前日期和时间
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        if hour is None:
            hour = datetime.now().strftime('%H')

        # 构建存储路径
        dir_path = os.path.join('hacker_news', date)
        os.makedirs(dir_path, exist_ok=True)  # 确保目录存在

        file_path = os.path.join(dir_path, f'{hour}.md')  # 定义文件路径
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(f"# Hacker News Top Stories ({date} {hour}:00)\n\n")
            for idx, story in enumerate(top_stories, start=1):
                file.write(f"{idx}. [{story['title']}]({story['link']})\n")

        LOG.info(f"Hacker News热门新闻文件生成：{file_path}")
        return file_path

