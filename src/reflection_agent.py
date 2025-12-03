"""
Reflection Agent - 通用生成任务智能体
扩展后的 Reflection Agent，能够完成代码、报告等通用生成任务
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, List, Optional, Any
import json
import re
from pathlib import Path
from logger import LOG


class ReflectionAgent:
    """
    反射智能体
    能够进行自我反思、改进和生成各种类型的任务（代码、报告等）
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        初始化 Reflection Agent
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.model_name = model_name
        self.reflection_history: List[Dict] = []
        
        # 系统提示词
        self.system_prompt = """你是一个专业的 Reflection Agent，擅长：
1. 分析和理解任务需求
2. 生成高质量的代码、报告、文档等
3. 进行自我反思和改进
4. 识别问题并提供解决方案

你的工作流程：
1. **理解任务**：仔细分析任务需求
2. **生成初稿**：根据需求生成初始版本
3. **自我反思**：检查生成的内容，识别潜在问题
4. **改进优化**：基于反思结果改进内容
5. **验证输出**：确保输出符合要求

请始终：
- 提供清晰、可执行的代码
- 包含必要的注释和文档
- 遵循最佳实践
- 考虑边界情况和错误处理"""
    
    def reflect(self, content: str, task_type: str = "code", requirements: Optional[str] = None) -> Dict:
        """
        对生成的内容进行反思
        
        Args:
            content: 要反思的内容
            task_type: 任务类型（code, report, document 等）
            requirements: 原始需求
            
        Returns:
            dict: 反思结果，包含问题、建议和改进版本
        """
        reflection_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """请对以下{task_type}进行反思和改进：

原始需求：
{requirements}

生成的内容：
{content}

请分析：
1. 内容是否满足需求？
2. 是否存在问题或可以改进的地方？
3. 是否遵循最佳实践？
4. 是否需要添加错误处理、注释等？

请以 JSON 格式输出反思结果：
{{
    "satisfies_requirements": true/false,
    "issues": ["问题1", "问题2", ...],
    "suggestions": ["建议1", "建议2", ...],
    "improved_content": "改进后的内容",
    "quality_score": 0-10
}}""")
        ])
        
        chain = reflection_prompt | self.llm | StrOutputParser()
        
        try:
            response = chain.invoke({
                "task_type": task_type,
                "content": content,
                "requirements": requirements or "无特定需求"
            })
            
            # 解析 JSON 响应
            reflection_result = self._parse_json_response(response)
            
            # 记录反思历史
            self.reflection_history.append({
                "task_type": task_type,
                "original_content": content,
                "reflection": reflection_result,
                "timestamp": str(Path(__file__).stat().st_mtime)  # 简化时间戳
            })
            
            return reflection_result
            
        except Exception as e:
            LOG.error(f"反思过程出错: {str(e)}")
            return {
                "satisfies_requirements": False,
                "issues": [f"反思过程出错: {str(e)}"],
                "suggestions": [],
                "improved_content": content,
                "quality_score": 0
            }
    
    def generate_with_reflection(
        self,
        task_description: str,
        task_type: str = "code",
        max_iterations: int = 3,
        quality_threshold: float = 8.0
    ) -> Dict:
        """
        生成内容并进行迭代反思改进
        
        Args:
            task_description: 任务描述
            task_type: 任务类型
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值
            
        Returns:
            dict: 生成结果，包含最终内容和反思历史
        """
        LOG.info(f"开始生成任务: {task_description} (类型: {task_type})")
        
        # 生成初始版本
        initial_content = self._generate_initial(task_description, task_type)
        current_content = initial_content
        iteration = 0
        quality_score = 0
        
        while iteration < max_iterations:
            iteration += 1
            LOG.info(f"第 {iteration} 次反思迭代")
            
            # 进行反思
            reflection = self.reflect(current_content, task_type, task_description)
            quality_score = reflection.get("quality_score", 0)
            
            # 如果质量达到阈值，停止迭代
            if quality_score >= quality_threshold:
                LOG.info(f"质量达到阈值 ({quality_score:.1f} >= {quality_threshold})，停止迭代")
                break
            
            # 使用改进后的内容
            improved_content = reflection.get("improved_content", current_content)
            if improved_content == current_content:
                LOG.info("内容未改进，停止迭代")
                break
            
            current_content = improved_content
        
        return {
            "final_content": current_content,
            "initial_content": initial_content,
            "quality_score": quality_score,
            "iterations": iteration,
            "reflection_history": self.reflection_history[-iteration:] if iteration > 0 else []
        }
    
    def _generate_initial(self, task_description: str, task_type: str) -> str:
        """生成初始内容"""
        generation_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", """请根据以下需求生成{task_type}：

任务描述：
{task_description}

请生成完整、可用的{task_type}，确保：
1. 代码要完整、可运行
2. 包含必要的导入和依赖
3. 包含错误处理
4. 包含文档字符串和注释
5. 遵循 Python 最佳实践

只输出{task_type}内容，不要输出其他说明。""")
        ])
        
        chain = generation_prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "task_description": task_description,
            "task_type": task_type
        })
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        try:
            # 尝试提取 JSON 部分
            if "```json" in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
            elif "{" in response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            
            # 如果无法解析，返回默认结构
            return {
                "satisfies_requirements": True,
                "issues": [],
                "suggestions": [],
                "improved_content": response,
                "quality_score": 7.0
            }
        except Exception as e:
            LOG.warning(f"解析 JSON 响应失败: {str(e)}")
            return {
                "satisfies_requirements": True,
                "issues": [],
                "suggestions": [],
                "improved_content": response,
                "quality_score": 7.0
            }
    
    def generate_code(
        self,
        task_description: str,
        code_type: str = "python",
        max_iterations: int = 3
    ) -> Dict:
        """
        生成代码（便捷方法）
        
        Args:
            task_description: 任务描述
            code_type: 代码类型（python, javascript 等）
            max_iterations: 最大迭代次数
            
        Returns:
            dict: 生成结果
        """
        return self.generate_with_reflection(
            task_description=f"生成 {code_type} 代码: {task_description}",
            task_type="code",
            max_iterations=max_iterations
        )
    
    def generate_report(
        self,
        topic: str,
        format: str = "markdown",
        max_iterations: int = 2
    ) -> Dict:
        """
        生成报告（便捷方法）
        
        Args:
            topic: 报告主题
            format: 报告格式（markdown, html 等）
            max_iterations: 最大迭代次数
            
        Returns:
            dict: 生成结果
        """
        return self.generate_with_reflection(
            task_description=f"生成 {format} 格式的报告: {topic}",
            task_type="report",
            max_iterations=max_iterations
        )
    
    def save_reflection_history(self, output_path: str = "reflection_history.json"):
        """保存反思历史"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.reflection_history, f, ensure_ascii=False, indent=2)
        LOG.info(f"反思历史已保存到: {output_path}")

