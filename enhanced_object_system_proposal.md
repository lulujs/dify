# Dify 对象传递增强方案

## 1. 增强 ObjectSegment 类型支持

### 1.1 添加结构化对象类型
```python
# 新增：结构化对象段
class StructuredObjectSegment(ObjectSegment):
    """支持带模式验证的结构化对象"""
    value_type: SegmentType = SegmentType.STRUCTURED_OBJECT
    schema: dict[str, Any] | None = None  # JSON Schema 定义
    
    def validate_schema(self) -> bool:
        """验证对象是否符合定义的模式"""
        if not self.schema:
            return True
        # 使用 jsonschema 库进行验证
        from jsonschema import validate, ValidationError
        try:
            validate(instance=self.value, schema=self.schema)
            return True
        except ValidationError:
            return False

# 新增：类实例对象段
class ClassInstanceSegment(ObjectSegment):
    """支持 Python 类实例对象"""
    value_type: SegmentType = SegmentType.CLASS_INSTANCE
    class_name: str
    module_name: str
    
    @property
    def text(self) -> str:
        return f"<{self.class_name} instance>"
    
    def to_dict(self) -> dict[str, Any]:
        """将类实例转换为字典"""
        if hasattr(self.value, '__dict__'):
            return self.value.__dict__
        return {}
```

### 1.2 扩展 SegmentType 枚举
```python
class SegmentType(StrEnum):
    # ... 现有类型
    STRUCTURED_OBJECT = "structured_object"
    CLASS_INSTANCE = "class_instance"
    NESTED_OBJECT = "nested_object"  # 支持深度嵌套
```

## 2. 增强变量池对象访问

### 2.1 改进嵌套属性访问
```python
class VariablePool(BaseModel):
    def get_object_path(self, selector: Sequence[str], path: str) -> Segment | None:
        """
        使用点分路径访问嵌套对象属性
        例: get_object_path([node_id, "data"], "user.profile.name")
        """
        obj = self.get(selector)
        if not isinstance(obj, ObjectSegment):
            return None
            
        current = obj.value
        for part in path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return variable_factory.build_segment(current)
    
    def set_object_path(self, selector: Sequence[str], path: str, value: Any) -> bool:
        """设置嵌套对象属性值"""
        obj = self.get(selector)
        if not isinstance(obj, ObjectSegment):
            return False
            
        # 深拷贝对象以保持不可变性
        new_obj = deepcopy(obj.value)
        
        # 导航到目标位置并设置值
        parts = path.split('.')
        current = new_obj
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
        
        # 更新变量池
        self.add(selector, new_obj)
        return True
```

### 2.2 对象合并和转换
```python
def merge_objects(self, selector1: Sequence[str], selector2: Sequence[str], 
                 target_selector: Sequence[str]) -> bool:
    """合并两个对象到目标位置"""
    obj1 = self.get(selector1)
    obj2 = self.get(selector2)
    
    if not (isinstance(obj1, ObjectSegment) and isinstance(obj2, ObjectSegment)):
        return False
    
    merged = {**obj1.value, **obj2.value}
    self.add(target_selector, merged)
    return True

def transform_object(self, selector: Sequence[str], 
                    transformer: Callable[[dict], dict]) -> bool:
    """使用转换函数处理对象"""
    obj = self.get(selector)
    if not isinstance(obj, ObjectSegment):
        return False
    
    transformed = transformer(obj.value)
    self.add(selector, transformed)
    return True
```

## 3. 模板系统增强

### 3.1 支持对象路径模板
```python
# 扩展模板解析器支持对象路径
OBJECT_PATH_PATTERN = re.compile(
    r"\{\{#([a-zA-Z0-9_]{1,50}(?:\.[a-zA-Z_][a-zA-Z0-9_]{0,29}){1,10})\.([a-zA-Z_][a-zA-Z0-9_.]{0,100})#\}\}"
)

class EnhancedVariableTemplateParser(VariableTemplateParser):
    def extract_object_paths(self) -> list[tuple[str, str]]:
        """提取对象路径引用 {{#node.var.path.to.field#}}"""
        matches = OBJECT_PATH_PATTERN.findall(self.template)
        return [(match[0], match[1]) for match in matches]
    
    def format_with_object_paths(self, variable_pool: VariablePool) -> str:
        """支持对象路径的模板格式化"""
        def replacer(match):
            selector_str = match.group(1)
            object_path = match.group(2)
            
            selector = selector_str.split('.')
            segment = variable_pool.get_object_path(selector, object_path)
            
            return str(segment.value) if segment else match.group(0)
        
        return re.sub(OBJECT_PATH_PATTERN, replacer, self.template)
```

## 4. 节点间对象传递优化

### 4.1 对象引用传递
```python
class ObjectReference(BaseModel):
    """对象引用，避免大对象的深拷贝"""
    node_id: str
    variable_name: str
    object_path: str = ""
    
    def resolve(self, variable_pool: VariablePool) -> Segment | None:
        """解析引用获取实际对象"""
        if self.object_path:
            return variable_pool.get_object_path(
                [self.node_id, self.variable_name], 
                self.object_path
            )
        return variable_pool.get([self.node_id, self.variable_name])

class ObjectReferenceSegment(Segment):
    """对象引用段，用于延迟加载大对象"""
    value_type: SegmentType = SegmentType.OBJECT_REFERENCE
    value: ObjectReference
```

### 4.2 对象序列化优化
```python
class OptimizedObjectSegment(ObjectSegment):
    """优化的对象段，支持压缩和缓存"""
    _compressed: bool = False
    _cache_key: str | None = None
    
    def compress(self) -> None:
        """压缩大对象"""
        if self.size > 1024 * 1024:  # 1MB
            import pickle, gzip
            compressed = gzip.compress(pickle.dumps(self.value))
            self.value = compressed
            self._compressed = True
    
    def decompress(self) -> dict[str, Any]:
        """解压缩对象"""
        if self._compressed:
            import pickle, gzip
            return pickle.loads(gzip.decompress(self.value))
        return self.value
```

## 5. 使用示例

### 5.1 复杂对象传递
```python
# 节点 A 输出复杂用户对象
user_data = {
    "id": 123,
    "profile": {
        "name": "张三",
        "email": "zhangsan@example.com",
        "preferences": {
            "language": "zh-CN",
            "theme": "dark"
        }
    },
    "orders": [
        {"id": 1, "amount": 100.0},
        {"id": 2, "amount": 200.0}
    ]
}

variable_pool.add(["node_a", "user"], user_data)

# 节点 B 访问嵌套属性
user_name = variable_pool.get_object_path(["node_a", "user"], "profile.name")
user_lang = variable_pool.get_object_path(["node_a", "user"], "profile.preferences.language")

# 模板中使用对象路径
template = "用户 {{#node_a.user.profile.name#}} 的首选语言是 {{#node_a.user.profile.preferences.language#}}"
```

### 5.2 对象转换和处理
```python
# 对象转换示例
def normalize_user(user_dict: dict) -> dict:
    return {
        "user_id": user_dict.get("id"),
        "display_name": user_dict.get("profile", {}).get("name", "Unknown"),
        "contact": user_dict.get("profile", {}).get("email"),
        "settings": user_dict.get("profile", {}).get("preferences", {})
    }

# 应用转换
variable_pool.transform_object(["node_a", "user"], normalize_user)
```

## 6. 实施步骤

1. **第一阶段**：扩展 SegmentType 和基础对象类型
2. **第二阶段**：增强 VariablePool 的对象访问方法
3. **第三阶段**：更新模板解析器支持对象路径
4. **第四阶段**：添加对象引用和优化机制
5. **第五阶段**：更新相关节点以支持增强的对象功能

## 7. 兼容性考虑

- 保持现有 ObjectSegment 的向后兼容性
- 新功能通过可选参数和新类型实现
- 渐进式迁移，不破坏现有工作流