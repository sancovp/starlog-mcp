# STARLOG Rules System Design

## Overview

The Rules system is an **intelligent rule enforcement mechanism** that uses a brain-agent to analyze changes against project rules and provide guidance. Rules emerge from development sessions and become enforced guidelines for future work.

## System Architecture

### 1. Rules Storage (RulesEntry Model)
```python
class RulesEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    rule: str = Field(..., description="The actual rule text")
    category: str = Field(default="general", description="Rule category (coding, process, etc.)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Additional fields for intelligent enforcement
    priority: int = Field(default=5, description="Rule priority 1-10 (10=critical)")
    applies_to: List[str] = Field(default_factory=list, description="File patterns this rule applies to")
    violation_examples: List[str] = Field(default_factory=list, description="Examples of rule violations")
    enforcement_level: str = Field(default="warning", description="error|warning|suggestion")
```

### 2. Brain-Agent Integration

**Core Function**: `check_rules_compliance(changes_description: str, project_path: str) -> str`

**Flow**:
1. **Load Rules** → Get all rules from `{project_name}_rules` registry
2. **Create Brain Registry** → Convert rules to brain-agent knowledge base
3. **Spawn Brain-Agent** → Analyze changes against rules
4. **Return Guidance** → Applicable rules, violations, recommendations

### 3. Implementation Design

```python
def check_rules_compliance(changes_description: str, project_path: str) -> str:
    """
    Analyze changes/additions against project rules using brain-agent.
    
    Args:
        changes_description: Description of what's being changed/added
        project_path: Path to project (to get project name)
    
    Returns:
        str: Analysis of rule compliance with recommendations
    """
    
    # 1. Get project rules from registry
    project_name = _get_project_name_from_path(project_path)
    rules_data = _get_all_from_registry(project_name, "rules")
    
    if not rules_data:
        return "No project rules found. Consider adding rules as you develop patterns."
    
    # 2. Create brain registry from rules
    brain_registry_name = f"{project_name}_rules_brain"
    brain_registry = _create_brain_registry_from_rules(rules_data, brain_registry_name)
    
    # 3. Spawn brain-agent with rules knowledge
    brain_agent_config = {
        "agent_type": "brain_agent",
        "registry_name": brain_registry_name,
        "system_prompt": f"""You are a project rules compliance analyst for {project_name}.

Your knowledge base contains all project rules categorized by type and priority.

TASK: Analyze the described changes against project rules and provide:
1. Which rules apply to these changes
2. Any potential violations or concerns  
3. Specific recommendations for compliance
4. Priority level of any issues found

Be constructive and helpful - focus on preventing problems, not just finding them.""",
        "temperature": 0.3  # More consistent rule enforcement
    }
    
    # 4. Query brain-agent
    analysis_prompt = f"""
PROJECT: {project_name}

CHANGES BEING MADE:
{changes_description}

ANALYZE: 
- Which project rules apply to these changes?
- Are there any rule violations or concerns?
- What specific recommendations do you have?
- What's the priority level of any issues?

Provide actionable guidance for maintaining project standards.
"""
    
    # TODO: Integrate with Heaven brain-agent system
    # result = spawn_brain_agent(brain_agent_config, analysis_prompt)
    
    # Placeholder for now
    return f"[RULES ANALYSIS] Would analyze changes against {len(rules_data)} rules using brain-agent"

def _create_brain_registry_from_rules(rules_data: Dict, brain_registry_name: str):
    """
    Convert rules registry data into brain-agent knowledge base.
    
    Creates structured knowledge that brain-agent can reason about:
    - Rule text and categories
    - Priority levels and enforcement
    - Examples and patterns
    - Relationships between rules
    """
    
    # Create brain registry
    registry_util_func("create_registry", registry_name=brain_registry_name)
    
    # Convert each rule to brain knowledge format
    for rule_id, rule_data in rules_data.items():
        brain_entry = {
            "type": "rule",
            "rule_text": rule_data["rule"],
            "category": rule_data["category"],
            "priority": rule_data.get("priority", 5),
            "enforcement_level": rule_data.get("enforcement_level", "warning"),
            "applies_to": rule_data.get("applies_to", []),
            "violation_examples": rule_data.get("violation_examples", []),
            "created_at": rule_data["created_at"],
            "metadata": {
                "source": "starlog_rules",
                "project_rule_id": rule_id
            }
        }
        
        # Store in brain registry
        registry_util_func("add", 
                          registry_name=brain_registry_name,
                          key=f"rule_{rule_id}",
                          value_dict=brain_entry)
    
    return brain_registry_name
```

### 4. Integration Points

**In STARLOG MCP Tools**:
```python
@app.tool()
def check_rules_compliance(changes_description: str, path: str) -> str:
    """Analyze changes against project rules using brain-agent."""
    return starlog.check_rules_compliance(changes_description, path)

@app.tool()  
def add_rule_from_violation(violation_description: str, rule_text: str, 
                           path: str, category: str = "general") -> str:
    """Add new rule based on discovered violation or pattern."""
    # Creates rule and updates brain registry
    return starlog.add_rule_from_violation(violation_description, rule_text, path, category)
```

**Usage Examples**:
```python
# Before making changes
result = check_rules_compliance(
    "Adding new API endpoint for user authentication with JWT tokens", 
    "/path/to/project"
)

# After discovering pattern
add_rule_from_violation(
    "Found inconsistent error handling across API endpoints",
    "All API endpoints must use standardized error response format with status codes",
    "/path/to/project",
    "api_design"
)
```

### 5. Rule Evolution Workflow

1. **Development Session** → Patterns discovered, challenges faced
2. **Session End** → Review challenges, identify rule candidates  
3. **Add Rules** → Convert patterns to enforceable guidelines
4. **Future Sessions** → Rules are checked automatically
5. **Rule Refinement** → Update rules based on new insights

### 6. Brain-Agent Knowledge Structure

**Registry Format** for brain-agent consumption:
```json
{
  "rule_abc123": {
    "type": "rule",
    "rule_text": "Always validate user input before processing",
    "category": "security", 
    "priority": 9,
    "enforcement_level": "error",
    "applies_to": ["*.py", "api/*"],
    "violation_examples": [
      "Direct database query with user input",
      "Unescaped HTML output"
    ],
    "related_rules": ["rule_def456"],
    "metadata": {
      "source": "starlog_rules",
      "project_rule_id": "rule_abc123"
    }
  }
}
```

## Benefits

1. **Intelligent Enforcement** - Brain-agent understands context, not just pattern matching
2. **Emergent Standards** - Rules emerge from real development experience
3. **Contextual Guidance** - Specific recommendations for specific changes
4. **Learning System** - Rules improve based on violations and new patterns
5. **Priority-Based** - Critical rules get more attention than suggestions
6. **Category-Aware** - Different rule types for different aspects (security, style, process)

## Integration with Heaven Framework

- **Brain-Agent System** - Uses Heaven's brain-agent infrastructure
- **Registry System** - Rules stored in Heaven registries
- **STARLOG Workflow** - Integrated into development session lifecycle
- **Heaven-BML** - Could integrate with issue tracking for rule violations

This creates a **self-improving development environment** where rules emerge from experience and actively guide future development through intelligent analysis.