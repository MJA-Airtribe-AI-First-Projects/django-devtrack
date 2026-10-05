# Create your views here.
import json
from json import JSONDecodeError
from typing import override, Any, List

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from issues.models import Reporter, IssueFactory

FILES_REPORTER_JSON = 'issues/files/reporters.json'
FILES_ISSUES_JSON = 'issues/files/issues.json'


## Reporter APIs ##
class ReporterView(APIView):
    """Handle API requests for listing, retrieving, and creating reporters."""

    @staticmethod
    def get_all_reporters() -> List[Any]:
        """Load reporters from the JSON file, returning an empty list if unavailable."""
        try:
            with open(FILES_REPORTER_JSON, 'r') as f:
                reporters = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            reporters = []

        return reporters

    @staticmethod
    def get_reporter_by_id(reporters: List[Any], reporter_id) -> Any | None:
        """Return the reporter with the given ID, or None when it is absent."""
        for reporter in reporters:
            if reporter['id'] == reporter_id:
                return reporter
        return None

    @override
    def get(self, request, id=None) -> Response:
        """Return all reporters or the reporter matching the optional ID."""
        reporters = self.get_all_reporters()

        if id is None:
            return Response({"reporters": reporters}, status=status.HTTP_200_OK)

        reporter = self.get_reporter_by_id(reporters, id)
        if reporter is not None:
            return Response({"reporter": reporter}, status=status.HTTP_200_OK)

        return Response({"error": "Reporter not found"}, status=status.HTTP_404_NOT_FOUND)

    @override
    def post(self, request) -> Response:
        """Validate and save a reporter submitted in the request body."""
        try:
            data = request.data
            reporter = Reporter(data['name'], data['email'], data['team'])
            reporter.validate()  # Reject incomplete or invalid reporter details.

            reporters = self.get_all_reporters()
            if self.get_reporter_by_id(reporters, reporter.id) is not None:
                return Response(
                    {"error": f"Reporter with id {reporter.id} already exists"},
                    status=status.HTTP_409_CONFLICT,
                )

            reporter_dict = reporter.to_dict()  # Convert the reporter to JSON-ready fields.

            with open(FILES_REPORTER_JSON, 'w') as f:
                reporters.append(reporter_dict)

                json.dump(reporters, f, indent=4)

            return Response({"reporter": reporter_dict}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (FileNotFoundError, JSONDecodeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing field: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


## Issues APIs ##
class IssueView(APIView):
    """Handle API requests for listing, retrieving, and creating issues."""

    @staticmethod
    def __get_all_issues() -> List[Any]:
        """Load issues from the JSON file, returning an empty list if unavailable."""
        try:
            with open(FILES_ISSUES_JSON, 'r') as f:
                issues = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            issues = []

        return issues

    @staticmethod
    def __get_issue_by_id(issues: List[Any], issue_id) -> Any | None:
        """Return the issue with the given ID, or None when it is absent."""
        for issue in issues:
            if issue['id'] == issue_id:
                return issue
        return None

    @staticmethod
    def __filter_issues(field_name: str, value: Any) -> List[Any]:
        """Return stored issues whose named field equals the supplied value."""
        issues = IssueView.__get_all_issues()
        return [issue for issue in issues if issue.get(field_name) == value]

    @override
    def get(self, request, id=None) -> Response:
        """Return an issue by ID, filter issues, or list all issues."""
        # An ID in the URL requests a single issue.
        if id is not None:
            issues = self.__get_all_issues()
            issue = self.__get_issue_by_id(issues, id)
            if issue is None:
                return Response({"error": "Issue not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"issue": issue}, status=status.HTTP_200_OK)

        # Filter by priority when a search query parameter is present.
        filter_value = request.query_params.get("search")
        if filter_value is not None:
            filtered_issues = self.__filter_issues("priority", filter_value)
            return Response({"issues": filtered_issues}, status=status.HTTP_200_OK)

        # With no ID or filter, return the full issue list.
        issues = self.__get_all_issues()
        return Response({"issues": issues}, status=status.HTTP_200_OK)

    @override
    def post(self, request) -> Response:
        """Validate and save a new issue submitted in the request body."""
        try:
            data = request.data
            issue = IssueFactory.crater_issue(data)
            issue.validate()  # Reject issues with missing or unsupported values.

            reporter = ReporterView.get_reporter_by_id(ReporterView.get_all_reporters(), issue.reporter_id)
            if reporter is None:
                return Response({"error": "Reporter not found"}, status=status.HTTP_404_NOT_FOUND)

            issues = self.__get_all_issues()
            if self.__get_issue_by_id(issues, issue.id) is not None:
                return Response(
                    {"error": f"Issue with id {issue.id} already exists"},
                    status=status.HTTP_409_CONFLICT,
                )

            issue_dict = issue.to_dict()  # Convert the issue to JSON-ready fields.

            with open(FILES_ISSUES_JSON, 'w') as f:
                issues.append(issue_dict)
                json.dump(issues, f, indent=4)

            return Response({"issue": issue_dict}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (FileNotFoundError, JSONDecodeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response({"error": f"Missing field: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
