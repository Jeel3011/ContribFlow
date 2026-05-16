import re
from collections import defaultdict

def build_dependency_map(tree: list[dict], file_contents: dict[str, str]) -> dict:
    imports = defaultdict(list)
    imported_by = defaultdict(list)
    
    module_to_path = {}
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        if not path.endswith(".py"):
            continue
        module = path.replace("/", ".").removesuffix(".py")
        module_to_path[module] = path
        module_to_path[path.split("/")[-1].removesuffix(".py")] = path
    
    for path, content in file_contents.items():
        if not path.endswith(".py"):
            continue
        for line in content.split("\n"):
            line = line.strip()
            m = re.match(r'^from\s+([\w.]+)\s+import', line)
            if m:
                module_name = m.group(1)
                target_path = module_to_path.get(module_name) or module_to_path.get(module_name.split(".")[-1])
                if target_path and target_path != path:
                    imports[path].append(target_path)
                    imported_by[target_path].append(path)
            m = re.match(r'^import\s+([\w.]+)', line)
            if m:
                module_name = m.group(1)
                target_path = module_to_path.get(module_name) or module_to_path.get(module_name.split(".")[-1])
                if target_path and target_path != path:
                    imports[path].append(target_path)
                    imported_by[target_path].append(path)
    
    return {"imports": dict(imports), "imported_by": dict(imported_by)}


def find_affected_files(target_files: list[str], dep_map: dict, depth: int = 2) -> dict:
    affected = {"direct": set(), "indirect": set()}
    imported_by = dep_map["imported_by"]
    
    for target in target_files:
        for importer in imported_by.get(target, []):
            affected["direct"].add(importer)
    
    if depth >= 2:
        for direct_file in list(affected["direct"]):
            for importer in imported_by.get(direct_file, []):
                if importer not in affected["direct"]:
                    affected["indirect"].add(importer)
    
    return {"direct": sorted(affected["direct"]), "indirect": sorted(affected["indirect"])}


def identify_target_files(change_description: str, source_files: list[str]) -> list[str]:
    import re
    desc_lower = change_description.lower()
    STOP = {"the","a","an","in","to","for","of","and","or","with","add","modify","update","change","fix","improve","refactor","implement","create","use","make","instead"}
    keywords = [w for w in re.findall(r'\b[a-z_]+\b', desc_lower) if w not in STOP and len(w) > 3]
    scored = []
    for path in source_files:
        path_lower = path.lower()
        score = sum(1 for kw in keywords if kw in path_lower)
        if score > 0:
            scored.append((score, path))
    scored.sort(reverse=True)
    return [path for _, path in scored[:5]]


def find_dynamic_imports(file_contents: dict[str, str]) -> list[str]:
    dynamic = []
    patterns = [r'importlib\.import_module', r'__import__\(', r'exec\(', r'eval\(']
    for path, content in file_contents.items():
        for pattern in patterns:
            if re.search(pattern, content):
                dynamic.append(path)
                break
    return dynamic


def build_reverse_dependencies_with_confidence(
    target_files: list[str],
    dep_map: dict,
    max_depth: int = 2
) -> dict[str, dict]:
    """
    Build reverse dependency map with confidence scores
    
    Args:
        target_files: Files to find importers for
        dep_map: Dependency map from build_dependency_map()
        max_depth: Maximum dependency depth (1=direct, 2=indirect)
        
    Returns:
        {
            "file.py": {
                "importers": ["importer1.py", "importer2.py"],
                "confidence_scores": {"importer1.py": 0.95, "importer2.py": 0.90},
                "depth": {"importer1.py": 1, "importer2.py": 1}
            }
        }
    """
    imported_by = dep_map.get("imported_by", {})
    reverse_deps = {}
    
    for target in target_files:
        importers = {}
        depths = {}
        
        # Direct importers (depth 1)
        direct_importers = imported_by.get(target, [])
        for importer in direct_importers:
            importers[importer] = 0.95  # High confidence for direct imports
            depths[importer] = 1
        
        # Indirect importers (depth 2)
        if max_depth >= 2:
            for direct_importer in direct_importers:
                indirect_importers = imported_by.get(direct_importer, [])
                for importer in indirect_importers:
                    if importer not in importers and importer != target:
                        importers[importer] = 0.65  # Medium confidence for indirect
                        depths[importer] = 2
        
        if importers:
            reverse_deps[target] = {
                "importers": sorted(importers.keys()),
                "confidence_scores": importers,
                "depth": depths,
                "total_importers": len(importers)
            }
    
    return reverse_deps


def get_all_affected_with_confidence(
    target_files: list[str],
    dep_map: dict,
    max_depth: int = 2
) -> dict[str, float]:
    """
    Get all affected files with confidence scores
    
    Returns:
        {"file.py": confidence_score, ...}
    """
    reverse_deps = build_reverse_dependencies_with_confidence(
        target_files, dep_map, max_depth
    )
    
    all_affected = {}
    
    # Add target files with max confidence
    for target in target_files:
        all_affected[target] = 1.0
    
    # Add all importers with their confidence scores
    for target, data in reverse_deps.items():
        for importer, confidence in data["confidence_scores"].items():
            if importer not in all_affected:
                all_affected[importer] = confidence
            else:
                # Take max confidence if file appears multiple times
                all_affected[importer] = max(all_affected[importer], confidence)
    
    return all_affected
