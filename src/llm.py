import os
import json
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块

class LLM:
    def __init__(self):
        # 创建一个OpenAI客户端实例
        self.client = OpenAI()
        # 从TXT文件加载提示信息
        with open("prompts/report_prompt.txt", "r", encoding='utf-8') as file:
            self.system_prompt = file.read()
        # 加载Hacker News提示信息
        try:
            with open("prompts/hacker_news_prompt.txt", "r", encoding='utf-8') as file:
                self.hacker_news_prompt = file.read()
        except FileNotFoundError:
            LOG.warning("Hacker News提示文件未找到，使用默认提示")
            self.hacker_news_prompt = "你是一个技术趋势分析专家。请根据提供的 Hacker News 热门话题列表，生成一份技术趋势报告。"

    def generate_daily_report(self, markdown_content, dry_run=False):
        # 使用从TXT文件加载的提示信息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": markdown_content},
        ]

        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/prompt.txt", "w+") as f:
                # 格式化JSON字符串的保存
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 daily_progress/prompt.txt")

            return "DRY RUN"

        # 日志记录开始生成报告
        LOG.info("使用 GPT 模型开始生成报告。")
        
        try:
            # 调用OpenAI GPT模型生成报告
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 指定使用的模型版本
                messages=messages
            )
            LOG.debug("GPT response: {}", response)
            # 返回模型生成的内容
            return response.choices[0].message.content
        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error(f"生成报告时发生错误：{e}")
            raise

    def generate_hacker_news_report(self, markdown_content, dry_run=False):
        """生成Hacker News趋势报告"""
        messages = [
            {"role": "system", "content": self.hacker_news_prompt},
            {"role": "user", "content": markdown_content},
        ]

        if dry_run:
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("hacker_news/prompt.txt", "w+", encoding='utf-8') as f:
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 hacker_news/prompt.txt")
            return "DRY RUN"

        LOG.info("使用 GPT 模型开始生成 Hacker News 趋势报告。")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            LOG.debug("GPT response: {}", response)
            return response.choices[0].message.content
        except Exception as e:
            LOG.error(f"生成 Hacker News 报告时发生错误：{e}")
            raise
