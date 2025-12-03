"""
使用 Reflection Agent 生成新的信息渠道代码
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reflection_agent import ReflectionAgent
from logger import LOG


def generate_reddit_channel():
    """生成 Reddit 信息渠道"""
    LOG.info("开始生成 Reddit 信息渠道代码")
    
    # 创建 Reflection Agent
    agent = ReflectionAgent(model_name="gpt-3.5-turbo", temperature=0.7)
    
    # 任务描述
    task_description = """
为 GitHubSentinel 项目创建一个新的 Reddit 信息渠道。

要求：
1. 继承自 BaseChannel 类
2. 实现 fetch_data 方法，从 Reddit API 获取热门帖子
3. 实现 export_data 方法，将数据导出为 Markdown 文件
4. 支持配置 subreddit 名称和获取数量限制
5. 包含错误处理和日志记录
6. 遵循项目现有的代码风格和结构
7. 参考 custom_rss_channel.py 的实现方式

Reddit API 使用：
- 可以使用 PRAW (Python Reddit API Wrapper) 库
- 或者使用 Reddit 的 JSON API: https://www.reddit.com/r/{subreddit}/hot.json
- 需要处理 API 限制和错误情况

输出格式应该与 custom_rss_channel.py 类似，包含：
- 类定义
- __init__ 方法
- fetch_data 方法
- export_data 方法
- 适当的错误处理和日志
"""
    
    # 生成代码
    result = agent.generate_code(
        task_description=task_description,
        code_type="python",
        max_iterations=3
    )
    
    # 保存生成的代码
    output_path = Path(__file__).parent / "channels" / "reddit_channel.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result['final_content'])
    
    LOG.info(f"Reddit 渠道代码已生成并保存到: {output_path}")
    LOG.info(f"质量评分: {result['quality_score']:.1f}/10")
    LOG.info(f"迭代次数: {result['iterations']}")
    
    # 保存反思历史
    agent.save_reflection_history("reddit_channel_reflection.json")
    
    return result


def generate_twitter_channel():
    """生成 Twitter/X 信息渠道"""
    LOG.info("开始生成 Twitter 信息渠道代码")
    
    # 创建 Reflection Agent
    agent = ReflectionAgent(model_name="gpt-3.5-turbo", temperature=0.7)
    
    # 任务描述
    task_description = """
为 GitHubSentinel 项目创建一个新的 Twitter/X 信息渠道。

要求：
1. 继承自 BaseChannel 类
2. 实现 fetch_data 方法，从 Twitter API 获取热门推文或特定关键词的推文
3. 实现 export_data 方法，将数据导出为 Markdown 文件
4. 支持配置搜索关键词、用户、或话题标签
5. 包含错误处理和日志记录
6. 遵循项目现有的代码风格和结构
7. 参考 custom_rss_channel.py 的实现方式

Twitter API 使用：
- 可以使用 tweepy 库（如果可用）
- 或者使用 Twitter API v2
- 需要处理 API 限制和错误情况
- 如果没有 API Key，可以使用公开的 RSS Feed 或网页抓取（作为备选）

输出格式应该与 custom_rss_channel.py 类似，包含：
- 类定义
- __init__ 方法
- fetch_data 方法
- export_data 方法
- 适当的错误处理和日志
"""
    
    # 生成代码
    result = agent.generate_code(
        task_description=task_description,
        code_type="python",
        max_iterations=3
    )
    
    # 保存生成的代码
    output_path = Path(__file__).parent / "channels" / "twitter_channel.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result['final_content'])
    
    LOG.info(f"Twitter 渠道代码已生成并保存到: {output_path}")
    LOG.info(f"质量评分: {result['quality_score']:.1f}/10")
    LOG.info(f"迭代次数: {result['iterations']}")
    
    # 保存反思历史
    agent.save_reflection_history("twitter_channel_reflection.json")
    
    return result


def main():
    """主函数"""
    print("="*80)
    print("使用 Reflection Agent 生成新的信息渠道")
    print("="*80)
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"):
        print("警告: 未设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY")
        print("请设置环境变量或修改代码中的 API Key")
        return
    
    # 生成 Reddit 渠道
    print("\n1. 生成 Reddit 信息渠道...")
    reddit_result = generate_reddit_channel()
    
    # 生成 Twitter 渠道
    print("\n2. 生成 Twitter 信息渠道...")
    twitter_result = generate_twitter_channel()
    
    # 总结
    print("\n" + "="*80)
    print("生成完成！")
    print("="*80)
    print(f"\nReddit 渠道:")
    print(f"  - 质量评分: {reddit_result['quality_score']:.1f}/10")
    print(f"  - 迭代次数: {reddit_result['iterations']}")
    print(f"\nTwitter 渠道:")
    print(f"  - 质量评分: {twitter_result['quality_score']:.1f}/10")
    print(f"  - 迭代次数: {twitter_result['iterations']}")
    print(f"\n代码文件已保存到:")
    print(f"  - src/channels/reddit_channel.py")
    print(f"  - src/channels/twitter_channel.py")


if __name__ == "__main__":
    main()

