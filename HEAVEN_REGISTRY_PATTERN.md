# STARLOG Heaven Registry Integration Pattern

## Overview

STARLOG uses Heaven's official registry system via `registry_util_func` for storage and integrates with GitHub Issues for bug tracking workflow. STARLOG generates markdown documentation strings and manages the complete development session lifecycle.

## Proven Pattern (from POC)

### 1. Pydantic Models with Proper Serialization

```python
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class RulesEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    rule: str
    category: str = "general"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DebugDiaryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str
    current_state: str
    next_steps: List[str]

class StarlogEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    session_title: str
    start: str
    context_from_docs: str
    session_goals: List[str]
    key_discoveries: List[str] = Field(default_factory=list)
    end: Optional[str] = None
    session_summary: Optional[str] = None
```

### 2. Registry Wrapper Functions (Schema Enforcement Layer)

```python
from heaven_base.tools.registry_tool import registry_util_func

def add_rule_to_registry(project_name: str, rule_entry: RulesEntry) -> str:
    """Registry wrapper that enforces RulesEntry schema"""
    return registry_util_func(
        "add",
        registry_name=f"{project_name}_rules",
        key=rule_entry.id,
        value_dict=rule_entry.model_dump(mode='json')  # Handles datetime serialization
    )

def get_rules_from_registry(project_name: str) -> List[RulesEntry]:
    """Get all rules and reconstruct Pydantic models"""
    result = registry_util_func("get_all", registry_name=f"{project_name}_rules")
    
    # Parse result and reconstruct models
    rules = []
    if "Items in registry" in result:
        # Extract and parse the data (implementation details)
        # Convert back to RulesEntry objects
    return rules

def update_debug_diary_in_registry(project_name: str, entry: DebugDiaryEntry) -> str:
    """Update debug diary with schema validation"""
    return registry_util_func(
        "update",
        registry_name=f"{project_name}_debug_diary",
        key="current_status",
        value_dict=entry.model_dump(mode='json')
    )
```

### 3. Business Logic (Mixin Methods)

```python
class RulesMixin:
    def add_rule(self, rule: str, path: str, category: str = "general") -> str:
        """Add single rule using schema validation"""
        project_name = self._get_project_name_from_path(path)
        
        # Create Pydantic model (automatic validation)
        rule_entry = RulesEntry(rule=rule, category=category)
        
        # Use registry wrapper (schema enforcement)
        return add_rule_to_registry(project_name, rule_entry)
```

## Key Benefits

1. **Schema Validation**: Pydantic models validate data before storage
2. **Datetime Handling**: `model_dump(mode='json')` properly serializes dates as ISO strings
3. **Type Safety**: Full typing throughout the stack
4. **Heaven Integration**: Uses official Heaven registry system
5. **No Custom JSON**: Eliminates custom file handling code

## Registry Naming Convention

- Rules: `{project_name}_rules`
- Debug Diary: `{project_name}_debug_diary` 
- Starlog Sessions: `{project_name}_starlog`

## Registry Operations

### Create Registry
```python
registry_util_func("create_registry", registry_name=f"{project_name}_rules")
```

### Add Item (with schema)
```python
rule_entry = RulesEntry(rule=rule, category=category)
registry_util_func("add", registry_name=f"{project_name}_rules", 
                  key=rule_entry.id, value_dict=rule_entry.model_dump(mode='json'))
```

### Get All Items
```python
result = registry_util_func("get_all", registry_name=f"{project_name}_rules")
```

### Get Single Item
```python
result = registry_util_func("get", registry_name=f"{project_name}_rules", key=rule_id)
```

### Update Item
```python
registry_util_func("update", registry_name=f"{project_name}_rules",
                  key=rule_id, value_dict=updated_entry.model_dump(mode='json'))
```

### Delete Item
```python
registry_util_func("delete", registry_name=f"{project_name}_rules", key=rule_id)
```

## Environment Requirements

- `HEAVEN_DATA_DIR` must be set (e.g., `/tmp/heaven_data`)
- Heaven framework must be installed and available

## Implementation Status

✅ **POC Verified**: Pattern proven to work with Pydantic + Heaven registry  
✅ **Code Updated**: Main starlog.py uses Heaven registry utilities  
⏳ **Mixins**: Need to implement actual business logic using this pattern  
⏳ **Testing**: Need to test full STARLOG MCP functionality