# 增强的变量池实现
from typing import Any, Dict, List, Optional, Sequence, Union
from collections import defaultdict
from copy import deepcopy
import json

from core.variables.segments import Segment, ObjectSegment, ArraySegment
from core.workflow.runtime.variable_pool import VariablePool
from factories import variable_factory

class EnhancedVariablePool(VariablePool):
    """增强的变量池，支持复杂对象和数组的嵌套访问"""
    
    def add_nested_variable(
        self, 
        selector: Sequence[str], 
        nested_definition: "NestedVariableDefinition",
        value: Any
    ) -> None:
        """
        添加嵌套变量到变量池
        
        Args:
            selector: 变量选择器 [node_id, variable_name]
            nested_definition: 嵌套变量定义
            value: 变量值
        """
        # 验证值是否符合定义
        validated_value = self._validate_nested_value(value, nested_definition)
        
        # 创建对应的段
        segment = self._create_nested_segment(validated_value, nested_definition)
        
        # 添加到变量池
        self.add(selector, segment)
    
    def get_nested_value(
        self, 
        selector: Sequence[str], 
        nested_path: Optional[str] = None
    ) -> Optional[Segment]:
        """
        获取嵌套变量值
        
        Args:
            selector: 变量选择器 [node_id, variable_name]
            nested_path: 嵌套路径，如 'user.profile.name'
            
        Returns:
            对应的段对象
        """
        if nested_path:
            # 扩展选择器以包含嵌套路径
            path_parts = nested_path.split('.')
            extended_selector = list(selector) + path_parts
            return self.get(extended_selector)
        else:
            return self.get(selector)
    
    def set_nested_value(
        self,
        selector: Sequence[str],
        nested_path: str,
        value: Any
    ) -> bool:
        """
        设置嵌套变量值
        
        Args:
            selector: 变量选择器 [node_id, variable_name]
            nested_path: 嵌套路径，如 'user.profile.name'
            value: 要设置的值
            
        Returns:
            是否设置成功
        """
        # 获取根对象
        root_segment = self.get(selector)
        if not isinstance(root_segment, ObjectSegment):
            return False
        
        # 深拷贝对象以保持不可变性
        new_obj = deepcopy(root_segment.value)
        
        # 导航到目标位置并设置值
        parts = nested_path.split('.')
        current = new_obj
        
        # 创建嵌套路径
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # 如果路径中的值不是字典，无法继续嵌套
                return False
            current = current[part]
        
        # 设置最终值
        current[parts[-1]] = value
        
        # 更新变量池
        self.add(selector, new_obj)
        return True
    
    def merge_nested_objects(
        self,
        target_selector: Sequence[str],
        source_selectors: List[Sequence[str]],
        merge_strategy: str = "deep"
    ) -> bool:
        """
        合并多个嵌套对象
        
        Args:
            target_selector: 目标变量选择器
            source_selectors: 源变量选择器列表
            merge_strategy: 合并策略 ('shallow' | 'deep')
            
        Returns:
            是否合并成功
        """
        merged_obj = {}
        
        for selector in source_selectors:
            segment = self.get(selector)
            if isinstance(segment, ObjectSegment):
                if merge_strategy == "deep":
                    merged_obj = self._deep_merge(merged_obj, segment.value)
                else:
                    merged_obj.update(segment.value)
        
        self.add(target_selector, merged_obj)
        return True
    
    def validate_nested_structure(
        self,
        selector: Sequence[str],
        expected_definition: "NestedVariableDefinition"
    ) -> Dict[str, Any]:
        """
        验证嵌套结构是否符合定义
        
        Args:
            selector: 变量选择器
            expected_definition: 期望的变量定义
            
        Returns:
            验证结果，包含错误信息
        """
        segment = self.get(selector)
        if not segment:
            return {"valid": False, "error": "Variable not found"}
        
        return self._validate_segment_structure(segment, expected_definition)
    
    def _validate_nested_value(
        self, 
        value: Any, 
        definition: "NestedVariableDefinition"
    ) -> Any:
        """验证嵌套值是否符合定义"""
        from enhanced_variable_structure import NestedVariableType
        
        # 基础类型验证
        if definition.type == NestedVariableType.STRING and not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value)}")
        elif definition.type == NestedVariableType.INTEGER and not isinstance(value, int):
            raise ValueError(f"Expected integer, got {type(value)}")
        elif definition.type == NestedVariableType.NUMBER and not isinstance(value, (int, float)):
            raise ValueError(f"Expected number, got {type(value)}")
        elif definition.type == NestedVariableType.BOOLEAN and not isinstance(value, bool):
            raise ValueError(f"Expected boolean, got {type(value)}")
        elif definition.type == NestedVariableType.OBJECT and not isinstance(value, dict):
            raise ValueError(f"Expected object, got {type(value)}")
        elif definition.type.startswith("array") and not isinstance(value, list):
            raise ValueError(f"Expected array, got {type(value)}")
        
        # 对象类型的子字段验证
        if definition.type == NestedVariableType.OBJECT and definition.children:
            for child_def in definition.children:
                if child_def.required and child_def.name not in value:
                    raise ValueError(f"Required field '{child_def.name}' missing")
                if child_def.name in value:
                    self._validate_nested_value(value[child_def.name], child_def)
        
        # 数组类型的元素验证
        if definition.type.startswith("array") and isinstance(value, list):
            if definition.type == NestedVariableType.ARRAY_OBJECT and definition.children:
                for item in value:
                    if not isinstance(item, dict):
                        raise ValueError("Array element must be object")
                    for child_def in definition.children:
                        if child_def.required and child_def.name not in item:
                            raise ValueError(f"Required field '{child_def.name}' missing in array element")
                        if child_def.name in item:
                            self._validate_nested_value(item[child_def.name], child_def)
        
        return value
    
    def _create_nested_segment(
        self, 
        value: Any, 
        definition: "NestedVariableDefinition"
    ) -> Segment:
        """根据定义创建嵌套段"""
        return variable_factory.build_segment(value)
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = target.copy()
        
        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_segment_structure(
        self, 
        segment: Segment, 
        definition: "NestedVariableDefinition"
    ) -> Dict[str, Any]:
        """验证段结构是否符合定义"""
        try:
            self._validate_nested_value(segment.value, definition)
            return {"valid": True}
        except ValueError as e:
            return {"valid": False, "error": str(e)}

# 扩展变量模板解析器以支持嵌套路径
class EnhancedVariableTemplateParser:
    """增强的变量模板解析器，支持嵌套路径"""
    
    # 支持嵌套路径的模板模式
    NESTED_PATTERN = re.compile(
        r"\{\{#([a-zA-Z0-9_]{1,50}(?:\.[a-zA-Z_][a-zA-Z0-9_]{0,29}){1,10})(?:\.([a-zA-Z_][a-zA-Z0-9_.]{0,100}))?#\}\}"
    )
    
    def __init__(self, template: str):
        self.template = template
    
    def extract_nested_selectors(self) -> List[Dict[str, Any]]:
        """提取嵌套选择器"""
        matches = self.NESTED_PATTERN.findall(self.template)
        selectors = []
        
        for match in matches:
            selector_str, nested_path = match
            selector_parts = selector_str.split('.')
            
            selectors.append({
                "variable": f"#{selector_str}{'.' + nested_path if nested_path else ''}#",
                "selector": selector_parts,
                "nested_path": nested_path if nested_path else None
            })
        
        return selectors
    
    def format_with_nested_variables(
        self, 
        variable_pool: EnhancedVariablePool
    ) -> str:
        """使用嵌套变量格式化模板"""
        def replacer(match):
            selector_str = match.group(1)
            nested_path = match.group(2) if len(match.groups()) > 1 else None
            
            selector = selector_str.split('.')
            segment = variable_pool.get_nested_value(selector, nested_path)
            
            if segment:
                return str(segment.value)
            else:
                return match.group(0)  # 返回原始匹配
        
        return re.sub(self.NESTED_PATTERN, replacer, self.template)