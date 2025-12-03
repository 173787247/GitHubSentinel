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

    # 启动时立即执行（如不需要可注释）
    github_job(subscription_manager, github_client, report_generator, notifier, config.freq_days)
    hacker_news_job(hacker_news_client, report_generator, notifier)

    # 安排每天的定时任务
    schedule.every(config.freq_days).days.at(
        config.exec_time
    ).do(github_job, subscription_manager, github_client, report_generator, notifier, config.freq_days)
    
    # 安排Hacker News定时任务（每天执行一次，默认在GitHub任务后1小时）
    with open('config.json', 'r') as f:
        config_data = json.load(f)
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
