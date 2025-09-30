# STARLOG Flight Config Specification

## Overview

STARLOG Flight Configs are modulators that extend the base STARLOG session workflow with domain-specific subchains. They provide a way to customize STARLOG sessions for different project types and workflows while maintaining the immutable base STARLOG structure.

## Architecture

### Base STARLOG Flight (Immutable)
```
check → orient → start_session → work_loop → end_session
```

This base structure can never be destroyed or overridden.

### Flight Config Extension
Flight configs can only add **one thing**: a waypoint subchain that executes as part of the work_loop phase.

```
check → orient → start_session → work_loop + [subchain] → end_session
```

## FlightConfig Model

```python
class FlightConfig(BaseModel):
    """Flight configs extend the work_loop with a waypoint subchain."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Flight config name (must end with '_flight_config')")
    original_project_path: str = Field(..., description="Path where created")
    category: str = Field(default="general", description="Category (research, development, analysis, etc.)")
    description: str = Field(..., description="What this flight pattern adds")
    
    # The only extension point: optional waypoint subchain
    work_loop_subchain: Optional[str] = Field(
        default=None, 
        description="Path to PayloadDiscovery JSON config for subchain execution"
    )
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

## Naming Convention

**Flight Config Names Must End With `_flight_config`**

- ✅ `giint_research_flight_config`
- ✅ `debugging_analysis_flight_config`
- ✅ `code_review_flight_config`
- ❌ `giint_waypoint` (this is a regular waypoint)
- ❌ `research_config` (missing suffix)

This distinguishes STARLOG session modulators from standalone waypoints.

## Execution Flow

### Without Flight Config
```
start_waypoint_journey("base_starlog.json", path)
→ check → orient → start → work_loop → end
```

### With Flight Config
```
start_waypoint_journey(config_path="/configs/research_methodology_waypoint.json", starlog_path=path)
→ check → orient → start → work_loop → "Continue the journey with waypoint.continue_journey('research_methodology_waypoint.json', path) to start the workflow loop subchain system" → execute subchain PayloadDiscovery → end
```

## Work Loop Subchain Requirements

### Single PayloadDiscovery Reference
```python
work_loop_subchain = "/configs/research_methodology_waypoint.json"
```

- **Not** a list of waypoints (no nested orchestration)
- **One** complete PayloadDiscovery chain that contains its own sequence of steps
- If you want to compose multiple waypoints, do it at the PayloadDiscovery level first

### Required Control Flow Handoff
The final PayloadDiscoveryPiece in the subchain **must** hand control back to STARLOG:

```markdown
# Final Step: Return to STARLOG Session

You have completed the [research methodology / debugging / analysis] workflow.

Now continue the STARLOG session:
waypoint.continue_journey("starlog_flight_config")

This will return you to the base STARLOG flow to complete the session with end_session.
```

**Complete Execution Flow:**
1. Base STARLOG: check → orient → start → work_loop
2. Work_loop: "Continue the journey with waypoint.continue_journey('{subchain_name}', 'your/starlog/path') to start the workflow loop subchain system"  
3. Execute subchain PayloadDiscovery (research/debugging/etc waypoint)
4. Final piece of subchain: `waypoint.continue_journey("starlog_flight_config")`
5. Back to base STARLOG: end_session

This creates proper control flow between the base session and extended subchains.

### Amplificatory Loop Recommendation
For stable recursion, subchains should be amplificatory processes:

- ✅ "Iteratively improve research methodology"
- ✅ "Continuously analyze and enhance findings" 
- ✅ "Build-Measure-Learn cycles for hypothesis testing"
- ⚠️ "Write final report" (linear, may cause termination issues)

Think OODA, DMAIC, Build-Measure-Learn - processes that can iterate and improve.

## Composition Architecture

**If you want to chain multiple waypoints:**

1. **Create individual waypoints:**
   - `literature_review_waypoint.json`
   - `data_analysis_waypoint.json`
   - `synthesis_waypoint.json`

2. **Compose them into one PayloadDiscovery:**
   ```bash
   # Use PayloadDiscovery compiler or manual composition
   create_composed_waypoint(
     sources=["literature_review_waypoint.json", "data_analysis_waypoint.json"],
     output="research_methodology_waypoint.json"
   )
   ```

3. **Reference in FlightConfig:**
   ```python
   work_loop_subchain = "/configs/research_methodology_waypoint.json"
   ```

**Composition happens at the PayloadDiscovery level, not the FlightConfig level.**

## Usage Examples

### Research Flight Config
```python
FlightConfig(
    name="academic_research_flight_config",
    category="research",
    description="Extends STARLOG with systematic literature review and analysis workflow",
    work_loop_subchain="/configs/academic_methodology_waypoint.json"
)
```

### Development Flight Config
```python
FlightConfig(
    name="tdd_development_flight_config", 
    category="development",
    description="Extends STARLOG with Test-Driven Development workflow",
    work_loop_subchain="/configs/tdd_methodology_waypoint.json"
)
```

### Debugging Flight Config
```python
FlightConfig(
    name="systematic_debugging_flight_config",
    category="debugging", 
    description="Extends STARLOG with systematic debugging methodology",
    work_loop_subchain="/configs/debug_methodology_waypoint.json"
)
```

## Flight Config Management Tools

### Required Tools (To Be Implemented)
- `add_flight_config(path, name, config_data, category)` - Create new flight configs
- `delete_flight_config(path, name)` - Remove flight configs  
- `update_flight_config(path, name, config_data)` - Modify existing configs
- `read_starlog_flight_config_instruction_manual()` - Show schema/examples

### Existing Tools
- `fly(path, page, category)` - Browse/paginate existing flight configs

## Conversational Topology

**Key Insight:** STARLOG bounds a conversation, and subchains are completed autonomously within that single conversation.

- **One STARLOG session = One complete conversation**
- **Subchains execute autonomously** without human interruption
- **Flight configs shape what happens in conversations** while STARLOG shapes how conversations happen

This creates **conversational programming** - using structured instructions to create deterministic workflows within conversation boundaries.

## Mathematical Properties

**Amplificatory Loop Safety:** For stable recursion, subchains should be amplificatory:
- Input → Process → Output that can feed back as new input
- Each iteration adds value/improvement
- Natural stopping conditions exist

**Examples:**
- Non-amplificatory: "Write a 5 paragraph essay" (one-time completion)  
- Amplificatory: "Create and/or edit 5 paragraph essays" (iterative improvement)

This ensures subchains can safely refire within the recursive work_loop structure.