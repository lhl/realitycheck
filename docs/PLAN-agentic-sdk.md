# Reality Check as an Epistemic Scaffold for Agentic Systems

## Overview

This document explores how Reality Check can be integrated as an "epistemic scaffold" into various agentic frameworks. Currently, RC works best as a skill within agentic TUIs (Claude Code, Codex). The goal is to invert this: allow any agent framework to leverage RC's rigorous methodology for claim analysis, evidence evaluation, and prediction tracking.

## Current State

Reality Check currently integrates with:
- **Claude Code** - via plugin (hooks + slash commands) or global skills
- **OpenAI Codex** - via skills ($check, $analyze, etc.)
- **Amp** - via skills with triggers

These are all "skill-based" integrations where the TUI loads methodology as context and the agent executes the workflow.

## Agentic SDK Landscape (Jan 2026)

### Tier 1: Major Vendor SDKs

#### Anthropic SDK (anthropic-sdk-python)
- **Model**: Direct API with tool use via `@beta_tool` decorator
- **Tool Registration**: Function decorators with type hints
- **Context Injection**: System prompts, tool descriptions
- **MCP Support**: Native (Anthropic created MCP)
- **Maturity**: Production-ready, widely used
- **Integration Approach**: RC as a set of tools with methodology in system prompt

```python
from anthropic import Anthropic, beta_tool

@beta_tool
def rc_analyze(url: str, domain: str = "TECH") -> str:
    """Analyze a source using Reality Check 3-stage methodology..."""
    # Inject methodology, call rc-db, etc.
```

#### OpenAI Agents SDK (openai-agents-python)
- **Model**: Agent with instructions, tools, handoffs, guardrails
- **Tool Registration**: `@function_tool` decorator
- **Context Injection**: Agent `instructions` parameter
- **MCP Support**: Not native, but extensible
- **Maturity**: Newer (2025), actively developed
- **Key Feature**: Multi-agent handoffs, sessions, tracing

```python
from agents import Agent, Runner, function_tool

@function_tool
def reality_check(url: str) -> str:
    """Perform Reality Check analysis on a URL."""

rc_agent = Agent(
    name="EpistemicAnalyst",
    instructions=REALITY_CHECK_METHODOLOGY,
    tools=[reality_check, rc_search, rc_validate],
)
```

### Tier 2: Framework Ecosystems

#### LangGraph (LangChain)
- **Model**: Graph-based state machines for agent workflows
- **Tool Registration**: LangChain Tool classes
- **Context Injection**: State schema, node functions
- **MCP Support**: Via langchain-mcp adapter
- **Maturity**: Very mature, large ecosystem
- **Key Feature**: Durable execution, checkpointing, human-in-the-loop

**Pros**: Most flexible, battle-tested, huge community
**Cons**: Can be complex, abstraction overhead

#### CrewAI
- **Model**: Role-based "crews" of collaborating agents
- **Tool Registration**: `@tool` decorator or Tool class
- **Context Injection**: Agent `backstory`, task descriptions
- **MCP Support**: Limited
- **Maturity**: Growing rapidly, 100k+ developers
- **Key Feature**: Multi-agent collaboration, Flows for orchestration

**RC Fit**: Natural mapping - RC methodology as agent backstory, each analysis stage as a task

```python
from crewai import Agent, Task, Crew

analyst = Agent(
    role="Epistemic Analyst",
    goal="Rigorously evaluate claims and evidence",
    backstory=REALITY_CHECK_METHODOLOGY,
    tools=[rc_fetch, rc_analyze, rc_register]
)
```

#### AutoGen (Microsoft)
- **Model**: Multi-agent conversations, AssistantAgent
- **Tool Registration**: Function tools or AgentTool wrapper
- **MCP Support**: Native via McpWorkbench
- **Maturity**: Mature, enterprise-focused
- **Key Feature**: MCP integration, AgentTool for agent-as-tool pattern

**Note**: Microsoft is transitioning to "Agent Framework" - AutoGen continues with maintenance

### Tier 3: Lightweight/Specialized

#### smolagents (Hugging Face)
- **Model**: Code-first agents (~1000 LOC core)
- **Tool Registration**: Class-based or from Hub/MCP/LangChain
- **Context Injection**: Agent instructions
- **MCP Support**: Native `ToolCollection.from_mcp()`
- **Maturity**: Newer, HF backing
- **Key Feature**: Minimal, Hub integration, sandboxed execution

**RC Fit**: Could publish RC tools to HF Hub for easy import

#### PydanticAI
- **Model**: Type-safe agents with Pydantic validation
- **Tool Registration**: Decorated functions with RunContext
- **Context Injection**: `instructions` + dependency injection
- **MCP Support**: Native
- **Maturity**: Newer (from Pydantic team), growing fast
- **Key Feature**: Type safety, structured outputs, evals

**RC Fit**: Excellent - RC's structured claim schema maps naturally to Pydantic models

```python
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

class Claim(BaseModel):
    id: str
    text: str
    type: str  # [F/T/H/P/A/C/S/X]
    domain: str
    evidence_level: str  # E1-E6
    credence: float

rc_agent = Agent(
    'anthropic:claude-sonnet-4-0',
    output_type=list[Claim],
    instructions=REALITY_CHECK_METHODOLOGY
)
```

### Tier 4: Protocol Layer

#### Model Context Protocol (MCP)
- **Model**: Standardized protocol for LLM context
- **Tool Registration**: Server exposes tools via protocol
- **Context Injection**: Resources, prompts
- **Maturity**: Growing adoption (Anthropic, Microsoft, HF, etc.)

**RC as MCP Server**: Most portable approach - any MCP-compatible client can use RC

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RealityCheck")

@mcp.tool()
def analyze(url: str, domain: str = "TECH") -> str:
    """3-stage analysis using Reality Check methodology"""

@mcp.resource("methodology://evidence-hierarchy")
def get_evidence_hierarchy() -> str:
    """Return the E1-E6 evidence hierarchy reference"""
```

## Integration Strategies

### Strategy 1: MCP Server (Recommended Starting Point)

**Approach**: Package RC as an MCP server that any MCP-compatible client can connect to.

**Benefits**:
- Single implementation, works everywhere
- Protocol-level portability
- Supported by: Claude Desktop, AutoGen, smolagents, PydanticAI, VS Code

**Components**:
```
integrations/mcp/
├── server.py           # FastMCP server
├── tools/
│   ├── analyze.py      # /check, /analyze endpoints
│   ├── search.py       # Semantic search
│   └── validate.py     # Data validation
├── resources/
│   ├── methodology.py  # Evidence hierarchy, claim types
│   └── templates.py    # Analysis templates
└── prompts/
    └── analysis.py     # Pre-built analysis prompts
```

### Strategy 2: Native SDK Adapters

**Approach**: Thin adapters for each major SDK that wrap RC functionality.

**Priority Order**:
1. **PydanticAI** - Type safety aligns with RC's structured approach
2. **OpenAI Agents** - Growing adoption, clean API
3. **LangGraph** - Mature ecosystem, enterprise users
4. **CrewAI** - Multi-agent scenarios (claim verification crews)

### Strategy 3: Methodology-as-Context Library

**Approach**: Publish methodology documents as importable context that any framework can inject.

```python
from realitycheck.methodology import (
    EVIDENCE_HIERARCHY,
    CLAIM_TYPES,
    ANALYSIS_STAGES,
    full_methodology,
)

# Use with any agent framework
agent = SomeAgent(
    instructions=full_methodology(),
    tools=[...]
)
```

## Recommended Implementation Plan

### Phase 1: MCP Server
- [ ] Create `integrations/mcp/` with FastMCP server
- [ ] Expose core tools: analyze, search, register, validate
- [ ] Expose resources: methodology docs, templates
- [ ] Test with Claude Desktop, smolagents

### Phase 2: PydanticAI Integration
- [ ] Define Pydantic models for Claim, Source, Analysis
- [ ] Create RC agent with structured outputs
- [ ] Add dependency injection for DB connection
- [ ] Evals for analysis quality

### Phase 3: OpenAI Agents Integration
- [ ] Create function tools wrapping rc-db commands
- [ ] Define EpistemicAnalyst agent with methodology
- [ ] Support handoffs (e.g., to FactChecker agent)
- [ ] Session persistence for multi-turn analysis

### Phase 4: Multi-Agent Scenarios (CrewAI/LangGraph)
- [ ] Design claim verification crew (Analyst + FactChecker + Devil's Advocate)
- [ ] LangGraph workflow for staged analysis with human-in-the-loop
- [ ] Cross-agent claim registry sharing

## Technical Considerations

### State Management
- All frameworks support some form of state/memory
- RC's LanceDB is the source of truth
- Agents should query, not cache claim data

### Tool Design Principles
1. **Atomic operations**: One tool per RC CLI command
2. **Structured outputs**: Return Pydantic models or JSON
3. **Methodology injection**: Include relevant methodology in tool descriptions
4. **Error handling**: Clear error messages for agent self-correction

### Context Window Management
- Full methodology is ~20k tokens
- Provide tiered context: minimal (3k), standard (10k), full (20k)
- Use MCP resources for on-demand methodology retrieval

## Open Questions

1. **Versioning**: How to handle methodology updates across deployed agents?
2. **Verification**: Should agents self-verify claims or delegate to specialized verifier?
3. **Confidence Calibration**: Can we train agents to better calibrate credence scores?
4. **Multi-agent Consensus**: How to handle disagreement between agents on claim credence?

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [PydanticAI](https://ai.pydantic.dev/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [CrewAI](https://github.com/crewAIInc/crewAI)
- [smolagents](https://github.com/huggingface/smolagents)
- [AutoGen](https://github.com/microsoft/autogen)
