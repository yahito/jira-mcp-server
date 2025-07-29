#!/usr/bin/env python3
import logging
from jira_config import JiraConfig
from jira_service import JiraService


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Jira MCP Server")
    
    # Initialize configuration and service
    config = JiraConfig()
    jira_service = JiraService(config)
    
    # Example usage
    try:
        # Get recent tickets
        recent_tickets = jira_service.get_recently_updated_tickets(5)
        logger.info(f"Found {len(recent_tickets)} recent tickets")
        
        for ticket in recent_tickets:
            logger.info(f"Ticket: {ticket.key} - {ticket.fields.summary if ticket.fields else 'No summary'}")
        
        # Get assigned tickets
        assigned_tickets = jira_service.get_my_assigned_tickets(5)
        logger.info(f"Found {len(assigned_tickets)} assigned tickets")
        
    except Exception as e:
        logger.error(f"Error accessing Jira: {e}")


if __name__ == "__main__":
    main()