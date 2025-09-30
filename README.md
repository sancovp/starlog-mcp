[![Part of STARSYSTEM](https://img.shields.io/badge/Part%20of-STARSYSTEM-blue)](https://github.com/sancovp/starsystem-metarepo)

# STARLOG MCP

STARLOG (Session, Task, and Activity Record LOG) is a comprehensive documentation workflow system designed for Claude Code integration via the Model Context Protocol (MCP).

## Overview

STARLOG provides three integrated documentation types:
- **RULES**: Project guidelines with brain-agent enforcement
- **DEBUG_DIARY**: Real-time development tracking with GitHub issue integration
- **STARLOG**: Session history with START/END markers for context continuity

## Features

### 🏗️ Project Initialization
- Automated project setup with registry creation
- Integrated starlog.hpi file generation
- Context-aware project configuration

### 📏 Rules System
- Hierarchical rule management with categories and priorities
- Brain-agent enforcement integration
- Dynamic rule validation and compliance checking

### 📓 Debug Diary
- Real-time development issue tracking
- Direct GitHub Issues API integration
- Automatic bug report and fix workflow

### 📋 Session Management
- Comprehensive session START/END tracking
- Goal-oriented work sessions with outcomes
- Historical context preservation

### 🧭 HPI (Human-Programming Interface) System  
- Automatic context assembly from latest session + debug diary
- Project orientation for seamless context switching
- Documentation-driven development workflow

## Installation

[Installation instructions pending PyPI publication]

## Quick Start

### Initialize a STARLOG Project

```python
from starlog_mcp import Starlog

starlog = Starlog()
result = starlog.init_project("my_project", "My Project Name")
print(result)
```

### Add Project Rules

```python
result = starlog.add_rule("Always write tests", "my_project", "testing")
print(result)
```

### Start a Development Session

```python
session_data = {
    "session_title": "Feature Implementation",
    "start_content": "Implementing user authentication",
    "context_from_docs": "Based on security requirements doc",
    "session_goals": ["Add login", "Add logout", "Add password reset"]
}
result = starlog.start_starlog(session_data, "my_project")
print(result)
```

### Get Project Context

```python
context = starlog.orient("my_project")
print(context)  # Complete project context for AI assistance
```

## MCP Server Usage

STARLOG includes a built-in MCP server for Claude Code integration:

```bash
starlog-server
```

### Environment Variables

- `HEAVEN_DATA_DIR`: Directory for STARLOG data storage (default: `/tmp/heaven_data`)
- `OPENAI_API_KEY`: Required for brain-agent rule enforcement

### MCP Configuration

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "starlog": {
      "command": "starlog-server",
      "env": {
        "HEAVEN_DATA_DIR": "/path/to/your/data",
        "OPENAI_API_KEY": "your-openai-key"
      }
    }
  }
}
```

## Available MCP Tools

- `init_project(path, name)` - Initialize new STARLOG project
- `rules(path)` - View all project rules
- `add_rule(rule, path, category)` - Add new rule
- `update_debug_diary(diary_entry, path)` - Add debug diary entry  
- `view_debug_diary(path)` - View debug diary
- `start_starlog(session_data, path)` - Start new session
- `view_starlog(path)` - View session history
- `end_starlog(session_id, end_content, path)` - End session
- `orient(path)` - Get complete project context
- `check(path)` - Check project status

## Development

### Running Tests

```bash
pytest tests/
```

### Development Installation

```bash
pip install -e .[dev]
```

## Architecture

STARLOG uses the HEAVEN framework's registry system for persistent storage and provides a clean FastMCP-based server implementation for seamless Claude Code integration.

### Registry Pattern

Data is stored in isolated registries per project:
- `{project_name}_rules` - Project rules with enforcement metadata
- `{project_name}_debug_diary` - Development tracking entries
- `{project_name}_starlog` - Session history with goals and outcomes

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.
