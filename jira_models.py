from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    display_name: Optional[str] = None
    email_address: Optional[str] = None


@dataclass
class Status:
    name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Priority:
    name: Optional[str] = None


@dataclass
class IssueType:
    name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Fields:
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    issuetype: Optional[IssueType] = None
    assignee: Optional[User] = None
    reporter: Optional[User] = None
    created: Optional[str] = None
    updated: Optional[str] = None


@dataclass
class JiraTicket:
    id: Optional[str] = None
    key: Optional[str] = None
    self: Optional[str] = None
    fields: Optional[Fields] = None