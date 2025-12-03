import shlex  # 导入shlex库，用于正确解析命令行输入

from config import Config  # 从config模块导入Config类，用于配置管理
from github_client import GitHubClient  # 从github_client模块导入GitHubClient类，用于GitHub API操作
from report_generator import ReportGenerator  # 从report_generator模块导入ReportGenerator类，用于报告生成
from llm import LLM  # 从llm模块导入LLM类，可能用于语言模型相关操作
from subscription_manager import SubscriptionManager  # 从subscription_manager模块导入SubscriptionManager类，管理订阅
from command_handler import CommandHandler  # 从command_handler模块导入CommandHandler类，处理命令行命令
from hacker_news_client import HackerNewsClient  # 从hacker_news_client模块导入HackerNewsClient类
from logger import LOG  # 从logger模块导入LOG对象，用于日志记录
# v1.0: 导入渠道管理系统
from channel_manager import ChannelManager
from channels import GitHubChannel, HackerNewsChannel
import json

def main():
    config = Config()  # 创建配置实例
    github_client = GitHubClient(config.github_token)  # 创建GitHub客户端实例
    # v0.6: 传递配置以支持 Ollama
    config_dict = {
        'llm': config.llm_config if hasattr(config, 'llm_config') else {}
    }
    llm = LLM(config_dict)  # 创建语言模型实例（支持 OpenAI 和 Ollama）
    report_generator = ReportGenerator(llm)  # 创建报告生成器实例
    subscription_manager = SubscriptionManager(config.subscriptions_file)  # 创建订阅管理器实例
    hacker_news_client = HackerNewsClient()  # 创建Hacker News客户端实例
    
    # v1.0: 初始化渠道管理器
    channel_manager = ChannelManager()
    github_channel = GitHubChannel(name="github", config={'token': config.github_token})
    channel_manager.register_channel(github_channel)
    hacker_news_channel = HackerNewsChannel(name="hacker_news")
    channel_manager.register_channel(hacker_news_channel)
    
    # v1.0: 从配置文件加载自定义渠道
    try:
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
                        LOG.info(f"注册自定义渠道: {channel_name}")
                except Exception as e:
                    LOG.error(f"注册自定义渠道失败: {str(e)}")
    except Exception as e:
        LOG.warning(f"加载自定义渠道配置失败: {str(e)}")
    
    command_handler = CommandHandler(github_client, subscription_manager, report_generator, 
                                     hacker_news_client, channel_manager)  # 创建命令处理器实例
    
    parser = command_handler.parser  # 获取命令解析器
    command_handler.print_help()  # 打印帮助信息

    while True:
        try:
            user_input = input("GitHub Sentinel> ")  # 等待用户输入
            if user_input in ['exit', 'quit']:  # 如果输入为退出命令，则结束循环
                break
            try:
                args = parser.parse_args(shlex.split(user_input))  # 解析用户输入的命令
                if args.command is None:  # 如果没有命令被解析，则继续循环
                    continue
                args.func(args)  # 执行对应的命令函数
            except SystemExit as e:  # 捕获由于错误命令引发的异常
                LOG.error("Invalid command. Type 'help' to see the list of available commands.")
        except Exception as e:
            LOG.error(f"Unexpected error: {e}")  # 记录其他未预期的错误

if __name__ == '__main__':
    main()  # 如果直接运行该文件，则执行main函数
