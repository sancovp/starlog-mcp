#!/usr/bin/env python3
"""
STARLOG Rules Brain Integration

This module provides integration between STARLOG project rules and brain-agent
for intelligent rule querying during development.

Usage:
    # Auto-create rules brain for a project
    rules_brain = create_rules_brain("my_project", "/path/to/project")
    
    # Query rules during development
    guidance = query_rules_brain("my_project", "I'm writing a Python validation function")
    
    # Returns relevant rules with reasoning for the development context
"""

from typing import List, Dict, Optional
from brain_agent.manager_tools import brain_manager_func
from brain_agent.query_brain_tool import query_brain_func
from .starlog import Starlog

class StarlogRulesBrainIntegration:
    """
    Integrates STARLOG rules with brain-agent for intelligent development guidance.
    """
    
    def __init__(self):
        pass
    
    def create_rules_brain(self, project_path: str) -> str:
        """
        Create a brain-agent brain from STARLOG project rules.
        
        Args:
            project_path: Path to STARLOG project
            
        Returns:
            Brain ID for the created rules brain
        """
        # Get project name from path
        project_name = self._get_project_name_from_path(project_path)
        rules_registry_name = f"{project_name}_rules"
        brain_id = f"{project_name}_rules_brain"
        
        # Create brain using NEW brain config system
        # neuron_source_type options: "registry_keys", "entire_registry", "directory", "file"
        result = brain_manager_func(
            operation="add",
            brain_id=brain_id,
            name=f"{project_name} Rules Brain",
            neuron_source_type="registry_keys",    # Each registry key = one neuron
            neuron_source=rules_registry_name,     # Registry name to read from
            chunk_max=30000                        # Max chars per neuron chunk
        )
        
        # This creates a BrainConfig internally:
        # BrainConfig(
        #     brain_name=brain_id,
        #     neuron_source_type="registry_keys", 
        #     neuron_source="hello_world_project_rules",
        #     chunk_max=30000
        # )
        #
        # The brain will then load neurons like:
        # - registry_key:hello_world_project_rules:rule_1
        # - registry_key:hello_world_project_rules:rule_2  
        # - registry_key:hello_world_project_rules:rule_3
        #
        # Each neuron gets the registry value as content via:
        # registry_heaven_variable={"registry_name": "hello_world_project_rules", "key": "rule_1"}
        
        # Handle creation result and error cases
        if "added to registry" in result:
            print(f"✅ Created rules brain '{brain_id}' for project '{project_name}'")
        else:
            raise RuntimeError(f"Failed to create rules brain: {result}")
        
        return brain_id
    
    async def query_rules_brain(
        self, 
        project_path: str, 
        development_context: str, 
        persona_id: str = None, 
        persona_str: str = None, 
        mode_id: str = None, 
        mode_str: str = None
    ) -> str:
        """
        Query project rules brain for development guidance.
        
        Args:
            project_path: Path to STARLOG project  
            development_context: What the developer is working on
            persona_id: Predefined persona ID
            persona_str: Custom persona description
            mode_id: Predefined mode ID
            mode_str: Custom mode description
            
        Returns:
            Synthesized rules guidance with reasoning
        """
        # Get or create rules brain for project
        brain_id = self._get_or_create_rules_brain(project_path)
        
        # Query brain directly using the proper function with persona/mode
        result = await query_brain_func(
            brain_id, 
            development_context, 
            persona_id=persona_id,
            persona_str=persona_str,
            mode_id=mode_id,
            mode_str=mode_str
        )
        
        if result and "Error:" not in result:
            return f"Rules Guidance:\n\n{result}"
        else:
            return f"No specific rules found for context: {development_context}"
    
    def auto_query_for_file(self, project_path: str, file_path: str, operation: str = "editing") -> str:
        """
        Auto-generate rules query based on file being worked on.
        
        Args:
            project_path: Path to STARLOG project
            file_path: File being worked on  
            operation: What operation is being performed (editing, creating, reviewing)
            
        Returns:
            Contextual rules query for the file
        """
        # Extract file context
        file_extension = file_path.split('.')[-1] if '.' in file_path else ''
        file_name = file_path.split('/')[-1]
        
        # Build contextual query
        context_parts = [
            f"I am {operation} the file: {file_name}"
        ]
        
        if file_extension:
            context_parts.append(f"File type: {file_extension}")
        
        # Add operation-specific context
        if operation == "creating":
            context_parts.append("What coding standards and conventions should I follow?")
        elif operation == "editing":
            context_parts.append("What rules should I keep in mind while making changes?")
        elif operation == "reviewing":
            context_parts.append("What should I check for during code review?")
        
        return " ".join(context_parts)
    
    def _get_or_create_rules_brain(self, project_path: str) -> str:
        """Get existing rules brain or create new one if needed."""
        project_name = self._get_project_name_from_path(project_path)
        brain_id = f"{project_name}_rules_brain"
        
        # Check if brain already exists
        try:
            result = brain_manager_func('get', brain_id=brain_id)
            if "not found" not in result:
                return brain_id
        except:
            pass
            
        # Create brain if it doesn't exist
        return self.create_rules_brain(project_path)
    
    def _get_project_name_from_path(self, project_path: str) -> str:
        """Extract project name from path."""
        import os
        project_name = os.path.basename(project_path.rstrip('/'))
        return project_name.replace(' ', '_').lower()

# Convenience functions for direct usage

async def create_project_rules_brain(project_path: str) -> str:
    """
    Create a brain-agent brain for STARLOG project rules.
    
    Args:
        project_path: Path to STARLOG project
        
    Returns:
        Brain ID for querying rules
    """
    integration = StarlogRulesBrainIntegration()
    return integration.create_rules_brain(project_path)

async def query_project_rules(
    project_path: str, 
    context: str, 
    persona_id: str = None, 
    persona_str: str = None, 
    mode_id: str = None, 
    mode_str: str = None
) -> str:
    """
    Query project rules for development guidance.
    
    Args:
        project_path: Path to STARLOG project
        context: Development context or question
        persona_id: Predefined persona ID (logical_philosopher, senior_scientist, senior_engineer)
        persona_str: Custom persona description
        mode_id: Predefined mode ID (summarize, imagine, reify)
        mode_str: Custom mode description
        
    Returns:
        Relevant rules and guidance
    """
    integration = StarlogRulesBrainIntegration()
    return await integration.query_rules_brain(project_path, context, persona_id, persona_str, mode_id, mode_str)

async def get_file_rules_guidance(project_path: str, file_path: str, operation: str = "editing") -> str:
    """
    Get rules guidance for working on a specific file.
    
    Args:
        project_path: Path to STARLOG project
        file_path: File being worked on
        operation: Operation being performed
        
    Returns:
        File-specific rules guidance
    """
    integration = StarlogRulesBrainIntegration()
    context = integration.auto_query_for_file(project_path, file_path, operation)
    return await integration.query_rules_brain(project_path, context)

# Integration with STARLOG MCP Tools

def add_rules_brain_tool_to_starlog():
    """
    Add rules brain querying as a STARLOG MCP tool.
    
    This would add a new MCP tool that developers can call:
    - query_project_rules(project_path, context)
    - get_file_guidance(project_path, file_path)
    - create_rules_brain(project_path)
    
    Note: Implementation should be added to starlog_mcp.py as FastMCP tools
    """
    # TODO: Implement as STARLOG MCP tool
    # TODO: Add to starlog_mcp.py tool definitions
    # TODO: Handle async calls in MCP context
    pass

# Development Workflow Integration Examples

"""
Example development workflows using rules brain:

1. Starting new feature:
   rules = await query_project_rules("/path/to/project", 
                                   "I'm implementing user authentication")
   
2. Code review:
   guidance = await get_file_rules_guidance("/path/to/project", 
                                          "src/auth/login.py", 
                                          "reviewing")
   
3. Refactoring:
   rules = await query_project_rules("/path/to/project",
                                   "I'm refactoring the database layer to use async/await")

4. Auto-guidance during development:
   # Called automatically when file is opened/modified
   guidance = await get_file_rules_guidance("/path/to/project",
                                          "src/utils/validators.py",
                                          "editing")
"""

# New Brain Config System Usage Examples

"""
Complete documentation of the new brain config system we implemented:

NEURON SOURCE TYPES:
===================

1. "registry_keys" - Each registry key becomes one neuron
   brain_manager_func(
       operation="add",
       brain_id="project_rules_brain",
       neuron_source_type="registry_keys",
       neuron_source="my_project_rules",    # Registry name
       chunk_max=30000
   )
   Results in neurons: registry_key:my_project_rules:rule_1, rule_2, etc.

2. "entire_registry" - Entire registry as one big neuron  
   brain_manager_func(
       operation="add", 
       brain_id="project_overview_brain",
       neuron_source_type="entire_registry",
       neuron_source="my_project_debug_diary",  # Registry name
       chunk_max=30000
   )
   Results in neuron: registry_entire:my_project_debug_diary

3. "directory" - Each file in directory = one neuron (original behavior)
   brain_manager_func(
       operation="add",
       brain_id="docs_brain", 
       neuron_source_type="directory",
       neuron_source="/path/to/docs",      # Directory path
       chunk_max=30000
   )
   Results in neurons: /path/to/docs/file1.md, /path/to/docs/file2.md, etc.

4. "file" - Single file chunked into multiple neurons
   brain_manager_func(
       operation="add",
       brain_id="large_spec_brain",
       neuron_source_type="file", 
       neuron_source="/path/to/huge_spec.md",  # File path
       chunk_max=10000                         # Will chunk file every 10k chars
   )
   Results in neurons: file_chunk:/path/to/huge_spec.md:0:10000, 10000:20000, etc.

STARLOG INTEGRATION PATTERNS:
============================

For STARLOG projects, we typically want:

- Rules Brain: neuron_source_type="registry_keys", neuron_source="{project}_rules"
- Debug Brain: neuron_source_type="registry_keys", neuron_source="{project}_debug_diary"  
- Session Brain: neuron_source_type="registry_keys", neuron_source="{project}_starlog"
- Project Overview: neuron_source_type="entire_registry", neuron_source="{project}_starlog"

BRAIN CONFIG MODEL:
==================

The BrainConfig model now supports:
- brain_name: str = None                    # Brain identifier
- neuron_source_type: Literal[...] = "directory"  # How to load neurons
- neuron_source: str = None                 # Where to load from
- chunk_max: int = 30000                   # Max chars per neuron
- directory: str = None                     # Backwards compatibility
- chunk_size: int = -1                     # Backwards compatibility

NEURON PATH FORMATS:
===================

Different neuron source types create different neuron path formats:

- registry_key:registry_name:key_name
- registry_entire:registry_name  
- /path/to/file.ext (regular files)
- file_chunk:path:start_pos:end_pos

These paths are handled by _build_enhanced_prompt_suffix_blocks() to create
appropriate prompt_suffix_blocks for the LLM context.
"""

# Future Enhancements

"""
Potential future enhancements:

1. Rule Learning:
   - Learn new rules from code review comments
   - Suggest rule additions based on common issues
   
2. Context Awareness:
   - Git branch context (feature/bugfix/hotfix)
   - Recent commit messages and changes
   - Related files being worked on
   
3. Team Integration:
   - Share rule brains across team members
   - Collaborative rule evolution and voting
   
4. IDE Integration:
   - Real-time rules suggestions in IDE
   - Pre-commit rules checking
   - Automated rule violation detection
   
5. Advanced Querying:
   - Natural language rule queries
   - Rule conflict detection and resolution
   - Rule priority and context weighting
"""