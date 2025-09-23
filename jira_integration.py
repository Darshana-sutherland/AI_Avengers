import os
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class JiraClient:
    def __init__(self):
        self.server = os.getenv('JIRA_SERVER')
        self.email = os.getenv('JIRA_EMAIL')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        self.client = None
        
    def connect(self):
        """Establish connection to Jira"""
        try:
            self.client = JIRA(
                server=self.server,
                basic_auth=(self.email, self.api_token)
            )
            return True, "Successfully connected to Jira"
        except Exception as e:
            return False, f"Failed to connect to Jira: {str(e)}"
    
    def create_issue(self, project_key, summary, description, issue_type="Task", **kwargs):
        """Create a new Jira issue"""
        if not self.client:
            success, message = self.connect()
            if not success:
                return None, message
                
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            # Add any additional fields provided in kwargs
            issue_dict.update(kwargs)
            
            issue = self.client.create_issue(fields=issue_dict)
            return issue, f"Successfully created issue {issue.key}"
            
        except Exception as e:
            return None, f"Failed to create issue: {str(e)}"
    
    def get_issue(self, issue_key):
        """Get a Jira issue by key"""
        if not self.client:
            success, message = self.connect()
            if not success:
                return None, message
                
        try:
            issue = self.client.issue(issue_key)
            return issue, "Successfully retrieved issue"
        except Exception as e:
            return None, f"Failed to get issue: {str(e)}"
    
    def update_issue(self, issue_key, **fields):
        """Update an existing Jira issue"""
        if not self.client:
            success, message = self.connect()
            if not success:
                return False, message
                
        try:
            issue = self.client.issue(issue_key)
            issue.update(fields=fields)
            return True, f"Successfully updated issue {issue_key}"
        except Exception as e:
            return False, f"Failed to update issue: {str(e)}"

# Example usage
if __name__ == "__main__":
    jira = JiraClient()
    success, message = jira.connect()
    print(message)
    
    if success:
        # Example: Create a new issue
        issue, msg = jira.create_issue(
            project_key="YOUR_PROJECT_KEY",
            summary="Test issue from Python",
            description="This is a test issue created from Python",
            issue_type="Task",
            priority={'name': 'High'}
        )
        print(msg)
