import os
from dotenv import load_dotenv
from jira_integration import JiraClient

# Load environment variables
load_dotenv()

def test_jira_connection():
    print("Testing Jira connection...")
    
    # Initialize Jira client
    jira = JiraClient()
    
    # Test connection
    success, message = jira.connect()
    print(message)
    
    if success:
        print("\nConnection successful! Testing issue creation...")
        
        # Test creating a test issue
        issue, msg = jira.create_issue(
            project_key="ASDFGHJKL",
            summary="Test Issue from Python",
            description="This is a test issue created to verify Jira integration.",
            issue_type="Task"
        )
        
        if issue:
            print(f"✅ Success! Created issue: {issue.key}")
            print(f"   URL: {jira.server}/browse/{issue.key}")
        else:
            print(f"❌ Failed to create issue: {msg}")
    else:
        print("❌ Failed to connect to Jira. Please check your credentials in the .env file.")
        print("   Make sure you have set JIRA_SERVER, JIRA_EMAIL, and JIRA_API_TOKEN.")

if __name__ == "__main__":
    test_jira_connection()
