import schedule # 导入 schedule 实现定时任务执行器
import time  # 导入time库，用于控制时间间隔
import signal  # 导入signal库，用于信号处理
import sys  # 导入sys库，用于执行系统相关的操作
import json  # 导入json库，用于读取配置文件

from config import Config  # 导入配置管理类
from github_client import GitHubClient  # 导入GitHub客户端类，处理GitHub API请求
from notifier import Notifier  # 导入通知器类，用于发送通知
from report_generator import ReportGenerator  # 导入报告生成器类
from llm import LLM  # 导入语言模型类，可能用于生成报告内容
from subscription_manager import SubscriptionManager  # 导入订阅管理器类，管理GitHub仓库订阅
from hacker_news_client import HackerNewsClient  # 导入Hacker News客户端类
from logger import LOG  # 导入日志记录器
# v1.0: 导入渠道管理系统
from channel_manager import ChannelManager
from channels import GitHubChannel, HackerNewsChannel


def graceful_shutdown(signum, frame):
    # 优雅关闭程序的函数，处理信号时调用
    LOG.info("[优雅退出]守护进程接收到终止信号")
    sys.exit(0)  # 安全退出程序

def github_job(subscription_manager, github_client, report_generator, notifier, days):
    LOG.info("[开始执行定时任务]")
    subscriptions = subscription_manager.list_subscriptions()  # 获取当前所有订阅
    LOG.info(f"订阅列表：{subscriptions}")
    for repo in subscriptions:
        # 遍历每个订阅的仓库，执行以下操作
        markdown_file_path = github_client.export_progress_by_date_range(repo, days)
        # 从Markdown文件自动生成进展简报
        report, report_file_path = report_generator.generate_report_by_date_range(markdown_file_path, days)
        notifier.notify(repo, report)
    LOG.info(f"[定时任务执行完毕]")


def hacker_news_job(hacker_news_client, report_generator, notifier):
    """Hacker News定时任务"""
    LOG.info("[开始执行Hacker News定时任务]")
    try:
        # 获取并导出Hacker News热门新闻
        markdown_file_path = hacker_news_client.export_top_stories()
        if markdown_file_path:
            # 生成趋势报告
            report, report_file_path = report_generator.generate_hacker_news_report(markdown_file_path)
            # 发送通知（使用"Hacker News"作为标识）
            notifier.notify("Hacker News", report)
            LOG.info(f"[Hacker News定时任务执行完毕]")
        else:
            LOG.warning("[Hacker News定时任务]未获取到数据")
    except Exception as e:
        LOG.error(f"[Hacker News定时任务]执行失败：{str(e)}")


def channel_job(channel_manager, channel_name, report_generator, notifier, **kwargs):
    """
    v1.0: 通用渠道任务函数
    支持任何已注册的自定义渠道
    
    Args:
        channel_manager: 渠道管理器实例
        channel_name: 渠道名称
        report_generator: 报告生成器实例
        notifier: 通知器实例
        **kwargs: 传递给渠道的额外参数
    """
    LOG.info(f"[开始执行渠道任务] {channel_name}")
    try:
        # 从渠道获取数据
        data = channel_manager.fetch_data(channel_name, **kwargs)
        if not data:
            LOG.warning(f"[渠道任务 {channel_name}]未获取到数据")
            return
        
        # 导出数据到 Markdown 文件
        markdown_file_path = channel_manager.export_data(channel_name, data=data, **kwargs)
        if markdown_file_path:
            # 生成报告
            report, report_file_path = report_generator.generate_channel_report(
                markdown_file_path, channel_name
            )
            # 发送通知
            notifier.notify(channel_name, report)
            LOG.info(f"[渠道任务 {channel_name}]执行完毕")
        else:
            LOG.warning(f"[渠道任务 {channel_name}]导出数据失败")
    except Exception as e:
        LOG.error(f"[渠道任务 {channel_name}]执行失败：{str(e)}")


def main():
    # 设置信号处理器
    signal.signal(signal.SIGTERM, graceful_shutdown)

    config = Config()  # 创建配置实例
    github_client = GitHubClient(config.github_token)  # 创建GitHub客户端实例
    notifier = Notifier(config.email)  # 创建通知器实例
    # v0.6: 传递配置以支持 Ollama
    config_dict = {
        'llm': config.llm_config if hasattr(config, 'llm_config') else {}
    }
    llm = LLM(config_dict)  # 创建语言模型实例（支持 OpenAI 和 Ollama）
    report_generator = ReportGenerator(llm)  # 创建报告生成器实例
    subscription_manager = SubscriptionManager(config.subscriptions_file)  # 创建订阅管理器实例
    hacker_news_client = HackerNewsClient()  # 创建Hacker News客户端实例
    
    # v1.0: 初始化渠道管理器并注册内置渠道
    channel_manager = ChannelManager()
    github_channel = GitHubChannel(name="github", config={'token': config.github_token})
    channel_manager.register_channel(github_channel)
    hacker_news_channel = HackerNewsChannel(name="hacker_news")
    channel_manager.register_channel(hacker_news_channel)
    
    # v1.0: 从配置文件加载自定义渠道
    with open('config.json', 'r') as f:
        config_data = json.load(f)
        custom_channels = config_data.get('custom_channels', [])
        for channel_config in custom_channels:
            try:
                channel_type = channel_config.get('type')
                channel_name = channel_config.get('name')
                channel_params = channel_config.get('config', {})
                
                if channel_type == 'rss':
                    from channels.custom_rss_channel import CustomRSSChannel
                    custom_channel = CustomRSSChannel(name=channel_name, config=channel_params)
                    channel_manager.register_channel(custom_channel)
                    LOG.info(f"注册自定义渠道: {channel_name} (类型: {channel_type})")
            except Exception as e:
                LOG.error(f"注册自定义渠道失败: {str(e)}")

    # 启动时立即执行（如不需要可注释）
    github_job(subscription_manager, github_client, report_generator, notifier, config.freq_days)
    hacker_news_job(hacker_news_client, report_generator, notifier)
    
    # v1.0: 执行自定义渠道任务
    for channel_name in channel_manager.list_channels():
        if channel_name not in ['github', 'hacker_news']:  # 跳过已单独处理的内置渠道
            try:
                channel_config = next((c for c in custom_channels if c.get('name') == channel_name), {})
                exec_time = channel_config.get('execution_time', "10:00")
                schedule.every(1).days.at(exec_time).do(
                    channel_job, channel_manager, channel_name, report_generator, notifier
                )
                LOG.info(f"安排自定义渠道任务: {channel_name} 执行时间: {exec_time}")
            except Exception as e:
                LOG.error(f"安排自定义渠道任务失败 {channel_name}: {str(e)}")

    # 安排每天的定时任务
    schedule.every(config.freq_days).days.at(
        config.exec_time
    ).do(github_job, subscription_manager, github_client, report_generator, notifier, config.freq_days)
    
    # 安排Hacker News定时任务（每天执行一次，默认在GitHub任务后1小时）
    hacker_news_time = config_data.get('hacker_news_execution_time', "09:00")
    schedule.every(1).days.at(hacker_news_time).do(
        hacker_news_job, hacker_news_client, report_generator, notifier
    )

    try:
        # 在守护进程中持续运行
        while True:
            schedule.run_pending()
            time.sleep(1)  # 短暂休眠以减少 CPU 使用
    except Exception as e:
        LOG.error(f"主进程发生异常: {str(e)}")
        sys.exit(1)



if __name__ == '__main__':
    main()
