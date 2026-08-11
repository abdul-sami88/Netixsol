# Week 5 Day 2 — Raw Python vs. LangChain: Write-Up

Raw Python vs. LangChain Agent

In the raw-Python implementation, the agent loop, tool registration, tool execution, message management, and response parsing had to be implemented manually. LangChain abstracts many of these responsibilities through standardized model wrappers, @tool, agent constructors, AgentExecutor, message-history utilities, and structured-output mechanisms.

The biggest advantage of LangChain was reducing the amount of infrastructure code required to build a tool-using agent. Tool schemas and execution, agent iteration, prompt composition, and integration between components became considerably easier. LCEL also provided a clean way to compose prompts, models, and parsers into reusable pipelines.

However, the framework introduced abstraction layers that sometimes hide what is actually happening. Instead of directly seeing API requests, message construction, tool-call parsing, and the agent loop, these operations are handled internally by LangChain. This makes development faster but can make debugging more difficult when something goes wrong.

The execution trace showed that the fundamental agent loop remained similar to the raw-Python implementation: the model decides on an action, a tool is executed, its result is returned to the model, and the model continues until it produces a final answer. The major difference is that LangChain manages much of this orchestration automatically.

## Annotated reasoning trace (condensed)

```python
REASON:  model determines it needs weather data for two cities before comparing
ACT:     Invoking: weather_lookup(city="Lahore")
OBSERVE: {"success": true, "city": "Lahore", "temperature": 32, "condition": "Sunny"}
REASON:  model still needs Islamabad's data
ACT:     Invoking: weather_lookup(city="Islamabad")
OBSERVE: {"success": true, "city": "Islamabad", "temperature": 28, "condition": "Partly cloudy"}
REASON:  both facts now in context; computes 32 - 28 = 4
FINAL:   "Lahore is warmer than Islamabad by 4 degrees."
```

Overall, LangChain is most useful when an application contains multiple interconnected LLM components, tools, memory, retrieval, structured outputs, or complex orchestration. For a very small LLM application, the framework may introduce unnecessary complexity, and direct provider APIs can sometimes be easier to understand and debug.
