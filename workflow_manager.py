"""
Content Workflow Management - Complete Implementation
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional

class ContentWorkflowManager:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def create_content_project(self, user_id: str, project_data: Dict):
        """Create a new content project"""
        response = self.supabase.table("content_projects").insert({
            "user_id": user_id,
            "name": project_data["name"],
            "description": project_data.get("description", ""),
            "content_segment": project_data["content_segment"],
            "target_audience": project_data["target_audience"],
            "start_date": project_data.get("start_date"),
            "end_date": project_data.get("end_date"),
            "target_platforms": project_data.get("platforms", []),
            "total_content_pieces": project_data.get("total_pieces", 0)
        }).execute()
        return response.data[0] if response.data else None
    
    def add_content_to_pipeline(self, user_id: str, content_data: Dict):
        """Add content piece to the workflow pipeline"""
        response = self.supabase.table("content_pipeline").insert({
            "user_id": user_id,
            "project_id": content_data.get("project_id"),
            "content_generation_id": content_data.get("content_generation_id"),
            "title": content_data["title"],
            "content_type": content_data["content_type"],
            "platform": content_data["platform"],
            "workflow_stage": "idea",
            "content_data": content_data.get("content_data", {}),
            "scheduled_publish_date": content_data.get("scheduled_date"),
            "hashtags": content_data.get("hashtags", []),
            "call_to_action": content_data.get("call_to_action", "")
        }).execute()
        return response.data[0] if response.data else None
    
    def update_workflow_stage(self, content_id: str, new_stage: str, notes: str = ""):
        """Update the workflow stage of content"""
        update_data = {
            "workflow_stage": new_stage,
            "updated_at": datetime.now().isoformat()
        }
        
        # Add specific fields based on stage
        if new_stage == "published":
            update_data["actual_publish_date"] = datetime.now().isoformat()
        
        response = self.supabase.table("content_pipeline")\
            .update(update_data)\
            .eq("id", content_id)\
            .execute()
        
        # Add note if provided
        if notes:
            self.add_content_note(content_id, f"Stage updated to {new_stage}: {notes}")
        
        return response.data[0] if response.data else None
    
    def create_task(self, user_id: str, task_data: Dict):
        """Create a new task for content workflow"""
        response = self.supabase.table("content_tasks").insert({
            "user_id": user_id,
            "content_pipeline_id": task_data["content_pipeline_id"],
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "task_type": task_data["task_type"],
            "priority": task_data.get("priority", "medium"),
            "due_date": task_data.get("due_date"),
            "estimated_hours": task_data.get("estimated_hours"),
            "assigned_to": task_data.get("assigned_to", user_id)
        }).execute()
        return response.data[0] if response.data else None
    
    def complete_task(self, task_id: str, actual_hours: float = None):
        """Mark task as completed"""
        update_data = {
            "status": "completed",
            "completed_date": datetime.now().isoformat()
        }
        if actual_hours:
            update_data["actual_hours"] = actual_hours
        
        return self.supabase.table("content_tasks")\
            .update(update_data)\
            .eq("id", task_id)\
            .execute()
    
    def record_publication(self, content_id: str, publication_data: Dict):
        """Record that content was published with platform details"""
        update_data = {
            "workflow_stage": "published",
            "actual_publish_date": publication_data.get("publish_date", datetime.now().isoformat()),
            "platform_post_id": publication_data.get("post_id"),
            "platform_url": publication_data.get("url")
        }
        
        return self.supabase.table("content_pipeline")\
            .update(update_data)\
            .eq("id", content_id)\
            .execute()
    
    def update_performance_metrics(self, content_id: str, metrics: Dict):
        """Update content performance metrics"""
        # Insert new analytics record
        analytics_data = {
            "content_pipeline_id": content_id,
            "views": metrics.get("views", 0),
            "likes": metrics.get("likes", 0),
            "comments": metrics.get("comments", 0),
            "shares": metrics.get("shares", 0),
            "clicks": metrics.get("clicks", 0),
            "impressions": metrics.get("impressions", 0),
            "engagement_rate": metrics.get("engagement_rate"),
            "revenue": metrics.get("revenue", 0)
        }
        
        return self.supabase.table("content_analytics")\
            .insert(analytics_data)\
            .execute()
    
    def get_content_pipeline(self, user_id: str, status_filter: str = None):
        """Get user's content pipeline with optional status filter"""
        query = self.supabase.table("content_pipeline")\
            .select("*, content_projects(name), content_analytics(views, likes, comments, engagement_rate)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)
        
        if status_filter:
            query = query.eq("workflow_stage", status_filter)
        
        return query.execute().data
    
    def get_user_tasks(self, user_id: str, status: str = None):
        """Get user's tasks with optional status filter"""
        query = self.supabase.table("content_tasks")\
            .select("*, content_pipeline(title, platform)")\
            .eq("user_id", user_id)\
            .order("due_date", desc=False)
        
        if status:
            query = query.eq("status", status)
        
        return query.execute().data
    
    def get_dashboard_metrics(self, user_id: str):
        """Get dashboard metrics for user"""
        # Get summary from view
        response = self.supabase.rpc("get_user_dashboard_summary", {
            "user_id": user_id
        }).execute()
        
        return response.data[0] if response.data else {}

def render_content_workflow_page(workflow_manager: ContentWorkflowManager, user_id: str):
    """Render the main content workflow page"""
    
    st.header("Content Workflow Management")
    
    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    metrics = workflow_manager.get_dashboard_metrics(user_id)
    
    with col1:
        st.metric("Active Projects", metrics.get("total_projects", 0))
    with col2:
        st.metric("Content Pieces", metrics.get("total_content_pieces", 0), 
                 delta=f"{metrics.get('published_pieces', 0)} published")
    with col3:
        st.metric("Pending Tasks", metrics.get("pending_tasks", 0))
    with col4:
        st.metric("Total Views", f"{metrics.get('total_views', 0):,}")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Pipeline", "Tasks", "Calendar", "Analytics"])
    
    with tab1:
        render_content_pipeline_tab(workflow_manager, user_id)
    
    with tab2:
        render_tasks_tab(workflow_manager, user_id)
    
    with tab3:
        render_calendar_tab(workflow_manager, user_id)
    
    with tab4:
        render_analytics_tab(workflow_manager, user_id)

def render_content_pipeline_tab(workflow_manager: ContentWorkflowManager, user_id: str):
    """Render content pipeline management"""
    
    st.subheader("Content Pipeline")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        stage_filter = st.selectbox("Filter by Stage", [
            "All", "idea", "outlined", "drafted", "scripted", "recorded", 
            "edited", "reviewed", "scheduled", "published", "analyzed"
        ])
    
    with col2:
        if st.button("Add New Content"):
            st.session_state["show_add_content"] = True
    
    # Show add content form
    if st.session_state.get("show_add_content", False):
        render_add_content_form(workflow_manager, user_id)
    
    # Get pipeline content
    stage_filter = None if stage_filter == "All" else stage_filter
    pipeline_content = workflow_manager.get_content_pipeline(user_id, stage_filter)
    
    # Display pipeline as kanban board
    stages = ["idea", "drafted", "reviewed", "scheduled", "published"]
    
    cols = st.columns(len(stages))
    for i, stage in enumerate(stages):
        with cols[i]:
            st.markdown(f"**{stage.title()}**")
            stage_content = [item for item in pipeline_content if item["workflow_stage"] == stage]
            
            for content in stage_content[:3]:  # Show first 3 items
                with st.container():
                    st.markdown(f"🎯 **{content['title']}**")
                    st.caption(f"{content['platform']} • {content.get('scheduled_publish_date', 'No date')[:10]}")
                    
                    # Action buttons
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("▶️", key=f"advance_{content['id']}", help="Advance stage"):
                            next_stage = get_next_stage(stage)
                            if next_stage:
                                workflow_manager.update_workflow_stage(content['id'], next_stage)
                                st.experimental_rerun()
                    
                    with col_b:
                        if st.button("📝", key=f"edit_{content['id']}", help="Edit/View details"):
                            st.session_state[f"editing_{content['id']}"] = True
                    
                    st.markdown("---")
            
            if len(stage_content) > 3:
                st.caption(f"...and {len(stage_content) - 3} more")

def render_tasks_tab(workflow_manager: ContentWorkflowManager, user_id: str):
    """Render task management"""
    
    st.subheader("Task Management")
    
    # Task filters and actions
    col1, col2, col3 = st.columns(3)
    with col1:
        task_status = st.selectbox("Filter by Status", ["All", "todo", "in_progress", "completed"])
    
    with col2:
        task_priority = st.selectbox("Filter by Priority", ["All", "low", "medium", "high", "urgent"])
    
    with col3:
        if st.button("Create Task"):
            st.session_state["show_create_task"] = True
    
    # Get tasks
    status_filter = None if task_status == "All" else task_status
    tasks = workflow_manager.get_user_tasks(user_id, status_filter)
    
    # Display tasks
    for task in tasks:
        with st.expander(f"{get_priority_emoji(task['priority'])} {task['title']} - {task['status']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Content:** {task.get('content_pipeline', {}).get('title', 'N/A')}")
                st.write(f"**Type:** {task['task_type']}")
                st.write(f"**Due:** {task.get('due_date', 'No due date')}")
            
            with col2:
                st.write(f"**Priority:** {task['priority']}")
                st.write(f"**Estimated:** {task.get('estimated_hours', 0)} hours")
                st.write(f"**Status:** {task['status']}")
            
            if task['description']:
                st.write(f"**Description:** {task['description']}")
            
            # Task actions
            if task['status'] != 'completed':
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("Start Task", key=f"start_{task['id']}"):
                        # Update task to in_progress
                        pass
                
                with col_b:
                    if st.button("Complete", key=f"complete_{task['id']}"):
                        workflow_manager.complete_task(task['id'])
                        st.experimental_rerun()
                
                with col_c:
                    actual_hours = st.number_input("Actual hours", key=f"hours_{task['id']}", min_value=0.0, step=0.5)

def render_calendar_tab(workflow_manager: ContentWorkflowManager, user_id: str):
    """Render content calendar"""
    
    st.subheader("Content Calendar")
    
    # Calendar view options
    col1, col2 = st.columns(2)
    with col1:
        view_type = st.selectbox("View", ["Week", "Month", "List"])
    
    with col2:
        if st.button("Schedule Content"):
            st.session_state["show_schedule_form"] = True
    
    # Get scheduled content
    pipeline_content = workflow_manager.get_content_pipeline(user_id)
    scheduled_content = [item for item in pipeline_content if item.get("scheduled_publish_date")]
    
    if view_type == "List":
        # List view
        for content in scheduled_content:
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**{content['title']}**")
                
                with col2:
                    st.write(content['platform'])
                
                with col3:
                    publish_date = content.get('scheduled_publish_date', '')
                    st.write(publish_date[:10] if publish_date else 'No date')
                
                with col4:
                    status = content['workflow_stage']
                    if status == 'published':
                        st.success("Published")
                    elif status == 'scheduled':
                        st.info("Scheduled")
                    else:
                        st.warning(f"In {status}")
                
                st.markdown("---")
    
    else:
        st.info("Calendar visualization coming soon - showing list view for now")
        # In a real implementation, you'd use a calendar component here

def render_analytics_tab(workflow_manager: ContentWorkflowManager, user_id: str):
    """Render analytics and performance tracking"""
    
    st.subheader("Content Performance Analytics")
    
    # Get content with analytics
    pipeline_content = workflow_manager.get_content_pipeline(user_id)
    published_content = [item for item in pipeline_content if item['workflow_stage'] == 'published']
    
    if not published_content:
        st.info("No published content yet. Publish some content to see analytics!")
        return
    
    # Performance overview
    col1, col2, col3 = st.columns(3)
    
    total_views = sum(item.get('content_analytics', [{}])[0].get('views', 0) for item in published_content)
    total_engagement = sum(
        item.get('content_analytics', [{}])[0].get('likes', 0) + 
        item.get('content_analytics', [{}])[0].get('comments', 0)
        for item in published_content
    )
    
    with col1:
        st.metric("Total Views", f"{total_views:,}")
    
    with col2:
        st.metric("Total Engagement", f"{total_engagement:,}")
    
    with col3:
        avg_engagement = (total_engagement / total_views * 100) if total_views > 0 else 0
        st.metric("Avg Engagement Rate", f"{avg_engagement:.1f}%")
    
    # Performance by platform
    platform_data = {}
    for content in published_content:
        platform = content['platform']
        analytics = content.get('content_analytics', [{}])[0]
        
        if platform not in platform_data:
            platform_data[platform] = {'views': 0, 'engagement': 0, 'count': 0}
        
        platform_data[platform]['views'] += analytics.get('views', 0)
        platform_data[platform]['engagement'] += analytics.get('likes', 0) + analytics.get('comments', 0)
        platform_data[platform]['count'] += 1
    
    # Create charts
    if platform_data:
        fig = px.bar(
            x=list(platform_data.keys()),
            y=[platform_data[p]['views'] for p in platform_data],
            title="Views by Platform"
        )
        st.plotly_chart(fig, use_container_width=True)

# Helper functions
def get_next_stage(current_stage: str) -> str:
    """Get the next workflow stage"""
    stages = ["idea", "outlined", "drafted", "scripted", "recorded", "edited", "reviewed", "scheduled", "published", "analyzed"]
    try:
        current_index = stages.index(current_stage)
        return stages[current_index + 1] if current_index < len(stages) - 1 else None
    except ValueError:
        return None

def get_priority_emoji(priority: str) -> str:
    """Get emoji for task priority"""
    priority_emojis = {
        "low": "🟢",
        "medium": "🟡", 
        "high": "🟠",
        "urgent": "🔴"
    }
    return priority_emojis.get(priority, "⚪")

def render_add_content_form(workflow_manager: ContentWorkflowManager, user_id: str):
    """Render form to add content to pipeline"""
    
    with st.form("add_content_form"):
        st.subheader("Add Content to Pipeline")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Content Title")
            content_type = st.selectbox("Content Type", ["video", "post", "story", "thread", "article"])
            platform = st.selectbox("Platform", ["youtube", "tiktok", "instagram", "facebook", "twitter", "linkedin"])
        
        with col2:
            scheduled_date = st.date_input("Scheduled Publish Date")
            hashtags = st.text_area("Hashtags (one per line)").split('\n')
            call_to_action = st.text_input("Call to Action")
        
        submitted = st.form_submit_button("Add to Pipeline")
        
        if submitted and title:
            content_data = {
                "title": title,
                "content_type": content_type,
                "platform": platform,
                "scheduled_date": scheduled_date.isoformat(),
                "hashtags": [tag.strip() for tag in hashtags if tag.strip()],
                "call_to_action": call_to_action
            }
            
            result = workflow_manager.add_content_to_pipeline(user_id, content_data)
            if result:
                st.success("Content added to pipeline!")
                st.session_state["show_add_content"] = False
                st.experimental_rerun()
            else:
                st.error("Failed to add content to pipeline")