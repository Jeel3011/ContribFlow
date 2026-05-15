def assemble_stage3_context(target_files, affected, file_contents, dep_map):
    context_parts = []
    
    for f in target_files:
        if f in file_contents:
            lines = file_contents[f].split("\n")
            trimmed = "\n".join(lines[:80])
            context_parts.append(f"=== TARGET: {f} ===\n{trimmed}")
    
    for f in affected.get("direct", []):
        if f in file_contents:
            lines = file_contents[f].split("\n")
            trimmed = "\n".join(lines[:80])
            context_parts.append(f"=== DIRECT IMPORTER: {f} ===\n{trimmed}")
    
    return "\n\n".join(context_parts)


def build_stage3_prompt(repo, change_description, diff, context, dynamic_imports):
    diff_section = f"\nDiff provided:\n{diff[:2000]}" if diff else ""
    dynamic_section = ""
    if dynamic_imports:
        dynamic_section = f"\nFiles with dynamic imports (uncertain blast radius):\n" + "\n".join(dynamic_imports[:5])
    
    return f"""You are analyzing the change impact for a GitHub repository.

Repository: {repo}
Change description: {change_description}
{diff_section}

Source file context:
{context}
{dynamic_section}

Analyze the full blast radius of this change. For each finding, assign a confidence score (0.0-1.0).
Rules:
- Direct imports: confidence 0.7-0.95
- Indirect (2-hop): confidence 0.4-0.65
- Dynamic imports: confidence 0.1-0.4
- Only include findings with confidence >= 0.2

Return ONLY valid JSON, no markdown:
{{
  "repo": "{repo}",
  "change_description": "{change_description[:100]}",
  "files_affected": [],
  "services_at_risk": [],
  "tests_to_update": [],
  "findings": [
    {{"finding": "", "confidence": 0.0, "type": "direct|indirect|dynamic", "evidence_files": []}}
  ],
  "suggested_order": []
}}"""
