# Create your models here.
import datetime
import uuid
from abc import ABC, abstractmethod
from typing import override


class BaseEntity(ABC):
    """Common interface and serialization helpers for model entities."""

    @abstractmethod
    def validate(self):
        """Raise an error when the entity's data is invalid."""
        pass

    def to_dict(self):
        """Return the entity's instance fields as a dictionary."""
        return {
            key: value for key, value in self.__dict__.items()
        }


class Reporter(BaseEntity):
    """Represent the person or team that reported an issue."""

    def __init__(self, name, email, team):
        """Initialize a reporter with an ID, name, email and team."""
        self.id = str(uuid.uuid4())  # Unique identifier for this reporter.
        self.name = name  # Reporter's display name.
        self.email = email  # Reporter's contact email address.
        self.team = team  # Team the reporter belongs to.

    @override
    def validate(self):
        """Ensure the reporter has a name and a valid-looking email."""
        if not self.name:
            raise ValueError('Name cannot be None or Empty')
        if '@' not in self.email:
            raise ValueError('Invalid Email')


class Issue(BaseEntity):
    """Represent an issue and its reporting, status, and priority details."""

    STATUS = ["open", "in_progress", "resolved", "closed"]  # Allowed issue states.
    PRIORITY = ["low", "medium", "high", "critical"]  # Allowed issue priorities.
    def __init__(self, title, description, status, priority, reporter_id,
                 created_at=None):
        """Initialize an issue, optionally with its creation timestamp."""
        self.id = str(uuid.uuid4())  # Unique identifier for this issue.
        self.title = title  # Short summary of the issue.
        self.description = description  # Detailed explanation of the issue.
        self.status = status  # Current state; must be one of STATUS.
        self.priority = priority  # Urgency level; must be one of PRIORITY.
        self.reporter_id = reporter_id  # ID of the reporter who filed the issue.
        self.created_at = created_at  # Timestamp when the issue was created.
        self._message = ""  # Stored privately; exposed as `message` in the public API and JSON.

    def set_message(self, message: str) -> None:
        """Set the issue's message."""
        self._message = message

    @property
    def message(self) -> str:
        """Return the issue's message."""
        return self._message

    @override
    def to_dict(self):
        """Return issue fields using the public message name."""
        data = super().to_dict()
        data["message"] = data.pop("_message")
        return data

    @override
    def validate(self):
        """Ensure the issue has a title and allowed status and priority."""
        if not self.title:
            raise ValueError('Title cannot be None or Empty')

        if self.status not in self.STATUS:
            raise ValueError('Invalid Status')

        if self.priority not in self.PRIORITY:
            raise ValueError('Invalid Priority')

    def describe(self):
        """Return a compact summary containing the title and priority."""
        return f"{self.title} - [{self.priority}]"


class CriticalIssue(Issue):
    """Represent an issue that needs urgent attention."""

    @override
    def describe(self):
        """Return an urgent review message for this issue."""
        return f"[URGENT] {self.title} - need immediate review"


class LowPriorityIssue(Issue):
    """Represent an issue that can be handled when time permits."""

    @override
    def describe(self):
        """Return a low-priority handling message for this issue."""
        return f"[LOW] {self.title} - low priority, handle when free"


class IssueFactory:
    @staticmethod
    def crater_issue(data):
        """Return a crater issue."""

        if data["priority"] == "critical":
            issue = CriticalIssue(data['title'], data['description'], data['status'], data["priority"],
                                  data['reporter_id'], str(datetime.datetime.now()))
        elif data["priority"] == "low":
            issue = LowPriorityIssue(data['title'], data['description'], data['status'], data["priority"],
                                     data['reporter_id'], str(datetime.datetime.now()))
        else:
            issue = Issue(data['title'], data['description'], data['status'], data['priority'],
                          data['reporter_id'], str(datetime.datetime.now()))

        issue.set_message(issue.describe())
        return issue
