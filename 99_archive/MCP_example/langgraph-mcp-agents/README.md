# LangGraph Agent with MCP

[![English](https://img.shields.io/badge/Language-English-blue)](README.md) [![Korean](https://img.shields.io/badge/Language-한국어-red)](README_KOR.md)

[![GitHub](https://img.shields.io/badge/GitHub-langgraph--mcp--agents-black?logo=github)](https://github.com/teddylee777/langgraph-mcp-agents)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-≥3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Version](https://img.shields.io/badge/Version-0.1.0-orange)](https://github.com/teddylee777/langgraph-mcp-agents)

![project demo](./assets/project-demo.png)

## Project Overview

![project architecture](./assets/architecture.png)

`LangChain-MCP-Adapters` is a toolkit provided by **LangChain AI** that enables AI agents to interact with external tools and data sources through the Model Context Protocol (MCP). This project provides a user-friendly interface for deploying ReAct agents that can access various data sources and APIs through MCP tools.

### Features

- **Streamlit Interface**: User-friendly web interface for interacting with LangGraph `ReAct Agent` with MCP tools
- **Tool Management**: Add, remove, and configure MCP tools directly through the UI(supports Smithery JSON Format). This happens dynamically without restarting the application.
- **Streaming Responses**: See agent responses and tool calls in real-time
- **Conversation History**: Track and manage your conversation with the agent

## MCP Architecture

MCP (Model Context Protocol) consists of three main components.

1. **MCP Host**: Programs that want to access data through MCP, such as Claude Desktop, IDEs, or LangChain/LangGraph.

2. **MCP Client**: Protocol clients that maintain 1:1 connections with servers, acting as intermediaries between hosts and servers.

3. **MCP Server**: Lightweight programs that expose specific functionalities through the standardized model context protocol, serving as key data sources.

## Installation

1. Clone this repository

```bash
git clone https://github.com/yourusername/langgraph-mcp-agents.git
cd langgraph-mcp-agents
```

2. Create a virtual environment and install dependencies using uv

```bash
uv venv
uv pip install -r requirements.txt
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Create a `.env` file with your API keys(from `.env.example`)

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key(optional)
TAVILY_API_KEY=your_tavily_api_key(optional)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=your_langsmith_project
```

## Usage

1. Start the Streamlit application.

```bash
streamlit run app.py
```

2. The application will launch in your browser, displaying the main interface.

3. Use the sidebar to add and configure MCP tools

You may visit to [Smithery](https://smithery.ai/) to find useful MCP servers.

First, select the tool you want to use.

Press COPY button JSON Configurations on the right side.

![copy from Smithery](./assets/smithery-copy-json.png)

Paste copied JSON string to the `Tool JSON` section.

<img src="./assets/add-tools.png" alt="tool json" style="width: auto; height: auto;">

Press `Add Tool` button to the "Registered Tools List" section.

Finally, "Apply" button to apply changes to initialize the agent with the new tools.

<img src="./assets/apply-tool-configuration.png" alt="tool json" style="width: auto; height: auto;">

4. Check the status of the agent.

![check status](./assets/check-status.png)

5. Ask questions in the chat interface to interact with the ReAct agent that utilizes the configured MCP tools.

![project demo](./assets/project-demo.png)

## Hands-on Tutorial

For developers who want to dive deeper into how MCP integration works with LangGraph, we've provided a comprehensive Jupyter notebook tutorial:

- link: [MCP-HandsOn-ENG.ipynb](./MCP-HandsOn-ENG.ipynb)

This hands-on tutorial covers:

1. **MCP Client Setup** - Learn how to configure and initialize MultiServerMCPClient for connecting to MCP servers
2. **Local MCP Server Integration** - Connect to a locally running MCP server via SSE and Stdio methods
3. **RAG Integration** - Use MCP to access a retriever tool for document search functionality
4. **Mixed Transport Methods** - Combine different transport protocols (SSE and Stdio) in a single agent
5. **LangChain Tools + MCP** - Integrate native LangChain tools alongside MCP tools

The tutorial walks through practical examples with step-by-step explanations to help you understand how to build and integrate MCP tools into your LangGraph agents.

## License

MIT License 

## References

- https://github.com/langchain-ai/langchain-mcp-adapters