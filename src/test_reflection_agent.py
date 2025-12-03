"""
测试 Reflection Agent 生成新渠道代码
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reflection_agent import ReflectionAgent
from src.channels.reddit_channel import RedditChannel
from logger import LOG


def test_reflection_agent():
    """测试 Reflection Agent"""
    print("="*80)
    print("测试 Reflection Agent")
    print("="*80)
    
    # 创建 Reflection Agent
    agent = ReflectionAgent(model_name="gpt-3.5-turbo", temperature=0.7)
    
    # 测试生成代码
    print("\n1. 测试代码生成...")
    code_task = """
创建一个简单的 Python 函数，计算斐波那契数列的第 n 项。
要求：
- 使用递归实现
- 包含文档字符串
- 包含错误处理
"""
    
    code_result = agent.generate_code(code_task, max_iterations=2)
    print(f"代码生成完成，质量评分: {code_result['quality_score']:.1f}/10")
    print(f"迭代次数: {code_result['iterations']}")
    print(f"\n生成的代码:\n{code_result['final_content'][:500]}...")
    
    # 测试生成报告
    print("\n2. 测试报告生成...")
    report_result = agent.generate_report(
        "LangGraph 多智能体系统的优势和应用场景",
        format="markdown",
        max_iterations=2
    )
    print(f"报告生成完成，质量评分: {report_result['quality_score']:.1f}/10")
    print(f"迭代次数: {report_result['iterations']}")
    print(f"\n生成的报告:\n{report_result['final_content'][:500]}...")
    
    return code_result, report_result


def test_reddit_channel():
    """测试 Reddit 渠道"""
    print("\n" + "="*80)
    print("测试 Reddit 渠道")
    print("="*80)
    
    try:
        # 创建 Reddit 渠道
        reddit = RedditChannel(name="reddit_test", config={"subreddit": "python"})
        
        # 获取数据
        print("\n从 r/python 获取热门帖子...")
        data = reddit.fetch_data(limit=5)
        
        print(f"\n获取到 {len(data)} 条数据:")
        for item in data:
            print(f"  - {item.get('rank')}. {item.get('title', '')[:60]}...")
            print(f"    分数: {item.get('score')}, 评论: {item.get('num_comments')}")
        
        # 导出数据
        if data:
            output_path = reddit.export_data(data, output_path="test_reddit_output.md")
            print(f"\n数据已导出到: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("DEEPSEEK_API_KEY"):
        print("警告: 未设置 OPENAI_API_KEY 或 DEEPSEEK_API_KEY")
        print("Reflection Agent 测试需要 API Key")
        print("但可以测试 Reddit 渠道（不需要 API Key）\n")
        
        # 只测试 Reddit 渠道
        test_reddit_channel()
        return
    
    # 测试 Reflection Agent
    code_result, report_result = test_reflection_agent()
    
    # 测试 Reddit 渠道
    test_reddit_channel()
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)


if __name__ == "__main__":
    main()

