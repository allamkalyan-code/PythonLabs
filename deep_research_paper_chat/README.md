# CrewAI Flow Workshop - Intelligent Research & Conversation System

This project demonstrates an advanced AI system built with [CrewAI Flow](https://crewai.com) that intelligently routes between research and conversation modes. The system can conduct comprehensive academic research using multiple databases and maintain natural conversations with users.

## Project Overview

This is an **intelligent routing system** that:

1. **Analyzes user intent** - Determines whether a message needs research or conversation
2. **Conducts deep research** - Searches academic databases (arXiv, Nature, IEEE, PubMed) for scholarly papers
3. **Maintains conversations** - Provides natural, contextual responses for non-research queries
4. **Preserves context** - Tracks conversation history across interactions

### Key Features

- **Smart Intent Routing**: Automatically classifies user messages as research or conversation
- **Academic Research**: Searches multiple scholarly databases with proper citations
- **Conversation Memory**: Maintains message history throughout the session
- **Custom Tools**: Integrated deep research capabilities via Firecrawl API
- **Flow Orchestration**: Uses CrewAI Flow for complex multi-agent workflows

## Getting Started from Scratch

### 1. Install CrewAI

First, install CrewAI globally:

```bash
pip install crewai[tools]
```

### 2. Create a New Flow Project

Generate a new CrewAI flow project:

```bash
crewai create flow your_flow_name
cd your_flow_name
```

### 3. Setup Environment

Ensure you have Python >=3.10 <3.14 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

Install UV if you haven't already:

```bash
pip install uv
```

Install project dependencies:

```bash
crewai install
```

### 4. Configure API Keys

Create a `.env` file in your project root and add your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

**Required API Keys:**
- **OpenAI API Key**: For LLM functionality and intent routing
- **Firecrawl API Key**: For academic research and paper searching

## Understanding the System Architecture

### Flow Structure

The main flow (`DeepResearchFlow`) uses CrewAI's `@persist()` decorator and orchestrates these key components:

#### Core Data Models
- **`Message`**: Tracks role, content, and timestamp for conversation history
- **`RouterIntent`**: Structures LLM routing decisions with intent classification and research query generation
- **`Source`**: Represents research sources with URL, title, and relevant content
- **`SearchResult`**: Contains comprehensive research summary with inline citations and source list
- **`FlowState`**: Maintains user message, conversation history, research queries, and results

#### Flow Methods

1. **Starting Flow** (`@start() starting_flow`)
   - Initializes the flow with user message
   - Adds user message to conversation history
   - Triggers the routing process

2. **Intent Router** (`@router(starting_flow) routing_intent`)
   - Uses GPT-4.1 mini with `response_format=RouterIntent` for structured output
   - Analyzes user messages and conversation history
   - Classifies intent as "research" or "conversation" using detailed criteria
   - Generates optimized research queries when research intent is detected
   - Returns routing decision for flow orchestration

3. **Research Handler** (`@listen("research") handle_research`)
   - Creates specialized `Deep Research Specialist` agent
   - Uses `DeepResearchPaper()` tool for academic database searches
   - Executes research with `response_format=SearchResult` for structured output
   - Requires comprehensive summaries with inline URL citations: `(https://example.com/source)`
   - Returns complete research results with sources list

4. **Conversation Handler** (`@listen("conversation") follow_up_conversation`)
   - Uses GPT-4.1 mini with higher temperature (0.7) for natural responses
   - Maintains conversation context and flow
   - Provides helpful responses while guiding toward research opportunities
   - Adds assistant responses to message history

### Custom Tools

- **DeepResearchPaper**: Searches academic databases and returns exactly 5 research papers with full content and proper citations

## Technical Implementation Details

### Key Implementation Features

#### Structured LLM Responses
- **RouterIntent**: Uses Pydantic models for structured LLM responses with `user_intent`, `research_query`, and `reasoning` fields
- **SearchResult**: Enforces structured research output with `research_summary` and `sources_list` fields
- **Response Format Validation**: All LLM calls use `response_format` parameter for type-safe outputs

#### Flow Decorators & Orchestration
- **`@persist()`**: Enables flow state persistence across sessions
- **`@start()`**: Marks the entry point method (`starting_flow`)
- **`@router()`**: Creates conditional routing based on LLM decisions
- **`@listen()`**: Defines event-driven handlers for "research" and "conversation" intents

#### Conversation Management
- **Message History**: Persistent tracking using `List[Message]` with role, content, and timestamp
- **Context Awareness**: All LLM prompts include conversation history for context-aware responses
- **State Management**: Centralized state handling through `FlowState` class

#### LLM Configuration
- **Router LLM**: GPT-4.1 mini with temperature=0.1 for consistent routing decisions
- **Conversation LLM**: GPT-4.1 mini with temperature=0.7 for natural, varied responses
- **Research Agent**: Specialized agent with verbose=True for detailed research execution

#### Research Output Requirements
- **Inline Citations**: Every fact must be followed by source URL in parentheses format: `(URL)`
- **Comprehensive Summaries**: Organized by topics/themes with cohesive narrative structure
- **Source Documentation**: Complete source list with URL, title, and relevant content

## Installation & Setup

Ensure you have Python >=3.10 <3.14 installed on your system.

1. Clone this repository or use it as a template
2. Install dependencies:

```bash
crewai install
```

3. Configure your `.env` file with required API keys
4. Run the system:

```bash
crewai run
```

## Customization Guide

### Modifying from the Base Template

Starting from a fresh CrewAI flow, here's how to adapt it for this research system:

1. **Update Flow State** (`FlowState` class):
   - Add message history tracking
   - Include research query handling
   - Add intent classification fields

2. **Implement Intent Routing**:
   - Create router method with LLM classification
   - Define research vs conversation criteria
   - Add proper prompt engineering

3. **Add Research Capabilities**:
   - Integrate research tools (Firecrawl API)
   - Create specialized research agent
   - Implement structured output formatting

4. **Build Conversation System**:
   - Add conversation handler
   - Implement context awareness
   - Include message history management

### Configuration Files

- **`src/crewai_flow_workshop1/main.py`**: Main flow logic and orchestration
- **`src/crewai_flow_workshop1/tools/deep_research_paper.py`**: Research tool implementation
- **`pyproject.toml`**: Project configuration and dependencies

### Core Dependencies & Imports

The main.py implementation relies on these key imports:

```python
from crewai.flow import Flow, listen, start, router, persist
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime
from crewai import LLM, Agent
import json
```

#### Key Features Used:
- **CrewAI Flow**: `Flow`, `@listen`, `@start`, `@router`, `@persist` decorators
- **Pydantic Models**: Type-safe data structures with `BaseModel` and `Field`
- **Type Hints**: `Literal`, `List`, `Optional` for strict typing
- **LLM Integration**: Direct `LLM` class usage with structured responses
- **Agent Creation**: Dynamic agent creation with specialized roles and tools

## Running the Project

Execute the flow from the project root:

```bash
crewai run
```

The system will:
1. Start with the default message: "help me researching on the latest trends in ai"
2. Add the user message to conversation history with timestamp
3. Route the message through GPT-4.1 mini intent classification
4. Either conduct deep research (with academic database search) or provide conversational response
5. Maintain persistent message history for context across interactions

### Utility Functions

The main.py file also includes utility functions:

- **`kickoff()`**: Initializes and runs the `DeepResearchFlow` with tracing enabled
- **`plot()`**: Generates a visual representation of the flow structure  
- **Direct execution**: Running `python main.py` calls `kickoff()` for immediate flow execution

## Example Usage

### Research Query Example
```
User: "What are the latest studies on transformer architectures in 2024?"
System: → Routes to research → Returns academic papers with citations
```

### Conversation Example
```
User: "Hello, how does this system work?"
System: → Routes to conversation → Provides explanation and guidance
```

### Follow-up Research Example
```
Previous: Discussion about AI ethics
User: "Can you find more studies about bias in machine learning?"
System: → Routes to research with context → Returns relevant bias studies
```

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure both `OPENAI_API_KEY` and `FIRECRAWL_API_KEY` are set in your `.env` file
2. **Python Version**: Verify you're using Python >=3.10 <3.14
3. **Dependencies**: Run `crewai install` to ensure all packages are properly installed
4. **Research Timeout**: If research queries timeout, try more specific search terms

### Development Tips

- Use `crewai run` for full execution
- Check logs for detailed flow execution information
- Modify the default query in `FlowState` for different starting points
- Adjust research limits and timeouts in the tool configuration

## Support & Resources

For support, questions, or feedback:

- **CrewAI Documentation**: [docs.crewai.com](https://docs.crewai.com)
- **CrewAI GitHub**: [github.com/joaomdmoura/crewai](https://github.com/joaomdmoura/crewai)
- **CrewAI Discord**: [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- **CrewAI Chat**: [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create intelligent systems together with the power and simplicity of CrewAI Flow!
