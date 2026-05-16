"""
ContribFlow - Streamlit Frontend
4-stage OSS contribution co-pilot interface
"""

import streamlit as st
import requests
import json
from typing import Optional

# API Configuration
API_BASE = "http://localhost:8000/api"

# Page Configuration
st.set_page_config(
    page_title="ContribFlow - OSS Contribution Co-Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stage-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .prompt-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'repo_url' not in st.session_state:
    st.session_state.repo_url = ""
if 'stage1_result' not in st.session_state:
    st.session_state.stage1_result = None
if 'stage2_result' not in st.session_state:
    st.session_state.stage2_result = None
if 'stage3_result' not in st.session_state:
    st.session_state.stage3_result = None
if 'stage4_result' not in st.session_state:
    st.session_state.stage4_result = None


def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def call_stage1(repo_url: str, bob_response: Optional[str] = None) -> dict:
    """Call Stage 1 API"""
    try:
        response = requests.post(
            f"{API_BASE}/stage1/analyze",
            json={"repo_url": repo_url, "bob_response": bob_response},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Try a smaller repository.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {str(e)}")
        return None


def call_stage2(repo_url: str, idea: str) -> dict:
    """Call Stage 2 API"""
    try:
        response = requests.post(
            f"{API_BASE}/stage2/deduplicate",
            json={"repo_url": repo_url, "idea": idea},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {str(e)}")
        return None


def call_stage3(repo_url: str, change_description: str, diff: str = "") -> dict:
    """Call Stage 3 API"""
    try:
        response = requests.post(
            f"{API_BASE}/stage3/impact",
            json={"repo_url": repo_url, "change_description": change_description, "diff": diff},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Try a smaller repository.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {str(e)}")
        return None


def call_stage4(repo_url: str, diff: str, bob_response: Optional[str] = None) -> dict:
    """Call Stage 4 API"""
    try:
        response = requests.post(
            f"{API_BASE}/stage4/review",
            json={"repo_url": repo_url, "diff": diff, "bob_response": bob_response},
            timeout=90
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {str(e)}")
        return None


# Header
st.markdown('<div class="main-header">🚀 ContribFlow</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Powered OSS Contribution Co-Pilot</p>', unsafe_allow_html=True)

# API Health Check
if not check_api_health():
    st.error("⚠️ Backend API is not running. Please start it with: `uvicorn main:app --reload`")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("📋 Repository")
    repo_url = st.text_input(
        "GitHub Repository URL",
        value=st.session_state.repo_url,
        placeholder="https://github.com/owner/repo",
        help="Enter the full GitHub repository URL"
    )
    
    if repo_url:
        st.session_state.repo_url = repo_url
        st.success(f"✅ Repository set")
    
    st.markdown("---")
    
    st.header("ℹ️ About")
    st.markdown("""
    **ContribFlow** helps you contribute to open-source projects with AI-powered analysis:
    
    1. 🔍 **Gap Finder** - Identify contribution opportunities
    2. 🔄 **Idea Dedup** - Check for conflicts
    3. 📊 **Impact Analysis** - Predict change effects
    4. ✅ **Quality Check** - Pre-PR review
    """)
    
    st.markdown("---")
    st.caption("Built for IBM Bob Hackathon 2026")

# Main Content - Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Stage 1: Gap Finder",
    "🔄 Stage 2: Idea Dedup",
    "📊 Stage 3: Impact Analysis",
    "✅ Stage 4: Quality Check"
])

# ============================================================================
# STAGE 1: GAP FINDER
# ============================================================================
with tab1:
    st.markdown('<div class="stage-header">🔍 Stage 1: Gap Finder</div>', unsafe_allow_html=True)
    st.markdown("Identify contribution opportunities in the repository")
    
    if not st.session_state.repo_url:
        st.warning("⚠️ Please enter a repository URL in the sidebar first")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"📦 Analyzing: **{st.session_state.repo_url}**")
        
        with col2:
            if st.button("🔍 Analyze Repository", key="stage1_analyze", type="primary"):
                with st.spinner("🔄 Fetching repository data..."):
                    result = call_stage1(st.session_state.repo_url)
                    if result:
                        st.session_state.stage1_result = result
        
        # Show results if available
        if st.session_state.stage1_result:
            result = st.session_state.stage1_result
            
            # Metadata
            if "metadata" in result:
                meta = result["metadata"]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📁 Total Files", meta.get("total_files", 0))
                col2.metric("🔬 Analyzed", meta.get("files_analyzed", 0))
                col3.metric("⚠️ Suspicious", meta.get("suspicious_files", 0))
                col4.metric("📝 Commits", meta.get("commits_analyzed", 0))
            
            st.markdown("---")
            
            # Bob Prompt
            st.subheader("📋 Prompt for Bob IDE")
            st.markdown("Copy this prompt to Bob IDE to identify contribution gaps:")
            
            prompt = result.get("prompt_for_bob", "")
            st.code(prompt, language="text")
            
            if st.button("📋 Copy Prompt", key="copy_stage1_prompt"):
                st.success("✅ Prompt copied to clipboard! (Use Ctrl+C manually)")
            
            st.markdown("---")
            
            # Bob Response Input
            st.subheader("🤖 Bob Response")
            bob_response = st.text_area(
                "Paste Bob's response here:",
                height=200,
                placeholder="Paste the JSON response from Bob IDE...",
                key="stage1_bob_response"
            )
            
            if bob_response and st.button("🔄 Parse Response", key="stage1_parse"):
                with st.spinner("🔄 Parsing Bob response..."):
                    parsed_result = call_stage1(st.session_state.repo_url, bob_response)
                    if parsed_result:
                        st.session_state.stage1_result = parsed_result
                        st.rerun()
            
            # Show gaps if parsed
            if result.get("gaps"):
                st.markdown("---")
                st.subheader("🎯 Identified Gaps")
                
                gaps = result["gaps"]
                st.success(f"✅ Found {len(gaps)} contribution opportunities")
                
                for i, gap in enumerate(gaps, 1):
                    with st.expander(f"**{i}. {gap['title']}** ({gap['impact'].upper()} impact)", expanded=i==1):
                        st.markdown(f"**📁 File:** `{gap['file']}`")
                        st.markdown(f"**🏷️ Category:** `{gap['category']}`")
                        st.markdown(f"**💡 Reasoning:**")
                        st.markdown(gap['reasoning'])

# ============================================================================
# STAGE 2: IDEA DEDUPLICATION
# ============================================================================
with tab2:
    st.markdown('<div class="stage-header">🔄 Stage 2: Idea Deduplication</div>', unsafe_allow_html=True)
    st.markdown("Check if your contribution idea conflicts with existing issues/PRs")
    
    if not st.session_state.repo_url:
        st.warning("⚠️ Please enter a repository URL in the sidebar first")
    else:
        st.info(f"📦 Repository: **{st.session_state.repo_url}**")
        
        idea = st.text_area(
            "💡 Your Contribution Idea",
            height=100,
            placeholder="Describe your contribution idea in plain English...\nExample: Add error handling to API endpoints",
            key="stage2_idea"
        )
        
        if idea and st.button("🔍 Check for Conflicts", key="stage2_check", type="primary"):
            with st.spinner("🔄 Analyzing existing issues and PRs..."):
                result = call_stage2(st.session_state.repo_url, idea)
                if result:
                    st.session_state.stage2_result = result
        
        # Show results
        if st.session_state.stage2_result:
            result = st.session_state.stage2_result
            
            st.markdown("---")
            
            status = result.get("status", "unknown")
            conflicts = result.get("conflicts", [])
            
            # Status indicator
            if status == "clear":
                st.success("✅ **CLEAR** - No conflicts found! Your idea is unique.")
            elif status == "complementary":
                st.info("ℹ️ **COMPLEMENTARY** - Related work exists but your idea adds value.")
            elif status == "conflict":
                st.error(f"⚠️ **CONFLICT** - Found {len(conflicts)} conflicting issue(s)/PR(s)")
            
            # Show conflicts
            if conflicts:
                st.markdown("---")
                st.subheader("🔍 Conflicting Issues/PRs")
                
                for conflict in conflicts:
                    with st.expander(f"**{conflict['type'].upper()} #{conflict['number']}**: {conflict['title']}", expanded=True):
                        st.markdown(f"**🔗 URL:** [{conflict['url']}]({conflict['url']})")
                        st.markdown(f"**📊 Similarity:** {conflict['similarity']*100:.0f}%")
                        st.markdown(f"**💬 Summary:**")
                        st.markdown(conflict['summary'])
            
            # Bob Prompt
            if "prompt_for_bob" in result:
                st.markdown("---")
                st.subheader("📋 Prompt for Bob IDE (Optional)")
                with st.expander("View Bob Prompt"):
                    st.code(result["prompt_for_bob"], language="text")

# ============================================================================
# STAGE 3: CHANGE IMPACT ANALYSIS
# ============================================================================
with tab3:
    st.markdown('<div class="stage-header">📊 Stage 3: Change Impact Analysis</div>', unsafe_allow_html=True)
    st.markdown("Predict the impact of your proposed changes")
    
    if not st.session_state.repo_url:
        st.warning("⚠️ Please enter a repository URL in the sidebar first")
    else:
        st.info(f"📦 Repository: **{st.session_state.repo_url}**")
        
        change_desc = st.text_area(
            "📝 Change Description",
            height=100,
            placeholder="Describe the changes you plan to make...\nExample: Refactor authentication module to use JWT tokens",
            key="stage3_change_desc"
        )
        
        diff = st.text_area(
            "📄 Git Diff (Optional)",
            height=150,
            placeholder="Paste your git diff here (optional)...",
            key="stage3_diff"
        )
        
        if change_desc and st.button("📊 Analyze Impact", key="stage3_analyze", type="primary"):
            with st.spinner("🔄 Analyzing dependencies and impact..."):
                result = call_stage3(st.session_state.repo_url, change_desc, diff)
                if result:
                    st.session_state.stage3_result = result
        
        # Show results
        if st.session_state.stage3_result:
            result = st.session_state.stage3_result
            
            st.markdown("---")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("📁 Files Affected", len(result.get("files_affected", [])))
            col2.metric("⚠️ Services at Risk", len(result.get("services_at_risk", [])))
            col3.metric("🧪 Tests to Update", len(result.get("tests_to_update", [])))
            
            st.markdown("---")
            
            # Files Affected
            if result.get("files_affected"):
                st.subheader("📁 Files Affected")
                for file in result["files_affected"]:
                    st.markdown(f"- `{file}`")
            
            # Services at Risk
            if result.get("services_at_risk"):
                st.markdown("---")
                st.subheader("⚠️ Services at Risk")
                for service in result["services_at_risk"]:
                    st.markdown(f"- `{service}`")
            
            # Tests to Update
            if result.get("tests_to_update"):
                st.markdown("---")
                st.subheader("🧪 Tests to Update")
                for test in result["tests_to_update"]:
                    st.markdown(f"- `{test}`")
            
            # Findings
            if result.get("findings"):
                st.markdown("---")
                st.subheader("🔍 Detailed Findings")
                
                for i, finding in enumerate(result["findings"], 1):
                    confidence = finding.get("confidence", 0)
                    finding_type = finding.get("type", "unknown")
                    
                    # Color code by confidence
                    if confidence >= 0.8:
                        icon = "🔴"
                    elif confidence >= 0.5:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                    
                    with st.expander(f"{icon} **Finding {i}** (Confidence: {confidence:.0%}, Type: {finding_type})", expanded=i==1):
                        st.markdown(f"**📝 Description:**")
                        st.markdown(finding.get("finding", ""))
                        
                        if finding.get("evidence_files"):
                            st.markdown(f"**📁 Evidence Files:**")
                            for file in finding["evidence_files"]:
                                st.markdown(f"- `{file}`")
            
            # Suggested Order
            if result.get("suggested_order"):
                st.markdown("---")
                st.subheader("📋 Suggested Implementation Order")
                for i, step in enumerate(result["suggested_order"], 1):
                    st.markdown(f"{i}. {step}")

# ============================================================================
# STAGE 4: PRE-PR QUALITY CHECK
# ============================================================================
with tab4:
    st.markdown('<div class="stage-header">✅ Stage 4: Pre-PR Quality Check</div>', unsafe_allow_html=True)
    st.markdown("Review your changes before submitting a pull request")
    
    if not st.session_state.repo_url:
        st.warning("⚠️ Please enter a repository URL in the sidebar first")
    else:
        st.info(f"📦 Repository: **{st.session_state.repo_url}**")
        
        diff = st.text_area(
            "📄 Git Diff",
            height=200,
            placeholder="Paste your git diff here...\nExample: git diff > changes.diff",
            key="stage4_diff"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if diff and st.button("🔍 Run Static Checks", key="stage4_static", type="primary"):
                with st.spinner("🔄 Running static analysis..."):
                    result = call_stage4(st.session_state.repo_url, diff)
                    if result:
                        st.session_state.stage4_result = result
        
        # Show results
        if st.session_state.stage4_result:
            result = st.session_state.stage4_result
            
            st.markdown("---")
            
            # Summary
            passes = result.get("passes_check")
            summary = result.get("summary", "")
            
            if passes is True:
                st.success(f"✅ **PASSED** - {summary}")
            elif passes is False:
                st.error(f"❌ **FAILED** - {summary}")
            else:
                st.info(f"ℹ️ {summary}")
            
            # Metadata
            if "metadata" in result:
                meta = result["metadata"]
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📁 Files Changed", meta.get("files_changed", 0))
                col2.metric("🔍 Static Issues", meta.get("static_issues", 0))
                col3.metric("❌ Errors", meta.get("static_errors", 0))
                col4.metric("⚠️ Warnings", meta.get("static_warnings", 0))
            
            st.markdown("---")
            
            # Issues
            issues = result.get("issues", [])
            if issues:
                st.subheader("🔍 Issues Found")
                
                # Group by severity
                errors = [i for i in issues if i.get("severity") == "error"]
                warnings = [i for i in issues if i.get("severity") == "warning"]
                infos = [i for i in issues if i.get("severity") == "info"]
                
                # Errors
                if errors:
                    st.markdown("### ❌ Errors")
                    for issue in errors:
                        with st.expander(f"**{issue['file']}:{issue['line']}** - {issue['issue']}", expanded=True):
                            st.markdown(f"**🔧 Fix:** {issue['fix']}")
                            st.markdown(f"**📍 Source:** {issue.get('source', 'unknown')}")
                
                # Warnings
                if warnings:
                    st.markdown("### ⚠️ Warnings")
                    for issue in warnings:
                        with st.expander(f"**{issue['file']}:{issue['line']}** - {issue['issue']}"):
                            st.markdown(f"**🔧 Fix:** {issue['fix']}")
                            st.markdown(f"**📍 Source:** {issue.get('source', 'unknown')}")
                
                # Info
                if infos:
                    st.markdown("### ℹ️ Info")
                    for issue in infos:
                        with st.expander(f"**{issue['file']}:{issue['line']}** - {issue['issue']}"):
                            st.markdown(f"**🔧 Fix:** {issue['fix']}")
                            st.markdown(f"**📍 Source:** {issue.get('source', 'unknown')}")
            else:
                st.success("✅ No issues found!")
            
            # Bob Prompt
            if "prompt_for_bob" in result and result["prompt_for_bob"]:
                st.markdown("---")
                st.subheader("📋 Prompt for Bob IDE (Optional)")
                st.markdown("For deeper analysis, copy this prompt to Bob IDE:")
                
                with st.expander("View Bob Prompt"):
                    st.code(result["prompt_for_bob"], language="text")
                
                # Bob Response Input
                bob_response = st.text_area(
                    "🤖 Paste Bob's response here (optional):",
                    height=150,
                    key="stage4_bob_response"
                )
                
                if bob_response and st.button("🔄 Parse Bob Response", key="stage4_parse"):
                    with st.spinner("🔄 Parsing Bob response..."):
                        parsed_result = call_stage4(st.session_state.repo_url, diff, bob_response)
                        if parsed_result:
                            st.session_state.stage4_result = parsed_result
                            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><strong>ContribFlow</strong> - AI-Powered OSS Contribution Co-Pilot</p>
    <p>Built for IBM Bob Hackathon 2026 | Made with ❤️ and 🤖</p>
</div>
""", unsafe_allow_html=True)

# Made with Bob
