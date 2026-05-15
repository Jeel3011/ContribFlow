import json
from stage3.github_api import get_tree, get_file_content
from stage3.dependency_map import (
    build_dependency_map, find_affected_files,
    identify_target_files, find_dynamic_imports
)
from stage3.prompt_builder import assemble_stage3_context, build_stage3_prompt

SOURCE_EXTS = {".py", ".js", ".ts", ".go", ".java"}
SKIP_DIRS = {"test", "tests", "node_modules", "vendor", "dist", "build"}

def run_stage3(repo_url: str, change_description: str, diff: str = "") -> dict:
    owner_repo = repo_url.replace("https://github.com/", "").strip("/")
    
    tree = get_tree(owner_repo)
    
    source_files = [
        item["path"] for item in tree
        if item.get("type") == "blob"
        and any(item["path"].endswith(ext) for ext in SOURCE_EXTS)
        and not any(d in item["path"].split("/") for d in SKIP_DIRS)
    ]
    
    target_files = identify_target_files(change_description, source_files)
    
    candidate_paths = list(set(target_files + source_files[:20]))[:25]
    file_contents = {}
    for path in candidate_paths:
        content = get_file_content(owner_repo, path)
        if content:
            file_contents[path] = content
    
    dep_map = build_dependency_map(tree, file_contents)
    affected = find_affected_files(target_files, dep_map)
    dynamic_imports = find_dynamic_imports(file_contents)
    
    context = assemble_stage3_context(target_files, affected, file_contents, dep_map)
    prompt = build_stage3_prompt(owner_repo, change_description, diff, context, dynamic_imports)
    
    return {
        "owner_repo": owner_repo,
        "target_files_identified": target_files,
        "static_affected": affected,
        "dynamic_import_risks": dynamic_imports[:5],
        "prompt_for_bob": prompt,
        "token_estimate": len(prompt)
    }
