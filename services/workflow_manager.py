from datetime import datetime, timedelta
from typing import List, Dict, Optional
import streamlit as st
from supabase import Client

class ContentWorkflowManager:
    """Manages content creation workflows and tasks with Supabase backend"""
    
    def __init__(self, supabase_client: Client):
        """Initialize with Supabase client"""
        self.client = supabase_client
        
    def get_workflows(self, user_id: str) -> List[Dict]:
        """Get all workflows for a user"""
        try:
            response = self.client.table('workflows')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"Error fetching workflows: {str(e)}")
            return []
    
    def create_workflow(self, user_id: str, title: str, content_type: str, 
                       platforms: List[str], target_date: datetime) -> Optional[Dict]:
        """Create a new workflow"""
        try:
            workflow_data = {
                'user_id': user_id,
                'title': title,
                'content_type': content_type,
                'platforms': platforms,
                'target_date': target_date.isoformat(),
                'status': 'planned'
            }
            
            response = self.client.table('workflows')\
                .insert(workflow_data)\
                .execute()
            
            if response.data:
                # Create default tasks for the workflow
                self._create_default_tasks(response.data[0]['id'], content_type)
                return response.data[0]
            return None
            
        except Exception as e:
            st.error(f"Error creating workflow: {str(e)}")
            return None
    
    def update_workflow_status(self, workflow_id: str, status: str) -> bool:
        """Update workflow status"""
        try:
            response = self.client.table('workflows')\
                .update({
                    'status': status,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', workflow_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            st.error(f"Error updating workflow: {str(e)}")
            return False
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            response = self.client.table('workflows')\
                .delete()\
                .eq('id', workflow_id)\
                .execute()
            return True
        except Exception as e:
            st.error(f"Error deleting workflow: {str(e)}")
            return False
    
    def get_workflow_tasks(self, workflow_id: str) -> List[Dict]:
        """Get all tasks for a workflow"""
        try:
            response = self.client.table('workflow_tasks')\
                .select('*')\
                .eq('workflow_id', workflow_id)\
                .order('order_index')\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            st.error(f"Error fetching tasks: {str(e)}")
            return []
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        try:
            update_data = {'status': status}
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
                
            response = self.client.table('workflow_tasks')\
                .update(update_data)\
                .eq('id', task_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            st.error(f"Error updating task: {str(e)}")
            return False
    
    def _create_default_tasks(self, workflow_id: str, content_type: str):
        """Create default tasks based on content type"""
        task_templates = {
            'Blog Post': [
                'Research topic and keywords',
                'Create outline',
                'Write first draft',
                'Edit and revise',
                'Add images/media',
                'SEO optimization',
                'Final review',
                'Publish'
            ],
            'Video Script': [
                'Define video concept',
                'Research and gather information',
                'Write script outline',
                'Write full script',
                'Review and edit',
                'Create shot list',
                'Finalize script'
            ],
            'Social Media Campaign': [
                'Define campaign goals',
                'Research target audience',
                'Create content calendar',
                'Design visuals',
                'Write captions',
                'Schedule posts',
                'Monitor engagement'
            ],
            'Podcast Episode': [
                'Choose episode topic',
                'Research and prep',
                'Create episode outline',
                'Write intro/outro',
                'Record episode',
                'Edit audio',
                'Create show notes',
                'Publish and promote'
            ],
            'Newsletter': [
                'Plan newsletter content',
                'Write main article',
                'Add supplementary content',
                'Design layout',
                'Proofread',
                'Test email',
                'Schedule send'
            ]
        }
        
        tasks = task_templates.get(content_type, ['Plan content', 'Create content', 'Review', 'Publish'])
        
        try:
            for index, task_title in enumerate(tasks):
                self.client.table('workflow_tasks').insert({
                    'workflow_id': workflow_id,
                    'title': task_title,
                    'order_index': index,
                    'status': 'pending'
                }).execute()
        except Exception as e:
            st.warning(f"Could not create default tasks: {str(e)}")
    
    def get_analytics(self, user_id: str) -> Dict:
        """Get workflow analytics for a user"""
        try:
            workflows = self.get_workflows(user_id)
            
            total = len(workflows)
            completed = len([w for w in workflows if w.get('status') == 'published'])
            in_progress = len([w for w in workflows if w.get('status') == 'in_progress'])
            planned = len([w for w in workflows if w.get('status') == 'planned'])
            
            # Platform distribution
            platform_counts = {}
            for workflow in workflows:
                for platform in workflow.get('platforms', []):
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            # Content type distribution
            content_type_counts = {}
            for workflow in workflows:
                content_type = workflow.get('content_type', 'Unknown')
                content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
            
            return {
                'total': total,
                'completed': completed,
                'in_progress': in_progress,
                'planned': planned,
                'completion_rate': (completed / total * 100) if total > 0 else 0,
                'platform_distribution': platform_counts,
                'content_type_distribution': content_type_counts
            }
            
        except Exception as e:
            st.error(f"Error getting analytics: {str(e)}")
            return {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'planned': 0,
                'completion_rate': 0,
                'platform_distribution': {},
                'content_type_distribution': {}
            }
