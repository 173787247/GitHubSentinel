# src/command_handler.py

import argparse

import argparse  # 导入argparse库，用于处理命令行参数解析

class CommandHandler:
    def __init__(self, github_client, subscription_manager, report_generator, hacker_news_client=None, channel_manager=None):
        # 初始化CommandHandler，接收GitHub客户端、订阅管理器和报告生成器
        self.github_client = github_client
        self.subscription_manager = subscription_manager
        self.report_generator = report_generator
        self.hacker_news_client = hacker_news_client
        self.channel_manager = channel_manager  # v1.0: 渠道管理器
        self.parser = self.create_parser()  # 创建命令行解析器

    def create_parser(self):
        # 创建并配置命令行解析器
        parser = argparse.ArgumentParser(
            description='GitHub Sentinel Command Line Interface',
            formatter_class=argparse.RawTextHelpFormatter
        )
        subparsers = parser.add_subparsers(title='Commands', dest='command')

        # 添加订阅命令
        parser_add = subparsers.add_parser('add', help='Add a subscription')
        parser_add.add_argument('repo', type=str, help='The repository to subscribe to (e.g., owner/repo)')
        parser_add.set_defaults(func=self.add_subscription)

        # 删除订阅命令
        parser_remove = subparsers.add_parser('remove', help='Remove a subscription')
        parser_remove.add_argument('repo', type=str, help='The repository to unsubscribe from (e.g., owner/repo)')
        parser_remove.set_defaults(func=self.remove_subscription)

        # 列出所有订阅命令
        parser_list = subparsers.add_parser('list', help='List all subscriptions')
        parser_list.set_defaults(func=self.list_subscriptions)

        # 导出每日进展命令
        parser_export = subparsers.add_parser('export', help='Export daily progress')
        parser_export.add_argument('repo', type=str, help='The repository to export progress from (e.g., owner/repo)')
        parser_export.set_defaults(func=self.export_daily_progress)

        # 导出特定日期范围进展命令
        parser_export_range = subparsers.add_parser('export-range', help='Export progress over a range of dates')
        parser_export_range.add_argument('repo', type=str, help='The repository to export progress from (e.g., owner/repo)')
        parser_export_range.add_argument('days', type=int, help='The number of days to export progress for')
        parser_export_range.set_defaults(func=self.export_progress_by_date_range)

        # 生成日报命令
        parser_generate = subparsers.add_parser('generate', help='Generate daily report from markdown file')
        parser_generate.add_argument('file', type=str, help='The markdown file to generate report from')
        parser_generate.set_defaults(func=self.generate_daily_report)

        # Hacker News相关命令
        parser_hn = subparsers.add_parser('hacker-news', help='Hacker News operations')
        hn_subparsers = parser_hn.add_subparsers(title='Hacker News Commands', dest='hn_command')
        
        # 获取Hacker News热门新闻
        parser_hn_fetch = hn_subparsers.add_parser('fetch', help='Fetch top stories from Hacker News')
        parser_hn_fetch.set_defaults(func=self.fetch_hacker_news)
        
        # 生成Hacker News趋势报告
        parser_hn_report = hn_subparsers.add_parser('report', help='Generate Hacker News trend report')
        parser_hn_report.set_defaults(func=self.generate_hacker_news_report)
        
        # v1.0: 自定义渠道命令
        parser_channel = subparsers.add_parser('channel', help='Custom channel operations')
        channel_subparsers = parser_channel.add_subparsers(title='Channel Commands', dest='channel_command')
        
        # 列出所有渠道
        parser_channel_list = channel_subparsers.add_parser('list', help='List all available channels')
        parser_channel_list.set_defaults(func=self.list_channels)
        
        # 从渠道获取数据
        parser_channel_fetch = channel_subparsers.add_parser('fetch', help='Fetch data from a channel')
        parser_channel_fetch.add_argument('channel_name', type=str, help='Channel name')
        parser_channel_fetch.set_defaults(func=self.fetch_channel_data)
        
        # 生成渠道报告
        parser_channel_report = channel_subparsers.add_parser('report', help='Generate report from a channel')
        parser_channel_report.add_argument('channel_name', type=str, help='Channel name')
        parser_channel_report.set_defaults(func=self.generate_channel_report)

        # 帮助命令
        parser_help = subparsers.add_parser('help', help='Show help message')
        parser_help.set_defaults(func=self.print_help)

        return parser  # 返回配置好的解析器

    # 下面是各种命令对应的方法实现，每个方法都使用了相应的管理器来执行实际操作，并输出结果信息
    def add_subscription(self, args):
        self.subscription_manager.add_subscription(args.repo)
        print(f"Added subscription for repository: {args.repo}")

    def remove_subscription(self, args):
        self.subscription_manager.remove_subscription(args.repo)
        print(f"Removed subscription for repository: {args.repo}")

    def list_subscriptions(self, args):
        subscriptions = self.subscription_manager.list_subscriptions()
        print("Current subscriptions:")
        for sub in subscriptions:
            print(f"  - {sub}")

    def export_daily_progress(self, args):
        self.github_client.export_daily_progress(args.repo)
        print(f"Exported daily progress for repository: {args.repo}")

    def export_progress_by_date_range(self, args):
        self.github_client.export_progress_by_date_range(args.repo, days=args.days)
        print(f"Exported progress for the last {args.days} days for repository: {args.repo}")

    def generate_daily_report(self, args):
        self.report_generator.generate_daily_report(args.file)
        print(f"Generated daily report from file: {args.file}")

    def fetch_hacker_news(self, args):
        """获取Hacker News热门新闻"""
        if not self.hacker_news_client:
            print("错误: Hacker News客户端未初始化")
            return
        file_path = self.hacker_news_client.export_top_stories()
        if file_path:
            print(f"Hacker News热门新闻已导出到: {file_path}")
        else:
            print("获取Hacker News热门新闻失败")

    def generate_hacker_news_report(self, args):
        """生成Hacker News趋势报告"""
        if not self.hacker_news_client:
            print("错误: Hacker News客户端未初始化")
            return
        try:
            # 获取并导出Hacker News热门新闻
            raw_file_path = self.hacker_news_client.export_top_stories()
            if raw_file_path:
                # 生成趋势报告
                report, report_file_path = self.report_generator.generate_hacker_news_report(raw_file_path)
                print(f"Hacker News趋势报告已生成: {report_file_path}")
            else:
                print("未获取到Hacker News数据")
        except Exception as e:
            print(f"生成Hacker News报告失败: {str(e)}")

    def list_channels(self, args):
        """v1.0: 列出所有可用渠道"""
        if not self.channel_manager:
            print("错误: 渠道管理器未初始化")
            return
        channels = self.channel_manager.list_channels()
        print("可用渠道:")
        for channel_name in channels:
            info = self.channel_manager.get_channel_info(channel_name)
            if info:
                print(f"  - {channel_name} ({info.get('type', 'Unknown')})")
    
    def fetch_channel_data(self, args):
        """v1.0: 从渠道获取数据"""
        if not self.channel_manager:
            print("错误: 渠道管理器未初始化")
            return
        try:
            data = self.channel_manager.fetch_data(args.channel_name)
            print(f"从渠道 {args.channel_name} 获取了 {len(data)} 条数据")
            for item in data[:5]:  # 只显示前5条
                print(f"  - {item.get('title', item.get('message', 'N/A'))[:60]}")
        except Exception as e:
            print(f"获取数据失败: {str(e)}")
    
    def generate_channel_report(self, args):
        """v1.0: 生成渠道报告"""
        if not self.channel_manager:
            print("错误: 渠道管理器未初始化")
            return
        try:
            # 获取数据
            data = self.channel_manager.fetch_data(args.channel_name)
            if not data:
                print(f"未获取到 {args.channel_name} 渠道的数据")
                return
            
            # 导出数据
            markdown_file_path = self.channel_manager.export_data(args.channel_name, data=data)
            if not markdown_file_path:
                print(f"导出 {args.channel_name} 数据失败")
                return
            
            # 生成报告
            report, report_file_path = self.report_generator.generate_channel_report(
                markdown_file_path, args.channel_name
            )
            print(f"{args.channel_name} 渠道报告已生成: {report_file_path}")
        except Exception as e:
            print(f"生成报告失败: {str(e)}")
    
    def print_help(self, args=None):
        self.parser.print_help()  # 输出帮助信息
