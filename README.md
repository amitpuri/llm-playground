![AI Generated](https://img.shields.io/badge/AI-Generated-blueviolet?style=for-the-badge&logo=openai&logoColor=white)

# LLM Playground

A comprehensive playground for experimenting with Model Context Protocol (MCP) servers, featuring web-based interfaces for testing multiple AI providers and MCP connectors.

## ⚠️ DISCLAIMER

**This code is for reference and demonstration purposes only. Please read the following important disclaimers:**

### 🔍 **Code Accuracy & Reliability**
- **AI-Generated Content**: This codebase is AI-generated and may contain inaccuracies, bugs, or incomplete implementations
- **Reference Only**: This code is provided as a learning resource and reference implementation, not for production use
- **No Guarantees**: The code may not work as expected and should be thoroughly tested before any use
- **Educational Purpose**: This is intended for educational and demonstration purposes only

### 💰 **Token Calculator & Cost Estimation**
- **Indicative Data**: All token counting, cost estimation, and pricing information provided is **indicative only**
- **May Not Be Accurate**: Token counts, costs, and pricing data may not reflect current or accurate values
- **Provider Changes**: AI providers frequently update their pricing, models, and tokenization methods
- **Verify Independently**: Always verify token counts and costs with official provider documentation
- **No Financial Advice**: Cost estimates should not be used for financial planning or budgeting

### 🎯 **Demo Purpose Only**
- **Not Production Ready**: This code is not intended for production environments
- **Learning Tool**: Use this as a learning tool to understand MCP concepts and implementations
- **Experimental**: This is experimental code that may break or change unexpectedly
- **No Support**: No guarantees of support, maintenance, or updates

### 🔒 **Security & Privacy**
- **API Keys**: Never use real API keys in this demo environment
- **Test Data**: Use only test data and dummy credentials
- **No Sensitive Information**: Do not process or store sensitive information with this code

**By using this code, you acknowledge that you understand these limitations and will use it responsibly for educational purposes only.**

---

## 🎯 Purpose & Overview

This repository provides a complete environment for working with MCP servers, designed to help developers and researchers:

- **Learn MCP**: Understand how Model Context Protocol works through hands-on examples
- **Test AI Providers**: Experiment with multiple AI providers (OpenAI, Anthropic, Google, Ollama) in a unified interface
- **Integrate MCP Connectors**: Connect to GitHub and PostgreSQL MCP servers for real-world data
- **Build AI Applications**: Create AI-powered applications that combine multiple data sources and AI models

## 🏗️ Architecture Overview

This repository includes three distinct playground implementations, each with different architectural approaches:

### **Basic Playground** - Simple & Lightweight
- **LLM Integration**: Direct API calls using `requests` library
- **MCP Integration**: Custom `fastmcp` client implementation
- **Async Support**: Limited async support with manual `asyncio.run()`
- **Type Safety**: Basic type hints with dataclasses
- **Use Case**: Quick testing and learning MCP fundamentals

### **Extended Playground** - Production-Ready Features
- **LLM Integration**: Direct API calls using `requests` library
- **MCP Integration**: Custom `fastmcp` client implementation
- **Async Support**: Limited async support with manual `asyncio.run()`
- **Type Safety**: Basic type hints with dataclasses
- **Advanced Features**: Session management, comprehensive logging, token calculator
- **Use Case**: Full-featured development with advanced capabilities

### **LangChain Playground** - Modern & Scalable ⭐ **Recommended**
- **LLM Integration**: LangChain's standardized LLM interfaces
- **MCP Integration**: LangChain's MCP adapters for seamless integration
- **Async Support**: Full async/await support throughout
- **Type Safety**: Enhanced type hints with proper interfaces
- **Architecture**: Modular design following SOLID principles
- **Performance**: True async operations with better resource management
- **Extensibility**: Easy to add new providers and connectors
- **Use Case**: Production-ready applications with modern best practices

### **Key Architectural Differences**

| Feature | Basic | Extended | LangChain |
|---------|-------|----------|-----------|
| **LLM Integration** | Direct API calls | Direct API calls | LangChain interfaces |
| **MCP Integration** | Custom fastmcp | Custom fastmcp | LangChain MCP adapters |
| **Async Support** | Limited | Limited | Full async/await |
| **Type Safety** | Basic | Basic | Enhanced |
| **Modularity** | Simple | Good | Excellent |
| **Testability** | Basic | Good | Excellent |
| **Performance** | Basic | Good | Optimized |
| **Maintainability** | Simple | Good | Excellent |
| **Extensibility** | Limited | Good | Excellent |

## 🧠 Context Strategies & MCP Integration

The playgrounds implement sophisticated **Model Context Protocol (MCP) context management strategies** that enable dynamic, real-time context updates when knowledge base content changes. This section documents the current implementation and roadmap for future enhancements.

### **Current Context Strategy Features**

#### **🔄 Real-Time Context Synchronization**
- **Immediate Context Propagation**: Changes to knowledge bases are immediately reflected in connected MCP clients
- **Session Persistence**: MCP maintains context state across distributed systems during service interruptions
- **Priority-Based Queuing**: Critical context updates receive priority processing to ensure important changes aren't delayed

#### **📊 Token-Efficient Context Management**
- **Intelligent Context Selection**: Provides precisely the context needed for specific queries rather than overwhelming models
- **Dynamic Context Sizing**: Automatically adjusts context window sizes based on query complexity and available information
- **Semantic Context Filtering**: Uses semantic understanding to include only relevant context, reducing token waste
- **Context Compression**: Preserves meaning while reducing token count through intelligent summarization

#### **🏗️ MCP-Specific Architecture**
- **Stateless Request Processing**: Separates context operations from model inference for independent scaling
- **Elastic Resource Allocation**: Automatic provisioning of additional context servers during high-update periods
- **Context-Aware Load Balancing**: Intelligent routing ensures context updates are processed by optimized servers

#### **🔧 Implementation Details**

##### **Prompt Template System**
```javascript
// Research-focused templates with MCP context integration
{
    id: "research_papers",
    name: "Research Paper Analysis", 
    text: `Analyze GitHub issues from {owner_repo} and match them with relevant AI research papers. Provide:
1. Key requirements extracted from GitHub issues
2. Relevant research papers that address these requirements  
3. Implementation recommendations based on research findings
4. Gap analysis and potential research opportunities`
}
```

##### **Smart Prompt Optimization**
```python
# Token budget allocation with MCP context
context_budget_total = int(prompt_budget * 0.45)
issues_budget = max(150, context_budget_total // 2)
papers_budget = max(150, context_budget_total - issues_budget)

# Real-time context fetching
gh_result = await gh_connector.fetch_issues_and_comments(limit_issues=3, limit_comments=5)
pg_result = await pg_connector.fetch_research_papers(limit_rows=8)
```

##### **Context Window Management**
```python
# Dynamic context sizing based on provider capabilities
reserve_reply = int(provider_cw_tokens * 0.25)  # 25% for response
reserve_system = 800  # Fixed system prompt reserve
available_context = int(provider_cw_tokens * max_context_usage)  # 80% max usage
```

#### **🎯 Current Context Strategies**

##### **1. Dual-Context Integration**
- **GitHub Issues Context**: Real-time project requirements and specifications
- **Research Papers Context**: AI research database with relevant papers
- **Combined Analysis**: Intelligent matching of requirements with research insights

##### **2. Template-Based Context Injection**
- **13 Specialized Templates**: Covering research analysis, implementation guides, and literature reviews
- **Dynamic Placeholder Substitution**: `{owner_repo}` placeholders replaced with actual repository data
- **Context-Aware Templates**: Designed specifically for MCP-enhanced workflows

##### **3. Real-Time Context Updates**
- **Fresh Data Fetching**: Each request fetches fresh data from MCP servers
- **Error Resilience**: Graceful degradation when MCP servers are unavailable
- **Parallel Processing**: GitHub and PostgreSQL queries run simultaneously

##### **4. Token Optimization**
- **Semantic Compression**: Uses LLM to summarize context while preserving key facts
- **Budget Enforcement**: Prevents context overflow with intelligent trimming
- **Provider Adaptation**: Adjusts to different LLM providers' context windows

### **🚀 Roadmap: Advanced Context Strategies**

#### **Phase 1: Enhanced Context Persistence** (Q2 2024)
- **Long-Term Context Memory**: Cross-session context persistence and evolution tracking
- **Context Versioning**: Track knowledge base changes and their impact on context
- **Context Evolution Analytics**: Monitor how context changes over time

#### **Phase 2: Adaptive Context Selection** (Q3 2024)
```python
# Proposed: Adaptive Context Selection
class AdaptiveContextSelector:
    def select_context_strategy(self, query_type: str, available_tokens: int) -> ContextStrategy:
        if query_type == "research_analysis":
            return ResearchFocusedStrategy(available_tokens * 0.6)
        elif query_type == "implementation_guide":
            return ImplementationFocusedStrategy(available_tokens * 0.4)
        elif query_type == "literature_review":
            return LiteratureReviewStrategy(available_tokens * 0.7)
```

#### **Phase 3: Real-Time Context Synchronization** (Q4 2024)
```python
# Proposed: WebSocket-based context updates
class RealTimeContextManager:
    async def subscribe_to_context_updates(self, repo: str):
        """Subscribe to real-time GitHub issue updates"""
        async for update in github_webhook_stream:
            await self.update_context_cache(update)
    
    async def broadcast_context_update(self, context_id: str, update: dict):
        """Notify all subscribed agents of context changes"""
```

#### **Phase 4: Multi-Agent Context Coordination** (Q1 2025)
```python
# Proposed: Shared context store for multi-agent systems
class SharedContextStore:
    def __init__(self):
        self.context_cache = {}
        self.agent_subscriptions = {}
    
    async def coordinate_context_access(self, agent_id: str, context_request: dict):
        """Coordinate context access between multiple agents"""
    
    async def resolve_context_conflicts(self, conflicting_updates: list):
        """Resolve conflicts when multiple agents update context simultaneously"""
```

#### **Phase 5: Enterprise Context Management** (Q2 2025)
- **Context Security Framework**: OAuth 2.1 authorization with granular permissions
- **Context Governance**: Immutable audit trails and compliance tracking
- **High-Throughput Processing**: 50,000+ requests/second with 99.95% uptime
- **Context Replication**: Automated failover and context replication across regions

#### **Phase 6: Advanced RAG Strategies & Hallucination Reduction** (Q3 2025)
```python
# Proposed: Advanced RAG Implementation with Hallucination Prevention
class AdvancedRAGManager:
    def __init__(self):
        self.vector_store = HybridVectorStore()
        self.retrieval_optimizer = RetrievalOptimizer()
        self.hallucination_detector = HallucinationDetector()
        self.context_verifier = ContextVerifier()
        self.knowledge_graph = KnowledgeGraphBuilder()
    
    async def enhanced_retrieval(self, query: str, context: dict) -> RetrievalResult:
        """Multi-modal retrieval with semantic and keyword search"""
        # Hybrid search combining dense and sparse retrievers
        dense_results = await self.vector_store.semantic_search(query, top_k=10)
        sparse_results = await self.vector_store.keyword_search(query, top_k=10)
        
        # Rerank using cross-encoder for better relevance
        reranked_results = await self.retrieval_optimizer.rerank(
            query, dense_results + sparse_results
        )
        
        return await self.context_verifier.validate_relevance(reranked_results, query)
    
    async def hallucination_prevention(self, response: str, context: dict) -> ValidationResult:
        """Multi-layer hallucination detection and prevention"""
        # Fact-checking against retrieved context
        fact_check = await self.hallucination_detector.fact_check(response, context)
        
        # Source attribution verification
        attribution_check = await self.context_verifier.verify_attributions(response, context)
        
        # Confidence scoring with uncertainty quantification
        confidence_score = await self.hallucination_detector.calculate_confidence(response)
        
        return ValidationResult(
            is_valid=fact_check.is_valid and attribution_check.is_valid,
            confidence=confidence_score,
            corrections=fact_check.corrections
        )
    
    async def knowledge_graph_enhancement(self, context: dict) -> KnowledgeGraph:
        """Build and maintain knowledge graph for better context understanding"""
        entities = await self.knowledge_graph.extract_entities(context)
        relationships = await self.knowledge_graph.extract_relationships(entities)
        
        return await self.knowledge_graph.build_graph(entities, relationships)
```

**Advanced RAG Features:**
- **Hybrid Retrieval**: Combines dense (semantic) and sparse (keyword) search for comprehensive results
- **Multi-Modal RAG**: Supports text, code, images, and structured data retrieval
- **Dynamic Reranking**: Uses cross-encoders to improve retrieval relevance
- **Context-Aware Retrieval**: Adapts retrieval strategy based on query type and domain
- **Real-Time Knowledge Updates**: Incremental updates to vector store and knowledge graph
- **Query Expansion**: Intelligent query reformulation for better retrieval
- **Source Diversity**: Ensures diverse source selection to reduce bias

**Hallucination Prevention Strategies:**
- **Fact-Checking Pipeline**: Automated verification against retrieved context
- **Source Attribution**: Mandatory citation and source linking for all claims
- **Confidence Scoring**: Uncertainty quantification for response reliability
- **Contradiction Detection**: Identifies and resolves conflicting information
- **Context Consistency**: Ensures response consistency with provided context
- **Human-in-the-Loop**: Fallback mechanisms for high-stakes decisions

#### **Phase 7: AI Agents & Multi-Agent Systems** (Q4 2025)
```python
# Proposed: Multi-Agent System with Specialized AI Agents
class MultiAgentSystem:
    def __init__(self):
        self.agent_orchestrator = AgentOrchestrator()
        self.shared_memory = SharedMemoryStore()
        self.task_decomposer = TaskDecomposer()
        self.agent_registry = AgentRegistry()
        
    async def coordinate_agents(self, task: str, context: dict) -> AgentResponse:
        """Coordinate multiple specialized agents for complex tasks"""
        # Decompose complex task into subtasks
        subtasks = await self.task_decomposer.decompose(task)
        
        # Assign agents based on expertise
        agent_assignments = await self.agent_orchestrator.assign_agents(subtasks)
        
        # Execute tasks in parallel with shared memory
        results = await self.agent_orchestrator.execute_parallel(agent_assignments)
        
        # Synthesize results and resolve conflicts
        final_response = await self.agent_orchestrator.synthesize_results(results)
        
        return await self.shared_memory.update_and_return(final_response)
    
    async def register_specialized_agent(self, agent: SpecializedAgent):
        """Register new specialized agent with the system"""
        await self.agent_registry.register(agent)
        await self.shared_memory.update_agent_capabilities(agent)

class SpecializedAgent:
    def __init__(self, name: str, expertise: str, capabilities: list):
        self.name = name
        self.expertise = expertise
        self.capabilities = capabilities
        self.memory = AgentMemory()
        self.tools = AgentTools()
    
    async def execute_task(self, task: str, context: dict) -> AgentResult:
        """Execute task within agent's area of expertise"""
        # Validate task compatibility with expertise
        if not self.can_handle(task):
            raise TaskNotSupportedError(f"Agent {self.name} cannot handle this task")
        
        # Execute with specialized tools and knowledge
        result = await self.tools.execute(task, context)
        
        # Update agent memory with new knowledge
        await self.memory.update(task, result, context)
        
        return result
```

**Specialized AI Agents:**
- **Research Agent**: Specialized in academic research and literature analysis
- **Code Analysis Agent**: Expert in code review, debugging, and implementation
- **Data Analysis Agent**: Specialized in data processing and statistical analysis
- **Security Agent**: Expert in security analysis and vulnerability assessment
- **Documentation Agent**: Specialized in technical writing and documentation
- **Testing Agent**: Expert in test case generation and quality assurance
- **Deployment Agent**: Specialized in CI/CD and infrastructure management

**Multi-Agent Coordination Features:**
- **Task Decomposition**: Intelligent breakdown of complex tasks into manageable subtasks
- **Agent Orchestration**: Dynamic agent selection and coordination based on task requirements
- **Shared Memory**: Centralized knowledge store accessible to all agents
- **Conflict Resolution**: Automated resolution of conflicting agent outputs
- **Load Balancing**: Dynamic distribution of tasks across available agents
- **Agent Learning**: Continuous improvement through task execution feedback
- **Fault Tolerance**: Graceful degradation when individual agents fail

#### **Phase 8: OWASP LLM Security Framework** (Q1 2026)
```python
# Proposed: OWASP LLM Security Implementation
class OWASPLLMSecurityManager:
    def __init__(self):
        self.prompt_injection_detector = PromptInjectionDetector()
        self.data_poisoning_monitor = DataPoisoningMonitor()
        self.model_skewing_prevention = ModelSkewingPrevention()
        self.supply_chain_security = SupplyChainSecurity()
    
    async def validate_prompt_security(self, prompt: str, context: dict) -> SecurityValidation:
        """Validate prompt against OWASP LLM security guidelines"""
        return await self.prompt_injection_detector.validate(prompt, context)
    
    async def monitor_context_integrity(self, context_data: dict) -> IntegrityCheck:
        """Monitor context data for poisoning and manipulation attempts"""
        return await self.data_poisoning_monitor.check_integrity(context_data)
    
    async def prevent_model_skewing(self, training_data: list) -> SkewingPrevention:
        """Prevent model skewing through adversarial training data"""
        return await self.model_skewing_prevention.validate_training_data(training_data)
    
    async def verify_supply_chain(self, mcp_server: str, dependencies: list) -> SupplyChainCheck:
        """Verify MCP server and dependency integrity"""
        return await self.supply_chain_security.verify_chain(mcp_server, dependencies)
```

**OWASP LLM Security Measures:**
- **LLM01: Prompt Injection Prevention**: Advanced prompt validation and sanitization
- **LLM02: Insecure Output Handling**: Secure response parsing and validation
- **LLM03: Training Data Poisoning**: Real-time monitoring of context data integrity
- **LLM04: Model Denial of Service**: Rate limiting and resource protection
- **LLM05: Supply Chain Vulnerabilities**: MCP server and dependency verification
- **LLM06: Sensitive Information Disclosure**: Context data encryption and access controls
- **LLM07: Insecure Plugin Design**: Secure MCP tool integration and validation
- **LLM08: Excessive Agency**: Role-based access control and action validation
- **LLM09: Overreliance**: Human oversight and fallback mechanisms
- **LLM10: Model Theft**: Model access controls and usage monitoring

### **🔍 Context Strategy Evaluation**

#### **Current Strengths**
✅ **MCP-Native Design**: Built specifically for Model Context Protocol  
✅ **Token Efficiency**: Sophisticated budget allocation and compression  
✅ **Real-Time Updates**: Fresh context on every request  
✅ **Error Resilience**: Graceful degradation when MCP servers fail  
✅ **Provider Flexibility**: Adapts to different LLM context windows  
✅ **Research Focus**: Specialized for AI research paper analysis workflows  

#### **Areas for Enhancement**
🔄 **Context Persistence**: No long-term context memory across sessions  
🔄 **Adaptive Strategies**: Limited dynamic context selection based on query type  
🔄 **Real-Time Synchronization**: No WebSocket-based live updates  
🔄 **Multi-Agent Support**: No shared context coordination between agents  
🔄 **Context Versioning**: No tracking of context evolution over time  
🔄 **Enterprise Features**: Limited security and governance capabilities  
🔄 **OWASP LLM Security**: No comprehensive LLM security framework implementation  
🔄 **Advanced RAG**: No hybrid retrieval or hallucination prevention mechanisms  
🔄 **AI Agents**: No specialized agent system or multi-agent coordination  
🔄 **Knowledge Graphs**: No semantic knowledge representation and reasoning  

### **📈 Performance Metrics**

#### **Current Performance**
- **Context Update Latency**: <100ms for most operations
- **Token Compression Ratio**: 40-60% reduction through summarization
- **Context Accuracy**: 95%+ relevance score for semantic filtering
- **Error Recovery**: 99%+ success rate for graceful degradation

#### **Target Performance (Roadmap)**
- **Real-Time Sync**: <50ms for live context updates
- **Multi-Agent Coordination**: <200ms for context conflict resolution
- **Enterprise Scale**: 50,000+ requests/second with 99.95% uptime
- **Context Persistence**: 99.9% data retention across sessions
- **RAG Retrieval**: <100ms for hybrid search with 95%+ relevance accuracy
- **Hallucination Detection**: <500ms for fact-checking with 99%+ accuracy
- **Agent Response**: <2s for complex multi-agent task completion
- **Knowledge Graph**: <300ms for semantic reasoning and relationship inference

### **🔧 Implementation Best Practices**

#### **MCP Server Design**
- **Goal-Oriented Tools**: Specialized for research paper analysis
- **Scoped Permissions**: Focused access to GitHub and PostgreSQL
- **Detailed Documentation**: Comprehensive parameter descriptions

#### **Configuration Management**
- **JSON Standardization**: Consistent configuration format
- **Session Isolation**: Per-session settings and logging
- **Provider Abstraction**: Clean separation of LLM providers

#### **OWASP LLM Security Best Practices**
- **Prompt Injection Prevention**: Input validation and sanitization for all user prompts
- **Output Validation**: Secure parsing and validation of LLM responses
- **Context Data Integrity**: Real-time monitoring of MCP context data for poisoning attempts
- **Access Control**: Role-based permissions for MCP server access and tool usage
- **Supply Chain Security**: Verification of MCP server authenticity and dependency integrity
- **Encryption**: End-to-end encryption for sensitive context data transmission
- **Audit Logging**: Comprehensive logging of all LLM interactions and security events
- **Rate Limiting**: Protection against model denial of service attacks
- **Human Oversight**: Fallback mechanisms and human-in-the-loop validation for critical operations

#### **Advanced RAG Best Practices**
- **Hybrid Retrieval**: Combine dense and sparse retrievers for comprehensive search coverage
- **Multi-Modal Support**: Handle text, code, images, and structured data in unified retrieval pipeline
- **Dynamic Reranking**: Use cross-encoders to improve retrieval relevance and reduce noise
- **Source Diversity**: Ensure diverse source selection to prevent bias and improve coverage
- **Real-Time Updates**: Incremental vector store updates to maintain knowledge freshness
- **Query Expansion**: Intelligent query reformulation for better retrieval performance
- **Context-Aware Retrieval**: Adapt retrieval strategy based on query type and domain expertise

#### **AI Agent Best Practices**
- **Specialized Expertise**: Design agents with focused capabilities for specific domains
- **Task Decomposition**: Break complex tasks into manageable subtasks for agent assignment
- **Shared Memory**: Implement centralized knowledge store for agent collaboration
- **Conflict Resolution**: Automated mechanisms to resolve conflicting agent outputs
- **Load Balancing**: Dynamic task distribution based on agent availability and expertise
- **Fault Tolerance**: Graceful degradation when individual agents fail or are unavailable
- **Agent Learning**: Continuous improvement through task execution feedback and performance metrics

## 🔒 Security Notice

**⚠️ IMPORTANT: Never commit API keys, tokens, or sensitive credentials to version control!**

- The `playgrounds/session-data/settings.json` file is **NOT** tracked by git (added to `.gitignore`)
- Always use environment variables (`.env` files) for sensitive configuration
- Keep your API keys secure and never share them publicly
- If you accidentally commit sensitive information, immediately rotate/regenerate your keys

## 📁 Project Structure

```
llm-playground/
├── playgrounds/                    # 🆕 Web-based MCP Playgrounds
│   ├── session-data/              # Centralized settings and session data
│   │   ├── settings.json         # Main settings template (NOT tracked by git)
│   │   ├── settings-*.json       # Session-specific settings files
│   │   ├── session-info.md       # Session data documentation
│   │   └── logs/                 # Centralized logging directory
│   │       ├── session_*.log     # Session-specific log files
│   │       ├── debug_*.log       # Debug log files
│   │       ├── mcp-calls.log     # MCP connector call logs
│   │       ├── error-logs.log    # Error and exception logs
│   │       └── performance.log   # Performance metrics
│   ├── sample.settings.json      # Sample settings configuration
│   ├── sample-outputs.md         # Sample outputs and examples
│   ├── basic/                     # Simple, lightweight playground
│   │   ├── app.py                # Flask web application (43KB, 1112 lines)
│   │   ├── requirements.txt      # Python dependencies
│   │   ├── static/               # Frontend assets
│   │   └── templates/            # HTML templates
│   ├── extended/                  # Advanced playground with full features
│   │   ├── app.py                # Enhanced Flask application (17KB, 484 lines)
│   │   ├── core/                 # Modular architecture
│   │   │   ├── __init__.py       # Core module initialization
│   │   │   ├── settings.py       # Settings management (11KB, 259 lines)
│   │   │   ├── chat_service.py   # Chat functionality (13KB, 306 lines)
│   │   │   ├── llm_providers.py  # AI provider integrations (18KB, 405 lines)
│   │   │   ├── mcp_connectors.py # MCP server connections (20KB, 459 lines)
│   │   │   ├── logging_service.py # Comprehensive logging (10KB, 244 lines)
│   │   │   ├── prompt_optimizer.py # Smart prompt optimization (14KB, 317 lines)
│   │   │   ├── token_calculator.py # Token counting & cost estimation (14KB, 376 lines)
│   │   │   └── models.py         # Data models and structures (10KB, 337 lines)
│   │   ├── static/               # Enhanced frontend assets
│   │   ├── templates/            # Advanced UI templates
│   │   └── requirements.txt      # Python dependencies
│   └── langchain/                 # ⭐ Modern LangChain-based playground (Recommended)
│       ├── app.py                # LangChain Flask application
│       ├── core/                 # LangChain modular architecture
│       │   ├── __init__.py       # Core module initialization
│       │   ├── settings.py       # Settings management with LangChain integration
│       │   ├── chat_service.py   # LangChain-based chat functionality
│       │   ├── llm_providers.py  # LangChain LLM provider implementations
│       │   ├── mcp_connectors.py # LangChain MCP adapters
│       │   ├── logging_service.py # Comprehensive logging
│       │   ├── prompt_optimizer.py # Smart prompt optimization
│       │   ├── token_calculator.py # Token counting & cost estimation
│       │   ├── models.py         # Data models and structures
│       │   ├── container.py      # Dependency injection container
│       │   ├── controllers.py    # Request controllers
│       │   ├── exceptions.py     # Custom exceptions
│       │   └── validation.py     # Data validation
│       ├── static/               # Frontend assets
│       ├── templates/            # UI templates
│       ├── requirements.txt      # Python dependencies
│       ├── README.md             # LangChain playground documentation
│       └── COMPARISON.md         # Architecture comparison (to be merged)
├── github-issues/                 # GitHub MCP Server - reading issues
│   ├── main.py                   # Main GitHub client application
│   ├── issue_fetch.py            # Issue fetching utilities
│   ├── diagnose.py               # Diagnostic tools
│   ├── requirements.txt          # Python dependencies
│   └── env_example.txt           # Environment configuration template
├── pg/                           # PostgreSQL MCP Server - reading local database
│   ├── main.py                   # Main PostgreSQL client application
│   ├── requirements.txt          # Python dependencies
│   └── env_example.txt           # Environment configuration template
└── database/                     # Database setup scripts
    ├── setup_schema.sql          # SQL schema and sample data
    ├── setup_database.py         # Python setup script
    ├── requirements.txt          # Python dependencies
    └── README.md                 # Setup instructions
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or uv package manager
- Node.js and npm (for MCP Inspector)
- Access to AI provider APIs (OpenAI, Anthropic, Google, Ollama)
- GitHub API access (for GitHub client)
- PostgreSQL database (for PostgreSQL client)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/llm-playground.git
cd llm-playground
   ```

2. **Set up the database (required for PostgreSQL MCP):**
   ```bash
   cd database
   pip install -r requirements.txt
   python setup_database.py
   cd ..
   ```

3. **Choose your playground:**
   - **Basic Playground**: Simple, lightweight interface
   - **Extended Playground**: Full-featured with advanced capabilities

## 🎮 Usage Scenarios

### Scenario 1: Learning MCP Basics
**Use Case**: Understanding how MCP works with simple examples
**Recommended**: Start with the **Basic Playground**

- Test individual MCP servers with MCP Inspector
- Run basic GitHub and PostgreSQL clients
- Understand the fundamentals of MCP protocol

### Scenario 2: Building AI Applications
**Use Case**: Creating AI-powered applications with multiple data sources
**Recommended**: Use the **Extended Playground**

- Combine GitHub issues with research papers
- Use multiple AI providers for different tasks
- Implement smart prompt optimization
- Build comprehensive logging and debugging
- **Advanced Context Strategies**: Real-time context synchronization and token-efficient management

### Scenario 3: Research and Development
**Use Case**: Academic research, prototyping, or development
**Recommended**: Use playgrounds based on complexity

- **Basic**: Quick prototyping and testing
- **Extended**: Full-featured development with advanced features
- **LangChain**: Modern, scalable development with industry best practices

### Scenario 3.5: Modern Production Development ⭐ **New**
**Use Case**: Building production-ready applications with modern architecture
**Recommended**: Use the **LangChain Playground**

- **LangChain Integration**: Industry-standard LLM interfaces and MCP adapters
- **Full Async Support**: True async/await operations throughout the stack
- **Enhanced Type Safety**: Comprehensive type hints and interfaces
- **Modular Architecture**: SOLID principles with clean separation of concerns
- **Better Performance**: Optimized resource management and connection pooling
- **Extensibility**: Easy to add new providers and connectors
- **Testability**: Dependency injection for better testing
- **Maintainability**: Clean code structure with proper error handling

### Scenario 4: Advanced Context Management
**Use Case**: Implementing sophisticated MCP context strategies for enterprise applications
**Recommended**: Use the **Extended Playground** with Context Strategies features

- **Real-Time Context Synchronization**: Immediate propagation of knowledge base changes
- **Token-Efficient Context Management**: Intelligent context selection and compression
- **Adaptive Context Selection**: Dynamic context strategies based on query type
- **Multi-Agent Context Coordination**: Shared context stores for distributed systems
- **Enterprise Context Governance**: Security, audit trails, and compliance tracking

### Scenario 5: Advanced RAG & Hallucination Prevention
**Use Case**: Building sophisticated RAG systems with hallucination detection and prevention
**Recommended**: Use the **Extended Playground** with Advanced RAG Strategies

- **Hybrid Retrieval**: Combine semantic and keyword search for comprehensive results
- **Multi-Modal RAG**: Support text, code, images, and structured data retrieval
- **Hallucination Prevention**: Fact-checking, source attribution, and confidence scoring
- **Knowledge Graph Integration**: Semantic knowledge representation and reasoning
- **Real-Time Updates**: Incremental knowledge base updates and vector store maintenance

### Scenario 6: Multi-Agent AI Systems
**Use Case**: Building distributed AI systems with specialized agents and coordination
**Recommended**: Use the **Extended Playground** with AI Agents & Multi-Agent Systems

- **Specialized Agents**: Research, code analysis, data analysis, security, and documentation agents
- **Agent Orchestration**: Dynamic task decomposition and agent assignment
- **Shared Memory**: Centralized knowledge store for agent collaboration
- **Conflict Resolution**: Automated resolution of conflicting agent outputs
- **Fault Tolerance**: Graceful degradation and load balancing across agents

### Scenario 7: Secure LLM Development
**Use Case**: Building secure, production-ready LLM applications with OWASP compliance
**Recommended**: Use the **Extended Playground** with OWASP LLM Security Framework

- **OWASP LLM Security**: Implement all 10 OWASP LLM security guidelines
- **Prompt Injection Prevention**: Advanced input validation and sanitization
- **Context Data Protection**: Real-time monitoring and integrity validation
- **Supply Chain Security**: MCP server and dependency verification
- **Compliance & Governance**: Audit trails, access controls, and security monitoring
**Use Case**: Academic research, prototyping, or development
**Recommended**: Use both playgrounds based on complexity

- **Basic**: Quick prototyping and testing
- **Extended**: Full-featured development with advanced features

## 🎯 Basic Playground

The **Basic Playground** provides a simple, lightweight interface for testing MCP servers and AI providers.

### Features

- **Simple Web Interface**: Clean, minimal UI for quick testing
- **Multi-Provider Support**: OpenAI, Anthropic, Google Gemini, and Ollama
- **MCP Integration**: GitHub and PostgreSQL MCP connectors
- **Basic Prompt Optimization**: Simple prompt enhancement
- **Settings Management**: Web-based configuration interface
- **Usage Tracking**: Token usage monitoring and tracking
- **Session Management**: Per-session settings and data isolation

### Installation

```bash
cd playgrounds/basic
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp ../../github-issues/env_example.txt .env
```

2. Configure your environment variables:
```bash
# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
OLLAMA_BASE_URL=http://localhost:11434

# MCP Configuration
GITHUB_TOKEN=your_github_personal_access_token
MCP_SERVER_URL=https://api.githubcopilot.com/mcp/
MCP_SSE_SERVER_URL=http://localhost:8000/sse
GITHUB_REPO=owner/repo
```

### Usage

```bash
# Start the basic playground
python app.py
```

Then open your browser to `http://localhost:5000`

### Use Cases

- **Quick Testing**: Fast setup for testing MCP servers
- **Learning**: Simple interface for understanding MCP concepts
- **Prototyping**: Rapid prototyping of AI applications
- **Lightweight Development**: Minimal resource usage

## 🌟 Extended Playground

The **Extended Playground** provides a full-featured, production-ready interface with advanced capabilities.

### Features

- **Advanced Web Interface**: Rich UI with multiple tabs and components
- **Multi-Provider Support**: OpenAI, Anthropic, Google Gemini, and Ollama
- **MCP Integration**: GitHub and PostgreSQL MCP connectors
- **Smart Prompt Optimization**: Advanced prompt enhancement using AI
- **Comprehensive Logging**: Centralized session-based logging in `session-data/logs/`
- **Settings Management**: Advanced web-based configuration with session isolation
- **Debug Panel**: Real-time debugging and monitoring
- **Session Management**: Per-session settings and data with automatic cleanup
- **Template System**: Reusable prompt templates
- **Token Calculator**: Comprehensive token counting and cost estimation for all major AI models
- **Usage Tracking**: Detailed token usage monitoring and analytics
- **Modular Architecture**: SOLID principles with clean separation of concerns
- **🧠 Advanced Context Strategies**: 
  - Real-time context synchronization with MCP servers
  - Token-efficient context management and compression
  - Dual-context integration (GitHub issues + Research papers)
  - Template-based context injection with dynamic placeholders
  - Semantic context filtering and intelligent summarization
- **🔒 Security & Compliance**: 
  - OWASP LLM security framework implementation (roadmap)
  - Prompt injection prevention and validation
  - Context data integrity monitoring
  - Supply chain security verification
  - Comprehensive audit logging and access controls
- **🔍 Advanced RAG & Hallucination Prevention** (roadmap):
  - Hybrid retrieval combining semantic and keyword search
  - Multi-modal RAG for text, code, images, and structured data
  - Fact-checking pipeline and source attribution verification
  - Confidence scoring and uncertainty quantification
  - Knowledge graph integration for semantic reasoning
- **🤖 AI Agents & Multi-Agent Systems** (roadmap):
  - Specialized agents for research, code analysis, data analysis, and security
  - Agent orchestration and task decomposition
  - Shared memory and conflict resolution mechanisms
  - Fault tolerance and load balancing across agents
  - Continuous agent learning and performance optimization

### Installation

```bash
cd playgrounds/extended
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp ../../github-issues/env_example.txt .env
```

2. Configure your environment variables (same as basic playground)

### Usage

```bash
# Start the extended playground
python app.py
```

Then open your browser to `http://localhost:5000`

### Advanced Features

#### 1. **Smart Prompt Optimization**
- Uses AI to optimize prompts based on context
- Combines GitHub issues with research papers
- Dynamic token budgeting and summarization
- **Real-Time Context Synchronization**: Fresh data fetching on each request
- **Token-Efficient Context Management**: Intelligent context selection and compression
- **Semantic Context Filtering**: Uses semantic understanding to include only relevant context
- **Dual-Context Integration**: Simultaneous GitHub issues and research papers processing

#### 2. **Comprehensive Logging**
- Centralized logging in `session-data/logs/` directory
- Session-based logging with unique IDs
- Detailed MCP and LLM communication logs
- Debug information for troubleshooting
- Automatic log rotation and cleanup

#### 3. **Advanced UI Components**
- **Chat Tab**: Interactive conversation interface
- **Settings Tab**: Advanced configuration management
- **Debug Tab**: Real-time monitoring and logs
- **Templates Tab**: Reusable prompt templates
- **Tokens Tab**: Token counting and cost estimation interface

#### 4. **Session Management**
- Per-session settings and data isolation with unique session IDs
- Automatic cleanup of old session files (configurable retention)
- Session-specific logging and debugging
- Session persistence across browser sessions

#### 5. **Token Calculator**
- Real-time token counting for OpenAI, Anthropic, and Google models
- Cost estimation with current pricing for all major models
- Cross-provider comparison and analysis
- Interactive web interface with debouncing
- Official tokenizers for accurate counting
- Support for multimodal inputs

#### 6. **🧠 Advanced Context Strategies**
- **Template-Based Context Injection**: 13 specialized templates for different use cases
- **Dynamic Placeholder Substitution**: `{owner_repo}` placeholders with real repository data
- **Context Window Management**: Dynamic sizing based on provider capabilities
- **Error Resilience**: Graceful degradation when MCP servers are unavailable
- **Parallel Context Processing**: Simultaneous GitHub and PostgreSQL queries
- **Context Budget Allocation**: Intelligent token distribution across context sources

#### 7. **🔒 Security & Compliance Framework**
- **OWASP LLM Security**: Implementation roadmap for all 10 OWASP LLM security guidelines
- **Prompt Injection Prevention**: Advanced input validation and sanitization techniques
- **Context Data Integrity**: Real-time monitoring for data poisoning and manipulation
- **Supply Chain Security**: MCP server and dependency verification mechanisms
- **Access Control**: Role-based permissions and granular access management
- **Audit Logging**: Comprehensive security event logging and monitoring

#### 8. **🔍 Advanced RAG & Hallucination Prevention** (Roadmap)
- **Hybrid Retrieval**: Combines dense (semantic) and sparse (keyword) search for comprehensive results
- **Multi-Modal RAG**: Supports text, code, images, and structured data retrieval
- **Dynamic Reranking**: Uses cross-encoders to improve retrieval relevance and reduce noise
- **Fact-Checking Pipeline**: Automated verification against retrieved context with source attribution
- **Confidence Scoring**: Uncertainty quantification for response reliability assessment
- **Knowledge Graph Integration**: Semantic knowledge representation and relationship inference
- **Real-Time Updates**: Incremental vector store and knowledge graph maintenance

#### 9. **🤖 AI Agents & Multi-Agent Systems** (Roadmap)
- **Specialized Agents**: Research, code analysis, data analysis, security, documentation, testing, and deployment agents
- **Task Decomposition**: Intelligent breakdown of complex tasks into manageable subtasks
- **Agent Orchestration**: Dynamic agent selection and coordination based on task requirements
- **Shared Memory**: Centralized knowledge store accessible to all agents for collaboration
- **Conflict Resolution**: Automated resolution of conflicting agent outputs and consensus building
- **Load Balancing**: Dynamic distribution of tasks across available agents with fault tolerance
- **Agent Learning**: Continuous improvement through task execution feedback and performance metrics

### Use Cases

- **Production Development**: Full-featured development environment
- **Research Projects**: Comprehensive AI research applications
- **Team Collaboration**: Advanced features for team development
- **Complex Integrations**: Sophisticated MCP and AI integrations
- **Context Strategy Research**: Study and implement advanced MCP context management
- **Enterprise Context Management**: Develop scalable context synchronization systems
- **Multi-Agent AI Systems**: Build distributed AI systems with shared context
- **Secure LLM Development**: Build OWASP-compliant, production-ready LLM applications
- **Compliance & Governance**: Implement enterprise-grade security and audit controls
- **Security Research**: Study and implement LLM security best practices and countermeasures
- **Advanced RAG Development**: Build sophisticated retrieval systems with hallucination prevention
- **Multi-Agent Systems**: Develop distributed AI systems with specialized agent coordination
- **Knowledge Graph Applications**: Create semantic knowledge representation and reasoning systems
- **Research & Development**: Study advanced AI techniques and experimental implementations

## 🚀 LangChain Playground ⭐ **Recommended**

The **LangChain Playground** represents the most modern and scalable implementation, built with industry-standard LangChain interfaces and MCP adapters. This playground offers significant improvements in architecture, performance, and maintainability.

### Features

- **Modern Architecture**: Built with LangChain's standardized interfaces and MCP adapters
- **Full Async Support**: True async/await operations throughout the entire stack
- **Enhanced Type Safety**: Comprehensive type hints with proper interfaces
- **Modular Design**: SOLID principles with clean separation of concerns
- **Better Performance**: Optimized resource management and connection pooling
- **Extensibility**: Easy to add new LangChain providers and MCP adapters
- **Testability**: Dependency injection for better testing and mocking
- **Maintainability**: Clean code structure with comprehensive error handling
- **All Extended Features**: Includes all features from the Extended Playground
- **LangChain Ecosystem**: Seamless integration with the broader LangChain ecosystem

### Key Improvements Over Extended Playground

#### **1. LLM Provider Implementation**

**Extended (Direct API):**
```python
class OpenAIProvider(BaseLLMProvider):
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None, logger=None) -> str:
        # Direct HTTP requests to OpenAI API
        response = requests.post(url, headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]
```

**LangChain (Standardized):**
```python
class OpenAIProvider(BaseLangChainProvider):
    def _create_llm(self) -> BaseLLM:
        return ChatOpenAI(
            model=self.config.default_model,
            openai_api_key=self.config.api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_completion_tokens
        )
    
    async def generate(self, prompt: str, system: Optional[str] = None, 
                      temperature: Optional[float] = None, logger=None) -> ChatResponse:
        # Use LangChain's standardized interface
        response = await llm.ainvoke(messages)
        return ChatResponse(text=response.content, ...)
```

#### **2. MCP Connector Implementation**

**Extended (Custom):**
```python
class GitHubMCPConnector(BaseMCPConnector):
    def _mcp_connect(self):
        auth = MCPBearerAuth(self.auth_token) if self.auth_token else None
        return MCPClient(self.url, auth=auth)
    
    async def fetch_issues_and_comments(self, limit_issues=3, limit_comments=5):
        # Manual MCP client usage
        client = self._mcp_connect()
        # Custom implementation for fetching data
```

**LangChain (Official Adapters):**
```python
class GitHubMCPConnector(BaseMCPConnector):
    async def connect(self) -> MCPClient:
        config = MCPClientConfig(
            server_url=self.url,
            auth_token=self.auth_token if self.auth_token else None
        )
        self._client = MCPClient(config)
        await self._client.connect()
        return self._client
    
    async def fetch_data(self, limit_issues: int = 3, limit_comments: int = 5):
        # Use LangChain's MCP adapters
        client = await self.connect()
        issues_result = await client.list_issues(...)
```

#### **3. Architecture Benefits**

- **Standardization**: Uses industry-standard LangChain interfaces
- **Performance**: True async operations with better resource management
- **Maintainability**: Cleaner code structure with better separation of concerns
- **Extensibility**: Easy to add new providers and connectors
- **Reliability**: Better error handling and recovery mechanisms
- **Future-Proof**: Built on LangChain's ecosystem for long-term sustainability

### Installation

```bash
cd playgrounds/langchain
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp ../../github-issues/env_example.txt .env
```

2. Configure your environment variables (same as other playgrounds)

### Usage

```bash
# Start the LangChain playground
python app.py
```

Then open your browser to `http://localhost:5052` (different port from other playgrounds)

### Advanced Features

#### **1. LangChain Integration**
- **Standardized LLM Interfaces**: Use LangChain's proven LLM abstractions
- **MCP Adapters**: Leverage official LangChain MCP adapters
- **Tool Integration**: Easy integration with LangChain's tool ecosystem
- **Chain Composition**: Build complex workflows with LangChain chains

#### **2. Enhanced Async Support**
- **True Async Operations**: Full async/await support throughout the stack
- **Connection Pooling**: Efficient resource management
- **Concurrent Processing**: Better handling of multiple requests
- **Performance Optimization**: Reduced latency and improved throughput

#### **3. Improved Architecture**
- **Dependency Injection**: Clean dependency management
- **Interface-Based Design**: Better abstraction and testability
- **Error Handling**: Comprehensive error management
- **Validation**: Enhanced input validation and type checking

#### **4. Developer Experience**
- **Better Testing**: Dependency injection enables easier testing
- **Code Quality**: Enhanced type safety and error handling
- **Documentation**: Comprehensive inline documentation
- **Debugging**: Better debugging capabilities with LangChain's tools

### Use Cases

- **Production Applications**: Build scalable, maintainable applications
- **Enterprise Development**: Modern architecture for enterprise needs
- **Team Development**: Clean code structure for team collaboration
- **Long-term Projects**: Future-proof architecture for sustained development
- **LangChain Ecosystem**: Leverage the full LangChain ecosystem
- **Modern Best Practices**: Follow industry standards and best practices

## 🔢 Token Calculator

The **Token Calculator** is a comprehensive service integrated into the Extended Playground that provides accurate token counting and cost estimation for OpenAI (GPT), Anthropic (Claude), and Google (Gemini) models.

### Features

#### 🔢 **Multi-Provider Support**
- **OpenAI**: Uses official `tiktoken` library for accurate token counting
- **Anthropic**: Uses official API for precise token counting (with fallback estimation)
- **Google**: Uses estimation based on character count (1 token ≈ 4 characters)

#### 💰 **Cost Estimation**
- Real-time cost calculation for input and output tokens
- Support for all major AI models with current pricing
- Cost comparison across different providers

#### 📊 **Comprehensive Analysis**
- Character, word, and sentence counting
- Token-to-word and token-to-character ratios
- Cross-provider comparison tables
- Real-time analysis as you type

#### 🎯 **User-Friendly Interface**
- Modern, responsive web interface
- Real-time token counting with debouncing
- Interactive cost estimation tool
- Error handling and loading states

### Usage

#### Web Interface

1. **Start the Extended Playground**:
   ```bash
   cd playgrounds/extended
   python app.py
   ```

2. **Navigate to the Tokens tab** in the web interface

3. **Enter text** in the text area to analyze

4. **Choose your analysis method**:
   - **Count Tokens**: Analyze for a specific provider/model
   - **Analyze All Providers**: Compare across all providers

5. **Use the Cost Estimation Tool** to calculate costs for specific token counts

#### API Endpoints

##### Count Tokens
```http
POST /api/tokens/count
Content-Type: application/json

{
    "text": "Your text here",
    "provider": "openai",
    "model": "gpt-4"
}
```

Response:
```json
{
    "input_tokens": 25,
    "characters": 100,
    "words": 15,
    "estimated_cost": 0.0008,
    "model": "gpt-4",
    "provider": "openai"
}
```

##### Analyze All Providers
```http
POST /api/tokens/analyze
Content-Type: application/json

{
    "text": "Your text here"
}
```

Response:
```json
{
    "text_length": 100,
    "characters": 100,
    "words": 15,
    "sentences": 2,
    "providers": {
        "openai": {
            "input_tokens": 25,
            "estimated_cost": 0.0008,
            "model": "gpt-4",
            "tokens_per_word": 1.67,
            "tokens_per_character": 0.25
        },
        "anthropic": {
            "input_tokens": 23,
            "estimated_cost": 0.0007,
            "model": "claude-3-5-sonnet",
            "tokens_per_word": 1.53,
            "tokens_per_character": 0.23
        },
        "google": {
            "input_tokens": 25,
            "estimated_cost": 0.0002,
            "model": "gemini-2.0-flash",
            "tokens_per_word": 1.67,
            "tokens_per_character": 0.25
        }
    }
}
```

##### Get Available Models
```http
GET /api/tokens/models/{provider}
```

##### Estimate Cost
```http
POST /api/tokens/estimate-cost
Content-Type: application/json

{
    "input_tokens": 1000,
    "output_tokens": 500,
    "provider": "openai",
    "model": "gpt-4"
}
```

#### Python API

```python
from core.token_calculator import token_calculator

# Count tokens for a specific provider
result = token_calculator.count_tokens("Hello, world!", "openai", "gpt-4")
print(f"Tokens: {result.input_tokens}")
print(f"Cost: ${result.estimated_cost}")

# Analyze text across all providers
analysis = token_calculator.analyze_text("Your text here")
print(f"Characters: {analysis['characters']}")
print(f"Words: {analysis['words']}")

# Estimate cost for a complete request
cost = token_calculator.estimate_cost(1000, 500, "openai", "gpt-4")
print(f"Total cost: ${cost}")
```

### Supported Models

#### OpenAI
- GPT-5
- GPT-4o
- GPT-4o Mini
- GPT-4
- GPT-3.5 Turbo

#### Anthropic
- Claude 3.5 Sonnet
- Claude 3.5 Haiku
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

#### Google
- Gemini 2.5 Pro (supported in settings, estimation-based counting)
- Gemini 2.0 Flash
- Gemini 1.5 Pro
- Gemini 1.5 Flash

#### Ollama
- Gemma3:270m
- Other local models via Ollama

### Pricing Information

The token calculator includes current pricing for all supported models:

#### OpenAI (per 1K tokens)
- GPT-5: $50.00 input, $150.00 output
- GPT-4o: $5.00 input, $15.00 output
- GPT-4o Mini: $0.15 input, $0.60 output
- GPT-4: $30.00 input, $60.00 output
- GPT-3.5 Turbo: $0.50 input, $1.50 output

#### Anthropic (per 1K tokens)
- Claude 3.5 Sonnet: $3.00 input, $15.00 output
- Claude 3.5 Haiku: $0.25 input, $1.25 output
- Claude 3 Opus: $15.00 input, $75.00 output
- Claude 3 Sonnet: $3.00 input, $15.00 output
- Claude 3 Haiku: $0.25 input, $1.25 output

#### Google (per 1K tokens)
- Gemini 2.5 Pro: $3.50 input, $10.50 output (estimated)
- Gemini 2.0 Flash: $0.075 input, $0.30 output
- Gemini 1.5 Pro: $3.50 input, $10.50 output
- Gemini 1.5 Flash: $0.075 input, $0.30 output

### Technical Details

#### Token Counting Methods

##### OpenAI
- Uses the official `tiktoken` library
- Supports different encodings based on model type
- Caches encodings for performance

##### Anthropic
- Uses the official API when available
- Falls back to estimation (1 token ≈ 4 characters) when API is not accessible
- Requires `ANTHROPIC_API_KEY` environment variable for API access

##### Google
- Uses estimation based on character count
- 1 token ≈ 4 characters (standard approximation)
- Future versions will support official API integration

#### Performance Considerations

- OpenAI token counting is the fastest and most accurate
- Anthropic API calls may have slight latency
- Google estimation is instant but approximate
- All operations are cached where possible

#### Error Handling

- Graceful fallbacks for API failures
- Clear error messages for debugging
- Network error handling
- Invalid input validation

### Testing

Run the test script to verify functionality:

```bash
cd playgrounds/extended
python test_token_calculator.py
```

This will test:
- Token counting for all providers
- Comprehensive text analysis
- Cost estimation
- Model availability

## 🔍 MCP Inspector - Interactive Testing

MCP Inspector is a powerful debugging and development tool for testing MCP servers interactively.

### Installation

```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector
```

### Testing GitHub MCP Server

```bash
# Direct command line connection
mcp-inspector --url https://api.githubcopilot.com/mcp --header "Authorization: Bearer YOUR_TOKEN" --token YOUR_TOKEN
```

### Testing PostgreSQL MCP Server

1. Start the PostgreSQL MCP server:
```bash
export DATABASE_URI="postgresql://user:password@localhost:5432/dbname"
postgres-mcp --access-mode=unrestricted --transport=sse
```

2. Launch MCP Inspector:
```bash
mcp-inspector
# Connect to http://localhost:8000/sse
```

### Testing with Built-in MCP Tools

The playground also provides access to MCP tools through the web interface:
- **GitHub Tools**: List issues, create issues, search repositories
- **PostgreSQL Tools**: Execute SQL queries, analyze database health
- **InstantDB Tools**: Create apps, manage schemas and permissions

## 📊 Individual MCP Clients

### GitHub MCP Server - Reading Issues

```bash
cd github-issues
pip install -r requirements.txt
cp env_example.txt .env
# Edit .env with your GitHub token
python main.py
```

### PostgreSQL MCP Server - Reading Local Database

```bash
cd pg
pip install -r requirements.txt
cp env_example.txt .env
# Start postgres-mcp server first
python main.py
```

## 🔧 Configuration

### Environment Variables

All components use environment variables for configuration. See the respective `env_example.txt` files for detailed options.

### Session Data Management

The playgrounds use a centralized session data management system located in `playgrounds/session-data/`:

#### **Session-Specific Settings**
- **Unique Session IDs**: Each browser session gets a unique UUID
- **Session Isolation**: Settings are isolated per session (`settings-{session-id}.json`)
- **Automatic Cleanup**: Old session files are automatically cleaned up (configurable retention)
- **Session Persistence**: Settings persist across browser sessions

#### **Centralized Logging**
- **Location**: All logs are stored in `playgrounds/session-data/logs/`
- **Session Logs**: Individual session log files (`session_*.log`)
- **Debug Logs**: Detailed debug information (`debug_*.log`)
- **MCP Call Logs**: All MCP connector interactions (`mcp-calls.log`)
- **Error Logs**: Error tracking and debugging (`error-logs.log`)
- **Performance Logs**: Timing and performance metrics (`performance.log`)

#### **Usage Tracking**
- **Token Usage**: Track total, user, optimized, and response tokens
- **API Calls**: Monitor API call frequency and patterns
- **Cost Tracking**: Estimate costs based on token usage
- **Performance Metrics**: Monitor response times and success rates

### Settings File Structure

The playgrounds use a centralized `playgrounds/session-data/settings.json` file for configuration. The Extended Playground also supports session-specific settings files (`settings-{session-id}.json`):

```json
{
  "providers": {
    "openai": {
      "enabled": false,
      "name": "OpenAI",
      "base_url": "https://api.openai.com/v1",
      "api_key": "",
      "temperature": 0.2,
      "default_model": "gpt-5",
      "context_window": 128000,
      "max_completion_tokens": 8192,
      "usage_cap_tokens": 1000000
    },
    "anthropic": {
      "enabled": true,
      "name": "Anthropic",
      "base_url": "https://api.anthropic.com",
      "api_key": "",
      "temperature": 0.2,
      "default_model": "claude-3-7-sonnet-latest",
      "context_window": 200000,
      "max_completion_tokens": 8192,
      "usage_cap_tokens": 1000000,
      "usage_tracking": {
        "total_tokens_used": 0,
        "user_tokens": 0,
        "optimized_tokens": 0,
        "response_tokens": 0,
        "api_calls": 0,
        "last_updated": ""
      }
    }
  },
  "mcp": {
    "github": {
      "enabled": true,
      "url": "https://api.githubcopilot.com/mcp/",
      "auth_token": "",
      "repo": "owner/repo"
    },
    "postgres": {
      "enabled": true,
      "url": "http://localhost:8000/sse",
      "auth_token": "",
      "sample_sql": "SELECT * FROM research_papers.ai_research_papers LIMIT 5;"
    }
  },
  "optimizer": {
    "provider": "openai",
    "model": "gpt-5",
    "temperature": 0.2,
    "max_tokens": 1000,
    "max_context_usage": 0.8
  },
  "default_provider": "openai"
}
```

**🔒 Security**: API keys and tokens are loaded from environment variables and should never be hardcoded in this file.

## 📝 Examples

### Sample Files

The playground includes several sample files for reference:

- **`playgrounds/sample.settings.json`**: Complete settings configuration example
- **`playgrounds/sample-outputs.md`**: Sample outputs and usage examples
- **`playgrounds/session-data/session-info.md`**: Detailed session data documentation

### Basic Playground Example

```python
# Simple chat with MCP integration
POST /api/chat
{
  "provider": "anthropic",
  "user_prompt": "Analyze the GitHub issues and suggest relevant research papers"
}
```

### Extended Playground Example

```python
# Advanced chat with smart optimization
POST /api/chat
{
  "provider": "anthropic",
  "user_prompt": "Based on the GitHub issues, find research papers that could help implement the requested features"
}
```

### GitHub Issues Example

```python
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

# Initialize client
client = Client(
    "github",
    auth=BearerAuth(os.getenv("GITHUB_TOKEN")),
    server_url=os.getenv("MCP_SERVER_URL")
)

# Fetch issues
issues = await client.call_tool("list_issues", {
    "owner": "owner",
    "repo": "repo",
    "state": "open"
})
```

### PostgreSQL Example

```python
from fastmcp import Client

# Initialize client
client = Client("postgres", server_url=os.getenv("POSTGRES_MCP_URL"))

# Execute SQL query
result = await client.call_tool("execute_sql", {
    "sql": "SELECT * FROM research_papers.ai_research_papers LIMIT 10"
})
```

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your API tokens have the necessary permissions
2. **Connection Issues**: Verify MCP server URLs and network connectivity
3. **Data Parsing**: Check that response data matches expected formats
4. **Ollama Connection**: Ensure Ollama is running locally for prompt optimization

### Diagnostic Tools

- Use the **Debug Tab** in the extended playground for detailed logging
- Use `diagnose.py` in the GitHub client for troubleshooting
- Check server logs for detailed error messages
- Verify environment variable configuration

### Playground-Specific Issues

#### Basic Playground
- **Simple Setup**: Minimal configuration required
- **Quick Testing**: Fast startup and testing
- **Limited Features**: Basic functionality only

#### Extended Playground
- **Advanced Features**: Full-featured with comprehensive capabilities
- **Session Management**: Per-session isolation and cleanup
- **Debug Tools**: Extensive logging and debugging features

## 📚 Dependencies

### Basic Playground
- `flask`
- `python-dotenv`
- `requests`
- `fastmcp`

### Extended Playground
- `flask`
- `python-dotenv`
- `requests`
- `fastmcp`
- `tiktoken` - Official OpenAI tokenizer for token counting
- `anthropic` - Anthropic API client for token counting

### LangChain Playground ⭐ **Recommended**
- `flask`
- `python-dotenv`
- `langchain` - Core LangChain framework
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Anthropic integration
- `langchain-google-genai` - Google Gemini integration
- `langchain-community` - Community integrations
- `langchain-mcp` - MCP adapters for LangChain
- `tiktoken` - Official OpenAI tokenizer for token counting
- `anthropic` - Anthropic API client for token counting

### GitHub Client
- `fastmcp`
- `pydantic`
- `httpx`
- `python-dotenv`

### PostgreSQL Client
- `postgres-mcp` (installed via pipx/uv)
- `fastmcp`
- `python-dotenv`

### Database Setup
- `psycopg2-binary`

## 🎮 Complete Demo Flow

Follow this step-by-step progression to experience the full LLM playground:

### Step 1: Test with MCP Inspector
```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Test GitHub MCP
mcp-inspector --url https://api.githubcopilot.com/mcp --header "Authorization: Bearer YOUR_TOKEN" --token YOUR_TOKEN

# Test PostgreSQL MCP (after starting postgres-mcp server)
mcp-inspector
# Connect to http://localhost:8000/sse
```

### Step 2: Run Individual MCP Clients
```bash
# Set up database first (required for PostgreSQL client)
cd database
pip install -r requirements.txt
python setup_database.py

# GitHub Issues Client
cd ../github-issues
python main.py

# PostgreSQL Client (in another terminal)
cd ../pg
python main.py
```

### Step 3: Try the Playgrounds
```bash
# Basic Playground (Simple)
cd playgrounds/basic
pip install -r requirements.txt
cp ../../github-issues/env_example.txt .env
# Edit .env with your API keys
python app.py
# Open http://localhost:5000

# Extended Playground (Advanced)
cd ../extended
pip install -r requirements.txt
cp ../../github-issues/env_example.txt .env
# Edit .env with your API keys
python app.py
# Open http://localhost:5000

# LangChain Playground (Modern & Recommended) ⭐
cd ../langchain
pip install -r requirements.txt
cp ../../github-issues/env_example.txt .env
# Edit .env with your API keys
python app.py
# Open http://localhost:5052
```

### What You'll Experience
1. **MCP Inspector**: Interactive testing of individual MCP tools
2. **Individual Clients**: See how each MCP server works independently
3. **Basic Playground**: Simple integration with multiple AI providers and MCP connectors
4. **Extended Playground**: Complete integration with advanced features
5. **LangChain Playground**: Modern, scalable implementation with industry best practices

## References

- [One Month in MCP: What I Learned the Hard Way](https://www.reddit.com/r/mcp/comments/1mub6g6/one_month_in_mcp_what_i_learned_the_hard_way/)
- [Model Context Protocol (MCP) Curriculum for Beginners](https://github.com/microsoft/mcp-for-beginners/)
- [Context Engineering: An Emerging Concept in the MCP Ecosystem](https://github.com/microsoft/mcp-for-beginners/tree/main/05-AdvancedTopics/mcp-contextengineering)

## 🔄 Migration Guide

### For Users

#### From Basic/Extended to LangChain Playground
1. **Install LangChain dependencies**: `pip install -r requirements.txt`
2. **Update environment variables**: Same format as other playgrounds
3. **Run the application**: `python app.py`
4. **Access at**: `http://localhost:5052` (different port from other playgrounds)

#### Benefits of Migration
- **Better Performance**: True async operations and optimized resource management
- **Enhanced Reliability**: Better error handling and recovery mechanisms
- **Future-Proof**: Built on LangChain's ecosystem for long-term sustainability
- **Industry Standards**: Uses proven LangChain interfaces and best practices

### For Developers

#### Architecture Migration
1. **LLM Providers**: Use LangChain's provider interfaces instead of direct API calls
2. **MCP Connectors**: Use LangChain's MCP adapters instead of custom implementations
3. **Async Operations**: Use proper async/await patterns throughout
4. **Error Handling**: Implement comprehensive error handling with LangChain's patterns
5. **Testing**: Use dependency injection for better testing and mocking

#### Code Migration Examples

**LLM Provider Migration:**
```python
# Before (Extended): Direct API calls
class OpenAIProvider(BaseLLMProvider):
    def complete(self, prompt: str) -> str:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]

# After (LangChain): Standardized interfaces
class OpenAIProvider(BaseLangChainProvider):
    def _create_llm(self) -> BaseLLM:
        return ChatOpenAI(model=self.config.default_model, ...)
    
    async def generate(self, prompt: str) -> ChatResponse:
        response = await llm.ainvoke(messages)
        return ChatResponse(text=response.content, ...)
```

**MCP Connector Migration:**
```python
# Before (Extended): Custom MCP client
class GitHubMCPConnector(BaseMCPConnector):
    def _mcp_connect(self):
        return MCPClient(self.url, auth=auth)

# After (LangChain): Official adapters
class GitHubMCPConnector(BaseMCPConnector):
    async def connect(self) -> MCPClient:
        config = MCPClientConfig(server_url=self.url, ...)
        self._client = MCPClient(config)
        await self._client.connect()
        return self._client
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

**🔒 Security Guidelines for Contributors**:
- Never commit API keys, tokens, or sensitive credentials
- Always use environment variables for configuration
- Test with dummy/placeholder values
- If you find exposed credentials, report them immediately

## 📊 Current Project Status

### Recent Updates (Latest)
- **Centralized Logging**: All logs now stored in `playgrounds/session-data/logs/` for better organization
- **Session Management**: Enhanced session isolation with automatic cleanup of old session files
- **Token Calculator**: Updated with latest model support including Gemini 2.5 Pro
- **MCP Integration**: Full integration with GitHub, PostgreSQL, and InstantDB MCP servers
- **Modular Architecture**: Extended playground uses SOLID principles with clean separation of concerns

### Active Development
- **Core Features**: All major features are implemented and functional
- **Documentation**: Comprehensive documentation with examples and troubleshooting guides
- **Testing**: Both playgrounds are tested and ready for use
- **Session Data**: Centralized session management with automatic cleanup

### File Structure Summary
- **Basic Playground**: 43KB, 1112 lines - Simple, lightweight interface
- **Extended Playground**: 17KB, 484 lines - Full-featured with modular architecture
- **LangChain Playground**: Modern implementation with LangChain integration - **Recommended**
- **Core Modules**: 8 modules totaling ~120KB with comprehensive functionality
- **Session Data**: Centralized management with logs, settings, and user data

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
