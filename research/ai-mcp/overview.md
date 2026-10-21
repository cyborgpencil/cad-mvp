# AI Tools & MCP (Model Context Protocol)

## What is MCP
- Open standard (Anthropic-led) for LLMs to connect to external tools/data.
- "USB-C for AI": Clients (Claude, Cursor, ChatGPT, Gemini, VS Code) talk to Servers exposing tools, resources, prompts.
- JSON-RPC 2.0. Tools: executable functions with schemas. Resources: data. Prompts: templates.
- Enables AI agents to act (query DB, run CAM, generate geometry) securely.

## Relevance to CAD/CAM MVP
- First-class AI: Embed MCP server so agents can:
  - Query/modify parametric models.
  - Generate toolpaths, run sims.
  - Suggest design changes, auto-export.
  - Integrate with external AI (Claude, etc.).
- Frameworks: mcp-use (TS/Python), official SDKs.

## Support (as of Oct 2026)
Claude, OpenAI Responses API, Gemini, VS Code/Copilot, Amazon Bedrock, etc.

## Implementation Notes
- Build MCP server exposing CAD ops (create sketch, extrude, boolean, export STEP/STL).
- Allow natural language design: "Add 5mm fillet and export 3MF".

Source: claude.com, mcp-use GitHub, protocol docs.
