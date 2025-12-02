import gradio as gr  # 导入gradio库用于创建GUI

from config import Config  # 导入配置管理模块
from github_client import GitHubClient  # 导入用于GitHub API操作的客户端
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from logger import LOG  # 导入日志记录器

# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)
try:
    # v0.4.1 版本 LLM 可能不需要 config 参数
    llm = LLM() if not hasattr(LLM.__init__, '__code__') or LLM.__init__.__code__.co_argcount == 1 else LLM(config)
except:
    llm = LLM()
report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)

def export_progress_by_date_range(repo, days):
    """
    导出和生成指定时间范围内项目的进展报告
    
    :param repo: 仓库名称
    :param days: 报告周期（天数）
    :return: 报告内容和报告文件路径
    """
    try:
        raw_file_path = github_client.export_progress_by_date_range(repo, days)
        report, report_file_path = report_generator.generate_report_by_date_range(raw_file_path, days)
        return report, report_file_path
    except Exception as e:
        LOG.error(f"生成报告失败: {e}")
        return f"错误: {str(e)}", None

def list_subscriptions_display():
    """获取订阅列表用于显示"""
    try:
        subscriptions = subscription_manager.get_subscriptions()
        return "\n".join([f"- {sub}" for sub in subscriptions]) if subscriptions else "暂无订阅"
    except Exception as e:
        return f"获取订阅列表失败: {str(e)}"

def get_subscriptions_list():
    """获取订阅列表（用于 Dropdown）"""
    try:
        return subscription_manager.get_subscriptions()
    except:
        return []

def add_subscription(repo):
    """添加订阅"""
    try:
        subscription_manager.add_subscription(repo)
        return f"成功添加订阅: {repo}", list_subscriptions_display()
    except Exception as e:
        return f"添加订阅失败: {str(e)}", list_subscriptions_display()

def remove_subscription(repo):
    """移除订阅"""
    try:
        subscription_manager.remove_subscription(repo)
        return f"成功移除订阅: {repo}", list_subscriptions_display()
    except Exception as e:
        return f"移除订阅失败: {str(e)}", list_subscriptions_display()

# 使用 Blocks 创建更灵活的布局
with gr.Blocks(title="GitHubSentinel - 项目进展监控", theme=gr.themes.Soft()) as demo:
    # 标题和描述
    gr.Markdown("# 🛡️ GitHubSentinel")
    gr.Markdown("### 智能 GitHub 项目进展监控工具")
    gr.Markdown("---")
    
    # 使用 Tabs 组织功能
    with gr.Tabs():
        # Tab 1: 报告生成
        with gr.Tab("📊 生成报告"):
            with gr.Row():
                with gr.Column(scale=1):
                    repo_dropdown = gr.Dropdown(
                        choices=get_subscriptions_list(),
                        label="选择仓库",
                        info="从订阅列表中选择要生成报告的仓库",
                        interactive=True
                    )
                    days_slider = gr.Slider(
                        value=7,
                        minimum=1,
                        maximum=30,
                        step=1,
                        label="报告周期（天）",
                        info="选择要查看过去多少天的进展"
                    )
                    generate_btn = gr.Button("生成报告", variant="primary", size="lg")
                    
                with gr.Column(scale=2):
                    report_output = gr.Markdown(
                        label="报告预览",
                        value="报告将在这里显示..."
                    )
                    file_output = gr.File(
                        label="下载报告",
                        visible=False
                    )
            
            # 刷新订阅列表按钮
            refresh_btn = gr.Button("刷新订阅列表", variant="secondary")
            
            # 事件绑定
            generate_btn.click(
                fn=export_progress_by_date_range,
                inputs=[repo_dropdown, days_slider],
                outputs=[report_output, file_output]
            ).then(
                lambda f: gr.update(visible=f is not None),
                inputs=[file_output],
                outputs=[file_output]
            )
            
            refresh_btn.click(
                fn=lambda: gr.update(choices=get_subscriptions_list()),
                outputs=[repo_dropdown]
            )
        
        # Tab 2: 订阅管理
        with gr.Tab("📋 订阅管理"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 添加订阅")
                    new_repo_input = gr.Textbox(
                        label="仓库名称",
                        placeholder="例如: owner/repo-name",
                        info="输入 GitHub 仓库的完整名称（格式: owner/repo）"
                    )
                    add_btn = gr.Button("添加订阅", variant="primary")
                    add_status = gr.Textbox(label="操作状态", interactive=False)
                
                with gr.Column():
                    gr.Markdown("### 移除订阅")
                    remove_repo_dropdown = gr.Dropdown(
                        choices=get_subscriptions_list(),
                        label="选择要移除的仓库",
                        interactive=True
                    )
                    remove_btn = gr.Button("移除订阅", variant="stop")
                    remove_status = gr.Textbox(label="操作状态", interactive=False)
            
            gr.Markdown("---")
            gr.Markdown("### 当前订阅列表")
            subscriptions_display = gr.Markdown(value=list_subscriptions_display())
            
            # 事件绑定
            def add_subscription_wrapper(repo):
                status, display = add_subscription(repo)
                return status, display, gr.update(choices=get_subscriptions_list()), gr.update(choices=get_subscriptions_list())
            
            def remove_subscription_wrapper(repo):
                status, display = remove_subscription(repo)
                return status, display, gr.update(choices=get_subscriptions_list()), gr.update(choices=get_subscriptions_list())
            
            add_btn.click(
                fn=add_subscription_wrapper,
                inputs=[new_repo_input],
                outputs=[add_status, subscriptions_display, repo_dropdown, remove_repo_dropdown]
            ).then(
                fn=lambda: "",
                outputs=[new_repo_input]
            )
            
            remove_btn.click(
                fn=remove_subscription_wrapper,
                inputs=[remove_repo_dropdown],
                outputs=[remove_status, subscriptions_display, repo_dropdown, remove_repo_dropdown]
            )
        
        # Tab 3: 关于
        with gr.Tab("ℹ️ 关于"):
            gr.Markdown("""
            ## GitHubSentinel
            
            GitHubSentinel 是一个智能的 GitHub 项目进展监控工具，帮助开发者和项目经理：
            
            - 📊 **自动生成项目进展报告**
            - 📋 **管理 GitHub 仓库订阅**
            - 🔔 **及时获取项目更新**
            - 📈 **跟踪项目发展趋势**
            
            ### 使用说明
            
            1. 在"订阅管理"标签页中添加要监控的仓库
            2. 在"生成报告"标签页中选择仓库和时间范围
            3. 点击"生成报告"按钮获取详细的项目进展报告
            
            ### 版本信息
            - 当前版本: v0.4.1 (Gradio 布局优化版)
            - 布局改进: 使用 Tabs、Rows、Columns 等组件优化界面
            """)

if __name__ == "__main__":
    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860
    )
