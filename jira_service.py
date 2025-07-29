import logging
from typing import List, Optional
import requests
from requests.auth import HTTPBasicAuth

from jira_config import JiraConfig
from jira_models import JiraTicket, Fields, Status, Priority, IssueType, User


logger = logging.getLogger(__name__)


class JiraService:
    def __init__(self, config: JiraConfig):
        self.config = config
        self.base_url = f"{config.base_url}/rest/api/2"
        self.auth = HTTPBasicAuth(config.username, config.api_token)
        self.headers = {"Content-Type": "application/json"}
    
    def get_ticket(self, ticket_key: str) -> JiraTicket:
        """Retrieves details of a specific Jira ticket by its key"""
        if not ticket_key or not ticket_key.strip():
            raise ValueError("ticket_key is required")
        
        url = f"{self.base_url}/issue/{ticket_key}"
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            timeout=self.config.timeout_seconds
        )
        response.raise_for_status()
        
        return self._parse_ticket(response.json())
    
    def search_tickets(self, jql_query: str, max_results: Optional[int] = None) -> List[JiraTicket]:
        """Searches for Jira tickets matching the given JQL query"""
        logger.info(f"Searching for tickets with JQL: {jql_query}")
        
        if not jql_query or not jql_query.strip():
            raise ValueError("jql_query is required")
        
        limit = max_results if max_results is not None else 50
        
        url = f"{self.base_url}/search"
        params = {
            "jql": jql_query,
            "maxResults": limit
        }
        
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params=params,
            timeout=self.config.timeout_seconds
        )
        response.raise_for_status()
        
        data = response.json()
        tickets = [self._parse_ticket(issue) for issue in data.get("issues", [])]
        
        logger.info(f"Found {len(tickets)} tickets")
        return tickets
    
    def search_tickets_by_text(self, text: str, max_results: Optional[int] = None) -> List[JiraTicket]:
        """Searches for Jira tickets containing specific text"""
        logger.info(f"Searching for tickets containing text: {text}")
        
        if not text or not text.strip():
            raise ValueError("text is required")
        
        jql = f'text ~ "{text}" ORDER BY updated DESC'
        return self.search_tickets(jql, max_results)
    
    def get_tickets_by_project(self, project_key: str, max_results: Optional[int] = None) -> List[JiraTicket]:
        """Gets all tickets for a specific Jira project"""
        logger.info(f"Getting tickets for project: {project_key}")
        
        if not project_key or not project_key.strip():
            raise ValueError("project_key is required")
        
        jql = f"project = {project_key} ORDER BY updated DESC"
        return self.search_tickets(jql, max_results)
    
    def get_my_assigned_tickets(self, max_results: Optional[int] = None) -> List[JiraTicket]:
        """Gets all Jira tickets assigned to the current user"""
        logger.info("Getting my assigned tickets")
        
        jql = "assignee = currentUser() ORDER BY updated DESC"
        return self.search_tickets(jql, max_results)
    
    def get_recently_updated_tickets(self, max_results: Optional[int] = None) -> List[JiraTicket]:
        """Gets recently updated Jira tickets from the last 7 days"""
        logger.info("Getting recently updated tickets")
        
        jql = "updated >= -7d ORDER BY updated DESC"
        return self.search_tickets(jql, max_results)
    
    def get_available_transitions(self, ticket_key: str) -> List[dict]:
        """Get available status transitions for a ticket"""
        if not ticket_key or not ticket_key.strip():
            raise ValueError("ticket_key is required")
        
        url = f"{self.base_url}/issue/{ticket_key}/transitions"
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            timeout=self.config.timeout_seconds
        )
        response.raise_for_status()
        
        data = response.json()
        transitions = []
        for transition in data.get("transitions", []):
            transitions.append({
                "id": transition.get("id"),
                "name": transition.get("name"),
                "to": {
                    "name": transition.get("to", {}).get("name"),
                    "description": transition.get("to", {}).get("description")
                }
            })
        return transitions
    
    def change_ticket_status(self, ticket_key: str, status_name: str) -> dict:
        """Change the status of a Jira ticket"""
        logger.info(f"Changing status of ticket {ticket_key} to {status_name}")
        
        if not ticket_key or not ticket_key.strip():
            raise ValueError("ticket_key is required")
        if not status_name or not status_name.strip():
            raise ValueError("status_name is required")
        
        # First, get available transitions
        transitions = self.get_available_transitions(ticket_key)
        
        # Find the transition that matches the desired status
        target_transition = None
        for transition in transitions:
            if (transition["to"]["name"].lower() == status_name.lower() or 
                transition["name"].lower() == status_name.lower()):
                target_transition = transition
                break
        
        if not target_transition:
            available_statuses = [t["to"]["name"] for t in transitions]
            available_transitions = [t["name"] for t in transitions]
            raise ValueError(
                f"Status '{status_name}' not available for ticket {ticket_key}. "
                f"Available statuses: {available_statuses}. "
                f"Available transitions: {available_transitions}"
            )
        
        # Perform the transition
        url = f"{self.base_url}/issue/{ticket_key}/transitions"
        payload = {
            "transition": {
                "id": target_transition["id"]
            }
        }
        
        response = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=payload,
            timeout=self.config.timeout_seconds
        )
        
        if response.status_code == 204:
            logger.info(f"Successfully changed status of {ticket_key} to {status_name}")
            # Get updated ticket info
            updated_ticket = self.get_ticket(ticket_key)
            return {
                "success": True,
                "message": f"Status changed to {status_name}",
                "ticket": {
                    "key": updated_ticket.key,
                    "status": updated_ticket.fields.status.name if updated_ticket.fields and updated_ticket.fields.status else None,
                    "summary": updated_ticket.fields.summary if updated_ticket.fields else None
                }
            }
        else:
            response.raise_for_status()
            return {"success": False, "message": "Unknown error occurred"}
    
    def _parse_ticket(self, data: dict) -> JiraTicket:
        """Parse JSON response into JiraTicket object"""
        fields_data = data.get("fields", {})
        
        # Parse nested objects
        status = None
        if fields_data.get("status"):
            status = Status(
                name=fields_data["status"].get("name"),
                description=fields_data["status"].get("description")
            )
        
        priority = None
        if fields_data.get("priority"):
            priority = Priority(name=fields_data["priority"].get("name"))
        
        issuetype = None
        if fields_data.get("issuetype"):
            issuetype = IssueType(
                name=fields_data["issuetype"].get("name"),
                description=fields_data["issuetype"].get("description")
            )
        
        assignee = None
        if fields_data.get("assignee"):
            assignee = User(
                display_name=fields_data["assignee"].get("displayName"),
                email_address=fields_data["assignee"].get("emailAddress")
            )
        
        reporter = None
        if fields_data.get("reporter"):
            reporter = User(
                display_name=fields_data["reporter"].get("displayName"),
                email_address=fields_data["reporter"].get("emailAddress")
            )
        
        fields = Fields(
            summary=fields_data.get("summary"),
            description=fields_data.get("description"),
            status=status,
            priority=priority,
            issuetype=issuetype,
            assignee=assignee,
            reporter=reporter,
            created=fields_data.get("created"),
            updated=fields_data.get("updated")
        )
        
        return JiraTicket(
            id=data.get("id"),
            key=data.get("key"),
            self=data.get("self"),
            fields=fields
        )