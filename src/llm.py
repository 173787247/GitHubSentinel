import os
import json
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块

class LLM:
    def __init__(self, config=None):
        """
        初始化LLM客户端
        支持 OpenAI 和 Ollama 两种后端
        """
        # 从配置文件或环境变量获取LLM配置
        if config:
            llm_config = config.get('llm', {})
            self.llm_type = llm_config.get('type', 'openai')  # 默认使用 OpenAI
            self.ollama_base_url = llm_config.get('ollama_base_url', 'http://localhost:11434/v1')
            self.ollama_model = llm_config.get('ollama_model', 'llama3.2')
            self.openai_model = llm_config.get('openai_model', 'gpt-4o-mini')
        else:
            # 兼容旧配置：从环境变量读取
            self.llm_type = os.getenv('LLM_TYPE', 'openai')
            self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434/v1')
            self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')
            self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # 根据配置创建客户端
        if self.llm_type.lower() == 'ollama':
            # Ollama 兼容 OpenAI API 格式
            self.client = OpenAI(
                base_url=self.ollama_base_url,
                api_key='ollama'  # Ollama 不需要真实的 API key
            )
            self.model = self.ollama_model
            LOG.info(f"使用 Ollama 模型: {self.ollama_model} (地址: {self.ollama_base_url})")
        else:
            # 默认使用 OpenAI
            self.client = OpenAI()
            self.model = self.openai_model
            LOG.info(f"使用 OpenAI 模型: {self.openai_model}")
        
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
        LOG.info(f"使用 {self.llm_type.upper()} 模型开始生成报告。")
        
        try:
            # 调用模型生成报告（支持 OpenAI 和 Ollama）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            LOG.debug(f"{self.llm_type.upper()} response: {}", response)
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

        LOG.info(f"使用 {self.llm_type.upper()} 模型开始生成 Hacker News 趋势报告。")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            LOG.debug(f"{self.llm_type.upper()} response: {}", response)
            return response.choices[0].message.content
        except Exception as e:
            LOG.error(f"生成 Hacker News 报告时发生错误：{e}")
            raise
