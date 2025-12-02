import gradio as gr  # 导入gradio库用于创建GUI

from config import Config  # 导入配置管理模块
from github_client import GitHubClient  # 导入用于GitHub API操作的客户端
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from hacker_news_client import HackerNewsClient  # 导入Hacker News客户端
from logger import LOG  # 导入日志记录器

# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)
llm = LLM()
report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)
hacker_news_client = HackerNewsClient()

def export_progress_by_date_range(repo, days):
    # 定义一个函数，用于导出和生成指定时间范围内项目的进展报告
    raw_file_path = github_client.export_progress_by_date_range(repo, days)  # 导出原始数据文件路径
    report, report_file_path = report_generator.generate_report_by_date_range(raw_file_path, days)  # 生成并获取报告内容及文件路径

    return report, report_file_path  # 返回报告内容和报告文件路径

def generate_hacker_news_report():
    """生成Hacker News趋势报告"""
    try:
        # 获取并导出Hacker News热门新闻
        raw_file_path = hacker_news_client.export_top_stories()
        if raw_file_path:
            # 生成趋势报告
            report, report_file_path = report_generator.generate_hacker_news_report(raw_file_path)
            return report, report_file_path
        else:
            return "未获取到Hacker News数据", None
    except Exception as e:
        LOG.error(f"生成Hacker News报告失败: {e}")
        return f"错误: {str(e)}", None

# 创建Gradio界面
with gr.Blocks(title="GitHubSentinel", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🛡️ GitHubSentinel")
    gr.Markdown("### 智能 GitHub 项目进展监控与 Hacker News 趋势分析工具")
    gr.Markdown("---")
    
    with gr.Tabs():
        with gr.Tab("📊 GitHub 项目报告"):
            with gr.Row():
                with gr.Column(scale=1):
                    repo_dropdown = gr.Dropdown(
                        choices=subscription_manager.list_subscriptions(),
                        label="订阅列表",
                        info="已订阅GitHub项目",
                        interactive=True
                    )
                    days_slider = gr.Slider(
                        value=2,
                        minimum=1,
                        maximum=7,
                        step=1,
                        label="报告周期",
                        info="生成项目过去一段时间进展，单位：天"
                    )
                    github_btn = gr.Button("生成GitHub报告", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    github_report_output = gr.Markdown(
                        label="报告预览",
                        value="报告将在这里显示..."
                    )
                    github_file_output = gr.File(
                        label="下载报告",
                        visible=False
                    )
            
            github_btn.click(
                fn=export_progress_by_date_range,
                inputs=[repo_dropdown, days_slider],
                outputs=[github_report_output, github_file_output]
            ).then(
                lambda f: gr.update(visible=f is not None),
                inputs=[github_file_output],
                outputs=[github_file_output]
            )
        
        with gr.Tab("🔥 Hacker News 趋势"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 生成 Hacker News 技术趋势报告")
                    gr.Markdown("点击按钮获取最新的 Hacker News 热门话题并生成趋势分析报告")
                    hn_btn = gr.Button("生成Hacker News趋势报告", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    hn_report_output = gr.Markdown(
                        label="趋势报告预览",
                        value="报告将在这里显示..."
                    )
                    hn_file_output = gr.File(
                        label="下载报告",
                        visible=False
                    )
            
            hn_btn.click(
                fn=generate_hacker_news_report,
                inputs=[],
                outputs=[hn_report_output, hn_file_output]
            ).then(
                lambda f: gr.update(visible=f is not None),
                inputs=[hn_file_output],
                outputs=[hn_file_output]
            )

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")  # 启动界面并设置为公共可访问
    # 可选带有用户认证的启动方式
    # demo.launch(share=True, server_name="0.0.0.0", auth=("django", "1234"))