# 增强的变量结构定义
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import StrEnum

class NestedVariableType(StrEnum):
    """嵌套变量类型"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ARRAY_STRING = "array[string]"
    ARRAY_INTEGER = "array[integer]"
    ARRAY_NUMBER = "array[number]"
    ARRAY_OBJECT = "array[object]"
    ARRAY_BOOLEAN = "array[boolean]"
    FILE = "file"
    ARRAY_FILE = "array[file]"

class NestedVariableDefinition(BaseModel):
    """嵌套变量定义"""
    name: str = Field(description="变量名称")
    type: NestedVariableType = Field(description="变量类型")
    required: bool = Field(default=False, description="是否必填")
    description: Optional[str] = Field(default="", description="变量描述")
    default_value: Optional[Any] = Field(default=None, description="默认值")
    
    # 嵌套子变量（用于 object 和 array[object] 类型）
    children: Optional[List["NestedVariableDefinition"]] = Field(
        default=None, 
        description="子变量定义，用于对象和对象数组类型"
    )
    
    # 数组元素类型定义（用于复杂数组类型）
    array_element_type: Optional[NestedVariableType] = Field(
        default=None,
        description="数组元素类型"
    )

class EnhancedVariableSelector(BaseModel):
    """增强的变量选择器，支持嵌套路径"""
    variable: str = Field(description="变量引用字符串")
    value_selector: List[str] = Field(description="变量选择器路径")
    nested_path: Optional[str] = Field(
        default=None, 
        description="嵌套对象路径，如 'user.profile.name'"
    )

class NodeInputDefinition(BaseModel):
    """节点输入定义"""
    name: str = Field(description="输入名称")
    type: NestedVariableType = Field(description="输入类型")
    required: bool = Field(default=False, description="是否必填")
    description: Optional[str] = Field(default="", description="输入描述")
    
    # 变量选择器（从其他节点获取值）
    variable_selector: Optional[EnhancedVariableSelector] = Field(
        default=None,
        description="变量选择器"
    )
    
    # 嵌套变量定义（用于复杂类型）
    nested_variables: Optional[List[NestedVariableDefinition]] = Field(
        default=None,
        description="嵌套变量定义"
    )
    
    # 默认值
    default_value: Optional[Any] = Field(default=None, description="默认值")

class NodeOutputDefinition(BaseModel):
    """节点输出定义"""
    name: str = Field(description="输出名称")
    type: NestedVariableType = Field(description="输出类型")
    description: Optional[str] = Field(default="", description="输出描述")
    
    # 嵌套变量定义（用于复杂输出类型）
    nested_variables: Optional[List[NestedVariableDefinition]] = Field(
        default=None,
        description="嵌套变量定义"
    )

# 更新 BaseNodeData 以支持新的输入输出定义
class EnhancedBaseNodeData(BaseModel):
    """增强的基础节点数据"""
    title: str
    desc: Optional[str] = None
    version: str = "1"
    
    # 输入定义
    inputs: List[NodeInputDefinition] = Field(
        default_factory=list,
        description="节点输入定义"
    )
    
    # 输出定义  
    outputs: List[NodeOutputDefinition] = Field(
        default_factory=list,
        description="节点输出定义"
    )