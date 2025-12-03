# src/report_generator.py

import os
from datetime import date, timedelta
from logger import LOG  # 导入日志模块，用于记录日志信息

class ReportGenerator:
    def __init__(self, llm):
        self.llm = llm  # 初始化时接受一个LLM实例，用于后续生成报告

    def generate_daily_report(self, markdown_file_path):
        # 读取Markdown文件并使用LLM生成日报
        with open(markdown_file_path, 'r') as file:
            markdown_content = file.read()

        report = self.llm.generate_daily_report(markdown_content)  # 调用LLM生成报告

        report_file_path = os.path.splitext(markdown_file_path)[0] + "_report.md"
        with open(report_file_path, 'w+') as report_file:
            report_file.write(report)  # 写入生成的报告

        LOG.info(f"GitHub 项目报告已保存到 {report_file_path}")

        return report, report_file_path


    def generate_report_by_date_range(self, markdown_file_path, days):
        # 生成特定日期范围的报告，流程与日报生成类似
        with open(markdown_file_path, 'r') as file:
            markdown_content = file.read()

        report = self.llm.generate_daily_report(markdown_content)

        report_file_path = os.path.splitext(markdown_file_path)[0] + f"_report.md"
        with open(report_file_path, 'w+') as report_file:
            report_file.write(report)
        
        LOG.info(f"GitHub 项目报告已保存到 {report_file_path}")

        return report, report_file_path

    def generate_hacker_news_report(self, markdown_file_path):
        """生成Hacker News趋势报告"""
        # 读取Markdown文件并使用LLM生成报告
        with open(markdown_file_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()

        report = self.llm.generate_hacker_news_report(markdown_content)  # 调用LLM生成报告

        report_file_path = os.path.splitext(markdown_file_path)[0] + "_trend_report.md"
        with open(report_file_path, 'w+', encoding='utf-8') as report_file:
            report_file.write(report)  # 写入生成的报告

        LOG.info(f"Hacker News 趋势报告已保存到 {report_file_path}")

        return report, report_file_path
    
    def generate_channel_report(self, markdown_file_path, channel_name: str = "custom"):
        """
        v1.0: 生成自定义渠道报告（通用方法）
        
        Args:
            markdown_file_path: Markdown 文件路径
            channel_name: 渠道名称，用于选择对应的提示词
            
        Returns:
            tuple: (报告内容, 报告文件路径)
        """
        # 读取Markdown文件
        with open(markdown_file_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
        
        # 根据渠道类型选择生成方法
        if channel_name.lower() == 'hacker_news':
            report = self.llm.generate_hacker_news_report(markdown_content)
        else:
            # 使用通用报告生成方法
            report = self.llm.generate_daily_report(markdown_content)
        
        # 生成报告文件路径
        report_file_path = os.path.splitext(markdown_file_path)[0] + f"_{channel_name}_report.md"
        with open(report_file_path, 'w+', encoding='utf-8') as report_file:
            report_file.write(report)
        
        LOG.info(f"{channel_name} 渠道报告已保存到 {report_file_path}")
        return report, report_file_path

