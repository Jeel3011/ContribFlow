"""
ARCHIVED — This file is no longer used.
routes.py imports from stage3.enhanced_pipeline, not this module.
Kept for reference. See enhanced_pipeline.py for the active implementation.

Stage 3 Change Impact Analysis - LangGraph Agent Implementation
Uses ReAct pattern to analyze repository changes and predict impact
"""

import os
import json
import re
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from stage3.github_api import get_tree, get_file_content
from stage3.dependency_map import (
    build_dependency_map, find_affected_files,
    identify_target_files, find_dynamic_imports
)

# Constants
SOURCE_EXTS = {".py", ".js", ".ts", ".go", ".java"}
SKIP_DIRS = {"test", "tests", "node_modules", "vendor", "dist", "build"}


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    repo_url: str
    owner_repo: str
    change_description: str
    diff: str
    repo_tree: list
    target_files: list
    file_contents: dict
    dep_map: dict
    affected_files: dict
    dynamic_imports: list
    final_output: dict


# Tool definitions for the agent
@tool
def fetch_repo_tree(owner_repo: str) -> str:
    """
    Fetch the repository file tree from GitHub.
    
    Args:
        owner_repo: Repository in format 'owner/repo'
        
    Returns:
        JSON string containing the file tree with paths and types
    """
    try:
        tree = get_tree(owner_repo)
        # Filter to source files only
        source_files = [
            {"path": item["path"], "type": item.get("type")}
            for item in tree
            if item.get("type") == "blob"
            and any(item["path"].endswith(ext) for ext in SOURCE_EXTS)
            and not any(d in item["path"].split("/") for d in SKIP_DIRS)
        ]
        return json.dumps({
            "total_files": len(source_files),
            "files": source_files[:100]  # Limit to 100 for token efficiency
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def fetch_file_content(owner_repo: str, file_path: str) -> str:
    """
    Fetch the content of a specific file from GitHub.
    
    Args:
        owner_repo: Repository in format 'owner/repo'
        file_path: Path to the file within the repository
        
    Returns:
        File content as string (first 80 lines for token efficiency)
    """
    try:
        content = get_file_content(owner_repo, file_path)
        if content:
            lines = content.split("\n")
            trimmed = "\n".join(lines[:80])
            return f"File: {file_path}\n{trimmed}"
        return f"Error: Could not fetch content for {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def analyze_dependencies(owner_repo: str, target_files: str, repo_tree_json: str, file_contents_json: str) -> str:
    """
    Analyze static dependencies and find affected files.
    
    Args:
        owner_repo: Repository in format 'owner/repo'
        target_files: JSON array of target file paths
        repo_tree_json: JSON string of repository tree
        file_contents_json: JSON object mapping file paths to contents
        
    Returns:
        JSON string with dependency analysis results
    """
    try:
        target_list = json.loads(target_files)
        tree = json.loads(repo_tree_json).get("files", [])
        contents = json.loads(file_contents_json)
        
        # Build dependency map
        dep_map = build_dependency_map(tree, contents)
        
        # Find affected files
        affected = find_affected_files(target_list, dep_map)
        
        # Find dynamic imports
        dynamic = find_dynamic_imports(contents)
        
        return json.dumps({
            "target_files": target_list,
            "direct_affected": affected.get("direct", []),
            "indirect_affected": affected.get("indirect", []),
            "dynamic_imports": dynamic[:5],
            "dependency_map": {
                "imports_count": len(dep_map.get("imports", {})),
                "imported_by_count": len(dep_map.get("imported_by", {}))
            }
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# Create tools list
tools = [fetch_repo_tree, fetch_file_content, analyze_dependencies]


def create_agent_executor():
    """Create a simplified agent that calls OpenAI directly without LangGraph tools"""
    
    # Initialize LLM (API key from environment)
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    
    def call_model_simple(state: AgentState):
        """Call the LLM with a simple prompt"""
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}
    
    def parse_final_output(state: AgentState):
        """Parse the final output from the agent"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Extract JSON from the response
        content = last_message.content if hasattr(last_message, "content") else str(last_message)
        content_str = str(content) if not isinstance(content, str) else content
        
        # Try to extract JSON from markdown code blocks or plain text
        json_match = re.search(r'\{[\s\S]*\}', content_str)
        if json_match:
            try:
                output = json.loads(json_match.group(0))
                return {"final_output": output}
            except json.JSONDecodeError:
                pass
        
        # Fallback: create minimal valid output
        return {
            "final_output": {
                "repo": state.get("owner_repo", ""),
                "change_description": state.get("change_description", ""),
                "files_affected": [],
                "services_at_risk": [],
                "tests_to_update": [],
                "findings": [],
                "suggested_order": []
            }
        }
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model_simple)
    workflow.add_node("parse_output", parse_final_output)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add edge from agent to parse_output
    workflow.add_edge("agent", "parse_output")
    
    # Add edge from parse_output to END
    workflow.add_edge("parse_output", END)
    
    return workflow.compile()


def run_stage3(repo_url: str, change_description: str, diff: str = "") -> dict:
    """
    Run Stage 3 Change Impact Analysis using LangGraph agent
    
    Args:
        repo_url: GitHub repository URL
        change_description: Description of the proposed change
        diff: Optional git diff of changes
        
    Returns:
        Structured JSON output matching Stage 3 schema
    """
    # Extract owner/repo from URL
    owner_repo = repo_url.split("github.com/")[-1].strip("/")
    
    try:
        # Run static analysis FIRST (before AI)
        print(f"Fetching repository structure for {owner_repo}...")
        tree = get_tree(owner_repo)
        source_files = [item["path"] for item in tree if item.get("type") == "blob" and any(item["path"].endswith(ext) for ext in SOURCE_EXTS)]
        
        print(f"Identifying target files...")
        target_files = identify_target_files(change_description, source_files[:100])
        
        print(f"Fetching file contents (max 7 files)...")
        file_contents = {}
        for path in target_files[:7]:
            content = get_file_content(owner_repo, path)
            if content:
                file_contents[path] = content
        
        print(f"Building dependency map...")
        dep_map = build_dependency_map(tree, file_contents)
        affected = find_affected_files(target_files, dep_map)
        dynamic = find_dynamic_imports(file_contents)
        
        # Build context summary for AI
        context_summary = f"""
Repository Analysis for {owner_repo}:

Target Files Identified ({len(target_files)}):
{chr(10).join(f"- {f}" for f in target_files[:5])}

Direct Dependencies ({len(affected.get('direct', []))}):
{chr(10).join(f"- {f}" for f in affected.get('direct', [])[:5])}

Indirect Dependencies ({len(affected.get('indirect', []))}):
{chr(10).join(f"- {f}" for f in affected.get('indirect', [])[:3])}

Dynamic Imports Found ({len(dynamic)}):
{chr(10).join(f"- {f}" for f in dynamic[:3])}

File Contents (first 80 lines each):
{chr(10).join(f"--- {path} ---{chr(10)}{content.split(chr(10))[:80]}" for path, content in list(file_contents.items())[:3])}
"""
        
        # Create the agent
        agent = create_agent_executor()
        
        # Build the prompt with pre-analyzed data
        system_prompt = f"""You are a code impact analysis expert. Based on the static analysis below, provide a comprehensive impact assessment.

Repository: {owner_repo}
Change Description: {change_description}
{f"Diff: {diff[:300]}" if diff else ""}

{context_summary}

CRITICAL: Return ONLY valid JSON matching this exact schema:
{{
  "repo": "{owner_repo}",
  "change_description": "{change_description[:100]}",
  "files_affected": ["list of file paths that will be modified"],
  "services_at_risk": ["list of service/class names whose behavior changes"],
  "tests_to_update": ["list of test file paths"],
  "findings": [
    {{
      "finding": "description of impact",
      "confidence": 0.85,
      "type": "direct|indirect|dynamic",
      "evidence_files": ["file1.py"]
    }}
  ],
  "suggested_order": ["step 1", "step 2"]
}}

Confidence rules:
- Direct calls/imports: 0.85-0.95
- Indirect (2 hops): 0.4-0.7
- Dynamic imports: 0.2-0.4
- Only include findings with confidence >= 0.2

Provide the JSON output now."""
        
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=system_prompt)],
            "repo_url": repo_url,
            "owner_repo": owner_repo,
            "change_description": change_description,
            "diff": diff,
            "repo_tree": [],
            "target_files": [],
            "file_contents": {},
            "dep_map": {},
            "affected_files": {},
            "dynamic_imports": [],
            "final_output": {}
        }
        
        # Run the agent
        print(f"Running LangGraph agent...")
        final_state = agent.invoke(initial_state)  # type: ignore
        output = final_state.get("final_output", {})
        
        # Ensure all required fields are present
        required_fields = {
            "repo": owner_repo,
            "change_description": change_description,
            "files_affected": [],
            "services_at_risk": [],
            "tests_to_update": [],
            "findings": [],
            "suggested_order": []
        }
        
        for key, default in required_fields.items():
            if key not in output:
                output[key] = default
        
        return output
        
    except Exception as e:
        # Return error in valid format
        print(f"Error in pipeline: {str(e)}")
        return {
            "repo": owner_repo,
            "change_description": change_description,
            "files_affected": [],
            "services_at_risk": [],
            "tests_to_update": [],
            "findings": [{
                "finding": f"Analysis error: {str(e)}",
                "confidence": 0.0,
                "type": "error",
                "evidence_files": []
            }],
            "suggested_order": []
        }

# Made with Bob
