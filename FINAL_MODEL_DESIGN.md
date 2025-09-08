# STARLOG Final Model Design

## System Architecture

STARLOG is an **autopoietic steering mechanism** that helps systems improve themselves through:
1. **Documentation generation** - Creates markdown strings from structured data
2. **Session lifecycle management** - START → progress tracking → END
3. **GitHub integration** - Bug reports become issues, issues get tracked to completion
4. **Rule emergence** - Patterns from sessions become rules for future sessions

## Three Core Models

### 1. RulesEntry
**Purpose**: Project rules and guidelines that emerge from development sessions.

```python
class RulesEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"rule_{uuid.uuid4().hex[:8]}")
    rule: str = Field(..., description="The actual rule text")
    category: str = Field(default="general", description="Rule category")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
```

**Registry Pattern**: `{project_name}_rules` with individual rule entries.

### 2. DebugDiaryEntry  
**Purpose**: Real-time development tracking with GitHub issue integration.

```python
class DebugDiaryEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"diary_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str = Field(..., description="The diary entry content")
    insights: Optional[str] = None
    in_file: Optional[str] = None  # File context
    
    # GitHub Issue Workflow
    bug_report: bool = False  # Creates GitHub issue → status: open
    bug_fix: bool = False     # Updates GitHub issue → status: in-review
    
    # GitHub integration data
    issue_id: Optional[str] = None  # Set when bug_report=True or linking external
    from_github: bool = False  # True if created from external GitHub issue
    
    def create_github_issue(self) -> str:
        """Create GitHub issue for bug reports"""
        if not self.bug_report:
            raise ValueError("Can only create issues for bug reports")
        # Creates issue with GitHub-safe content, returns issue_id
    
    def update_github_issue(self) -> str:
        """Update GitHub issue status for bug fixes"""
        if not self.bug_fix or not self.issue_id:
            raise ValueError("Bug fix requires existing issue_id")
        # Updates issue to in-review status
    
    def to_github_issue_body(self) -> str:
        """Generate GitHub-safe issue content"""
        body = f"**Bug Report from STARLOG**\n\n"
        body += f"**Description**: {self.content}\n\n"
        if self.insights:
            body += f"**Insights**: {self.insights}\n\n"
        if self.in_file:
            body += f"**File Context**: {self.in_file}\n\n"
        body += f"**Timestamp**: {self.timestamp.isoformat()}\n"
        return body
```

**Registry Pattern**: `{project_name}_debug_diary` with timestamped entries.

**GitHub Workflow**:
- `bug_report=True` → Creates issue, stores `issue_id`
- `bug_fix=True` → Updates issue to "in-review"  
- External issues → Can be pulled in with `from_github=True`
- Duplicate prevention → Check existing entries before creating

### 3. StarlogEntry
**Purpose**: Complete development sessions with START/END markers and markdown generation.

```python
class StarlogEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=datetime.now)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Session content
    session_title: str = Field(..., description="Brief session title")
    start_content: str = Field(..., description="START marker content")
    context_from_docs: str = Field(..., description="Context loaded from project docs")
    session_goals: List[str] = Field(..., description="List of session goals")
    
    # Session progress (accumulated during session)
    key_discoveries: List[str] = Field(default_factory=list)
    files_updated: List[str] = Field(default_factory=list)
    challenges_faced: List[str] = Field(default_factory=list)
    
    # Session completion
    end_content: Optional[str] = Field(default=None, description="END marker content")
    end_timestamp: Optional[datetime] = Field(default=None, description="When session ended")
    
    def end_session(self, end_content: str):
        """Mark session as ended"""
        self.end_content = end_content
        self.end_timestamp = datetime.now()
    
    def to_markdown(self) -> str:
        """Generate full STARLOG markdown format"""
        md = f"## {self.date} - {self.session_title}\n\n"
        md += f"**START**: {self.start_content}\n\n"
        md += f"**Context from docs**: {self.context_from_docs}\n\n"
        md += f"**Session goals**:\n"
        for goal in self.session_goals:
            md += f"- {goal}\n"
        md += "\n"
        
        if self.key_discoveries:
            md += "**Key discoveries**:\n"
            for i, discovery in enumerate(self.key_discoveries, 1):
                md += f"{i}. {discovery}\n"
            md += "\n"
        
        if self.files_updated:
            md += "**Files updated during session**:\n"
            for file in self.files_updated:
                md += f"- `{file}`\n"
            md += "\n"
        
        if self.end_content:
            md += f"**END**: {self.end_content}\n\n"
        
        return md
    
    @property
    def is_ended(self) -> bool:
        return self.end_content is not None
    
    @property
    def duration_minutes(self) -> Optional[int]:
        if self.end_timestamp:
            delta = self.end_timestamp - self.timestamp
            return int(delta.total_seconds() / 60)
        return None
```

**Registry Pattern**: `{project_name}_starlog` with session entries.

## Key Functions

### Debug Diary Functions
```python
def add_debug_entry(content: str, insights: Optional[str] = None, 
                   in_file: Optional[str] = None, bug_report: bool = False, 
                   bug_fix: bool = False, issue_id: Optional[str] = None) -> str

def check_external_issues() -> str  # "5 bugs were promoted to ready for work"

def add_external_issue(issue_id: str) -> str  # Pull external GitHub issue
```

### Orient Function
```python
def orient(path: str) -> str:
    """Returns: last_start + debug_diary + last_end"""
    # Gets latest session START
    # Gets current debug diary entries  
    # Gets latest session END (if exists)
    # Combines into complete context
```

## GitHub Integration Points

1. **Bug Reports** → Create GitHub issues with proper formatting
2. **Bug Fixes** → Update issue status to in-review  
3. **External Issues** → Pull ready issues into STARLOG tracking
4. **Duplicate Prevention** → Check existing entries before creating
5. **Issue Status Sync** → Ready issues appear in STARLOG workflow

## Registry Storage

- **Rules**: `{project_name}_rules_registry.json`
- **Debug Diary**: `{project_name}_debug_diary_registry.json`  
- **Sessions**: `{project_name}_starlog_registry.json`

All use `registry_util_func` with `model_dump(mode='json')` for proper datetime serialization.

## Content Generation

STARLOG generates **two types of content**:
1. **Markdown strings** for display (STARLOG format, orient function)
2. **GitHub-safe content** for issue creation (restricted markdown)

This enables STARLOG to be both a documentation system AND an active development workflow tool.