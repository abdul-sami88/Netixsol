# Task 1 — Agent Concepts & Mental Model

## Agent vs Chatbot vs Workflow

### Chatbot

A chatbot primarily interacts with users by receiving a message and generating a response.

```text
User → LLM → Response
```

For example, asking an LLM to explain Python recursion is a simple chatbot interaction.

### Workflow

A workflow follows a predefined sequence of steps. The developer determines what happens and in what order.

```text
Input → Step 1 → Step 2 → Step 3 → Output
```

For example, a data pipeline that loads a CSV, cleans it, calculates statistics, and saves the result is a workflow.

### Agent

An agent uses an LLM to decide what action should be taken next to accomplish a goal. It can use tools, observe their results, and perform multiple actions when necessary.

```text
Goal → LLM → Tool → Result → LLM → Tool → Result → Final Answer
```

### Simple Comparison

| System   | Main Idea                           |
| -------- | ----------------------------------- |
| Chatbot  | Generates responses                 |
| Workflow | Follows predefined steps            |
| Agent    | Dynamically decides what to do next |

---

## What Makes a System Agentic?

A system becomes more agentic when it has the ability to:

* **Autonomy:** Decide what action to take next instead of following every step explicitly programmed by the developer.
* **Tool use:** Interact with external tools such as calculators, APIs, databases, or file systems.
* **Multi-step planning:** Perform several actions to accomplish a larger goal.
* **Self-correction:** Use the results or errors from previous actions to adjust its next action.

For example, if a user asks:

> "Which is warmer, Lahore or Islamabad?"

An agent can use a weather tool to check both cities, compare the results, and then provide an answer.

---

## ReAct Pattern

ReAct stands for **Reason + Act**. It describes a common agent loop where the model decides what to do, performs an action using a tool, observes the result, and then decides what to do next.

```text
             User Goal
                 ↓
               LLM
              Reason
                 ↓
          Tool needed?
           /        \
         Yes         No
          ↓           ↓
        Tool      Final Answer
          ↓
       Result
       Observe
          ↓
         LLM
          ↓
        Repeat
```

### Pseudocode

```python
send request to LLM

while task is not finished:

    response = LLM()

    if response requests a tool:

        execute the tool

        return the result to the LLM

    else:

        return final answer
```

The loop allows the agent to perform multiple actions until it has enough information to complete the task.

---

## When Is an Agent Overkill?

An agent is unnecessary when a problem can be solved easily with a simple prompt, script, or deterministic workflow.

For example, converting kilometers to miles does not require an agent:

```python
miles = kilometers * 0.621371
```

Using an agent for such a simple task would add unnecessary complexity, API calls, latency, cost, and potential failure points.

**A good rule is: use an agent when dynamic decision-making and multiple actions provide real value; otherwise, prefer simpler solutions.**
