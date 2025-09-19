import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

def render_content_workflow_page(workflow_manager, user_id: str):
    """Render the content workflow management page"""
    st.title("📋 Content Workflow Management")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Workflow Options")
        view_mode = st.radio(
            "Select View",
            ["Dashboard", "Create Workflow", "Manage Workflows", "Analytics"]
        )
    
    # Main content area
    if view_mode == "Dashboard":
        render_dashboard(workflow_manager, user_id)
    elif view_mode == "Create Workflow":
        render_create_workflow(workflow_manager, user_id)
    elif view_mode == "Manage Workflows":
        render_manage_workflows(workflow_manager, user_id)
    elif view_mode == "Analytics":
        render_analytics(workflow_manager, user_id)

def render_dashboard(workflow_manager, user_id: str):
    """Render the dashboard view"""
    st.header("📊 Workflow Dashboard")
    
    # Get workflows
    workflows = workflow_manager.get_workflows(user_id)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Workflows", len(workflows))
    with col2:
        active = len([w for w in workflows if w.get('status') == 'in_progress'])
        st.metric("Active", active)
    with col3:
        completed = len([w for w in workflows if w.get('status') == 'published'])
        st.metric("Completed", completed)
    with col4:
        planned = len([w for w in workflows if w.get('status') == 'planned'])
        st.metric("Planned", planned)
    
    # Recent workflows
    st.subheader("Recent Workflows")
    if workflows:
        for workflow in workflows[:5]:
            with st.expander(f"📝 {workflow.get('title', 'Untitled')}"):
                st.write(f"**Type:** {workflow.get('content_type', 'N/A')}")
                st.write(f"**Status:** {workflow.get('status', 'N/A')}")
                st.write(f"**Platforms:** {', '.join(workflow.get('platforms', []))}")
    else:
        st.info("No workflows created yet. Start by creating your first workflow!")

def render_create_workflow(workflow_manager, user_id: str):
    """Render the create workflow form"""
    st.header("🚀 Create New Workflow")
    
    with st.form("create_workflow_form"):
        title = st.text_input("Workflow Title", placeholder="My Amazing Content")
        
        content_type = st.selectbox(
            "Content Type",
            ["Blog Post", "Video Script", "Social Media Campaign", "Podcast Episode", "Newsletter"]
        )
        
        platforms = st.multiselect(
            "Target Platforms",
            ["YouTube", "Instagram", "TikTok", "LinkedIn", "Twitter/X", "Facebook", "Blog"]
        )
        
        target_date = st.date_input(
            "Target Publish Date",
            min_value=datetime.now().date(),
            value=datetime.now().date() + timedelta(days=7)
        )
        
        submitted = st.form_submit_button("Create Workflow")
        
        if submitted and title and platforms:
            workflow = workflow_manager.create_workflow(
                user_id, title, content_type, platforms, 
                datetime.combine(target_date, datetime.min.time())
            )
            st.success(f"✅ Workflow '{title}' created successfully!")
            st.balloons()

def render_manage_workflows(workflow_manager, user_id: str):
    """Render the manage workflows view"""
    st.header("⚙️ Manage Workflows")
    
    workflows = workflow_manager.get_workflows(user_id)
    
    if not workflows:
        st.info("No workflows to manage. Create your first workflow to get started!")
        return
    
    # Filter options
    status_filter = st.selectbox("Filter by Status", ["All", "Planned", "In Progress", "Published"])
    
    # Display workflows
    for workflow in workflows:
        if status_filter != "All" and workflow.get('status') != status_filter.lower().replace(" ", "_"):
            continue
            
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{workflow.get('title', 'Untitled')}**")
                st.caption(f"Type: {workflow.get('content_type', 'N/A')}")
            with col2:
                new_status = st.selectbox(
                    "Status",
                    ["planned", "in_progress", "published"],
                    index=["planned", "in_progress", "published"].index(workflow.get('status', 'planned')),
                    key=f"status_{workflow.get('id')}"
                )
            with col3:
                if st.button("Update", key=f"update_{workflow.get('id')}"):
                    if workflow_manager.update_workflow_status(workflow.get('id'), new_status):
                        st.success("Updated!")
                        st.rerun()
            st.divider()

def render_analytics(workflow_manager, user_id: str):
    """Render the analytics view"""
    st.header("📈 Workflow Analytics")
    
    workflows = workflow_manager.get_workflows(user_id)
    
    if not workflows:
        st.info("No data available yet. Create and complete some workflows to see analytics!")
        return
    
    # Calculate metrics
    total_workflows = len(workflows)
    completed_workflows = len([w for w in workflows if w.get('status') == 'published'])
    completion_rate = (completed_workflows / total_workflows * 100) if total_workflows > 0 else 0
    
    # Display analytics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    with col2:
        st.metric("Average Time to Publish", "Coming Soon")
    
    # Platform distribution
    st.subheader("Platform Distribution")
    platform_counts = {}
    for workflow in workflows:
        for platform in workflow.get('platforms', []):
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    if platform_counts:
        st.bar_chart(platform_counts)
