# STARLOG Complete Workflow Integration

## Two-Stage Validation Architecture

STARLOG uses a **two-stage validation system** that separates pre-work guidance from post-work enforcement.

### Stage 1: Pre-Work Brain Analysis (STARLOG MCP)

**Purpose**: Provide intelligent guidance BEFORE work begins.

```python
def start_starlog_with_brain_prediction(session_title: str, planned_changes: str, 
                                       context_from_docs: str, session_goals: List[str],
                                       path: str) -> str:
    """Start session with brain-agent analysis of planned work"""
    
    # 1. Brain-agent analyzes planned changes against rules
    brain_analysis = check_rules_compliance(planned_changes, path)
    
    # 2. Create session with predictions logged
    session = StarlogEntry(
        session_title=session_title,
        start_content=f"Starting work with brain analysis: {planned_changes}",
        context_from_docs=context_from_docs,
        session_goals=session_goals,
        predicted_patterns=extract_patterns_from_analysis(brain_analysis),
        rule_compliance_plan=brain_analysis
    )
    
    # 3. Store session in registry
    # 4. Return guidance for development work
    return f"Session started with brain guidance: {brain_analysis}"
```

**Enhanced StarlogEntry Model**:
```python
class StarlogEntry(BaseModel):
    # ... existing fields ...
    
    # Brain-agent predictions (Stage 1)
    predicted_patterns: List[str] = Field(default_factory=list, description="Brain-predicted patterns at start")
    rule_compliance_plan: Optional[str] = Field(default=None, description="Brain-generated compliance plan")
    potential_violations: List[str] = Field(default_factory=list, description="Brain-predicted risk areas")
```

### Stage 2: Post-Work Code Review Automation (External System)

**Purpose**: Enforce rules and update issue statuses AFTER work is completed.

**System**: Claude + GitHub Actions / heaven-bml automation (NOT in STARLOG MCP)

**Flow**:
1. PR submitted with changes
2. Automated code review runs:
   - Gets project rules from STARLOG registry
   - Claude pattern-matches through PR changes
   - Adds comments on specific lines/files for violations
3. Issue status updates based on review:
   - Clean review: `in-review` → `READY`
   - Issues found: `in-review` → `MEASURE` 
   - Major violations: Add detailed comments

## Issue Status Workflow Integration

### Heaven-BML → GitHub Status Flow

**BUILD Status Rules**:
- When heaven-bml puts something in `BUILD` status
- It automatically becomes `READY` in GitHub
- **ONLY ONE ITEM** can be `READY` at a time

**Exception Handling**:
- If a rejection from `in-review` becomes `ready` 
- It goes on top of whatever was already planned
- The rejected item gets tagged `AUTO`
- STARLOG treats `AUTO` tagged items as **higher priority than non-AUTO**

### STARLOG Priority System

```python
class DebugDiaryEntry(BaseModel):
    # ... existing fields ...
    
    # Priority system integration
    auto_tagged: bool = Field(default=False, description="True if tagged AUTO due to rejection")
    github_status: Optional[str] = Field(default=None, description="Current GitHub issue status")
    priority_level: str = Field(default="normal", description="auto|normal - auto takes precedence")

def get_current_work_priority(path: str) -> List[DebugDiaryEntry]:
    """Get work items ordered by priority: AUTO items first, then normal"""
    
    project_name = _get_project_name_from_path(path)
    diary_entries = _get_all_from_registry(project_name, "debug_diary")
    
    # Separate AUTO and normal items
    auto_items = [entry for entry in diary_entries if entry.get("auto_tagged", False)]
    normal_items = [entry for entry in diary_entries if not entry.get("auto_tagged", False)]
    
    # AUTO items get priority
    return auto_items + normal_items
```

### Orient Function Enhancement

```python
def orient(path: str) -> str:
    """Enhanced orient with priority-aware context"""
    
    # Standard context (last session + debug diary)
    base_context = get_last_session_and_diary(path)
    
    # Priority context injection
    priority_items = get_current_work_priority(path)
    auto_items = [item for item in priority_items if item.get("auto_tagged")]
    
    if auto_items:
        priority_context = "\n\n**HIGH PRIORITY: AUTO-TAGGED ITEMS (Review Rejections)**\n"
        for item in auto_items:
            priority_context += f"- URGENT: {item['content']}\n"
            if item.get('issue_id'):
                priority_context += f"  Issue: {item['issue_id']}\n"
        priority_context += "These rejected items take precedence over planned work.\n"
        
        base_context = priority_context + base_context
    
    return base_context
```

## Complete User Workflow (End-to-End)

### 1. Heaven-TreeKanban → GitHub Issue Flow
- **User action**: Moves item to `BUILD` in heaven-treekanban  
- **Heaven-BML**: Automatically updates GitHub status `backlog` → `READY`
- **Constraint**: **ONLY ONE ITEM** can be `READY` at a time

### 2. AI Session Initialization  
- **AI calls** `orient(path)` → Gets context + retrieves next `READY` task
- **Priority logic**: If `AUTO` tagged item exists, it takes priority over normal `READY`
- **AI calls** `start_starlog()` with planned work description
- **Brain-agent subagent**: Analyzes requirements → provides compliance guidance
- **STARLOG logs**: Brain predictions + compliance plan in session

### 3. Development Work (Live Updates)
- **AI works** on the task following brain guidance  
- **Live debug updates**: AI calls `add_debug_entry()` as it progresses
- **Atomic status updates** (simultaneous):
  - **STARLOG**: `add_debug_entry(bug_fix=True, issue_id=xxx)`
  - **GitHub**: Issue status `READY` → `IN-REVIEW`

### 4. Session Completion
- **AI calls** `end_starlog()` with completion summary
- **STARLOG documents**: What was actually accomplished vs planned
- **GitHub status**: Issue remains `IN-REVIEW` for external review

### 5. External Code Review Process
- **System**: Claude + pattern matching reviews the PR (NOT in STARLOG MCP)
- **Review process**:
  - Gets project rules from STARLOG registry
  - Pattern-matches through PR changes  
  - Adds comments on specific lines/files for violations
- **Review outcomes**:
  - ✅ **Clean review**: `IN-REVIEW` → `CLOSED` (task complete)
  - ❌ **Issues found**: `IN-REVIEW` → `READY` + `AUTO` tag

### 6. AUTO Priority Loop (Rejection Handling)
- **Rejected item**: Becomes `READY` + `AUTO` tag, jumps queue
- **Next AI session**: `orient()` gives `AUTO` items **priority context injection**
- **Cycle repeats**: Until item passes code review and gets closed

### 7. Issue Creation Flow (New Bugs)
- **AI discovers bug**: Calls `add_debug_entry(bug_report=True)`
- **STARLOG**: Creates new GitHub issue automatically
- **GitHub status**:
  - If nothing else `READY`: New issue → `READY` (work on immediately)
  - If something already `READY`: New issue → `backlog` (queue for later)

### 8. Status Synchronization Requirements
- **Atomic updates**: STARLOG debug diary + GitHub status must update simultaneously
- **Heaven-BML**: Tracks status consistency across systems
- **Redundancy handling**: AI may update redundantly, but systems stay in sync

## Clean Separation of Responsibilities

### STARLOG MCP Handles:
- ✅ **Pre-work guidance** - Brain-agent analysis before development
- ✅ **Session documentation** - What was planned vs what happened
- ✅ **Priority management** - AUTO items get precedence in orient
- ✅ **Learning loops** - Patterns from successful/failed sessions

### External Systems Handle:
- ✅ **Post-work enforcement** - Code review automation
- ✅ **Status transitions** - BUILD → READY, in-review → MEASURE/READY
- ✅ **Pattern matching** - Claude reviews actual code changes
- ✅ **Comment placement** - Specific line-by-line feedback

### Heaven-BML Handles:
- ✅ **Work queue management** - Only 1 READY item at a time
- ✅ **Status orchestration** - BUILD/READY/MEASURE transitions
- ✅ **AUTO tagging** - Rejected items get priority
- ✅ **Issue tracking** - GitHub integration and status sync

This creates a **complete autopoietic development system** where:
- Planning gets intelligent guidance (STARLOG brain-agent)
- Execution gets enforced validation (code review automation)
- Failures get priority attention (AUTO tagging + orient injection)
- Patterns improve over time (learning from review outcomes)