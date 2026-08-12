# LangGraph Core Building Blocks

LangGraph is a library for building stateful, multi-actor applications with Large Language Models (LLMs), built on top of LangChain. It extends the LangChain Expression Language (LCEL) with the ability to coordinate multiple chains (or actors) across multiple steps of computation in a cyclic manner.

At its heart, LangGraph models application logic as a **state machine** represented by a directed graph. Below are the fundamental building blocks that make this possible.

---

## 1. The Shared `State` Object

The core of any LangGraph application is the **State**. This is a shared data structure that is passed around to every node in the graph.

* **Definition**: It is typically defined using a Python `TypedDict` or a Pydantic model. It outlines the variables that the graph will track.
* **Updates**: When a node executes, it does not overwrite the entire state. Instead, it returns an *update* to the state.  
* **Reducers**: You can specify how these updates are applied by defining "reducers" in your state schema. For example, a common pattern is to append new messages to an existing list of messages rather than overwriting the list.

## 2. `StateGraph`

`StateGraph` is the central graph object that orchestrates the execution flow.

* **Initialization**: You initialize a `StateGraph` by passing it your defined `State` schema.
* **Compilation**: Once you have added all your nodes and edges to the `StateGraph`, you call `.compile()` on it. This transforms the graph definition into an executable `Runnable` (similar to standard LangChain runnables) that you can invoke, stream, or batch.

## 3. Nodes

Nodes represent the actual compute units or "actors" in your graph.

* **Functionality**: A node is simply a Python function or a LangChain `Runnable`. It takes the current `State` as input, performs some logic (like calling an LLM, querying a database, or running a tool), and returns a dictionary containing updates to the state.
* **Adding Nodes**: You add nodes to the graph using the `graph.add_node(name, action)` method, giving each node a unique string identifier.
* **Special Nodes**: The graph has implicit `START` and `END` nodes to define where execution begins and terminates.

## 4. Edges

Edges connect nodes and define the deterministic flow of execution from one node to the next.

* **Standard Edges**: Added via `graph.add_edge(start_node, end_node)`. This guarantees that whenever `start_node` finishes executing, `end_node` will *always* be executed next.
* **Starting the Graph**: You typically add an edge from the `START` node to your first operational node to kick off the flow.

## 5. Conditional Edges

Unlike standard edges, **Conditional Edges** allow for dynamic routing based on the current state of the application.

* **Routing Logic**: You define a "router" function that evaluates the current `State` and returns the name of the next node to execute.
* **Implementation**: Added via `graph.add_conditional_edges(start_node, router_function, mapping)`.
* **Use Cases**: This is essential for agentic loops. For example, after an LLM node generates a response, a conditional edge can check if the LLM requested a tool call. If yes, it routes to a "Tool Node"; if no, it routes to the "END" node.

---

## Summary of the Flow

1. Define your **State** schema.
2. Initialize a **StateGraph** with that schema.
3. Add **Nodes** (Python functions) that take the state and return updates.
4. Connect nodes with standard **Edges** for straight-line execution.
5. Add **Conditional Edges** for decision-making (e.g., loops, tool calling).
6. **Compile** the graph and `invoke()` it with an initial state!
