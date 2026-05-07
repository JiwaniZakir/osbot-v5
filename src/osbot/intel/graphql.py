from __future__ import annotations

from typing import TYPE_CHECKING, Any

from osbot.log import get_logger

if TYPE_CHECKING:
    from osbot.types import GitHubCLIProtocol

logger = get_logger(__name__)

REPO_PROFILE_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    owner { login }
    name
    description
    primaryLanguage { name }
    stargazerCount
    pushedAt
    defaultBranchRef { name }
    licenseInfo { spdxId }
    repositoryTopics(first: 20) { nodes { topic { name } } }
    fundingLinks { url }
    codeOfConduct { name }
    hasContributing: object(expression: "HEAD:CONTRIBUTING.md") { ... on Blob { byteSize } }
    hasPrTemplate: object(expression: "HEAD:.github/PULL_REQUEST_TEMPLATE.md") { ... on Blob { byteSize } }
    gfiIssues: issues(labels: ["good first issue"], states: OPEN) { totalCount }
    helpWantedIssues: issues(labels: ["help wanted"], states: OPEN) { totalCount }
    bugIssues: issues(labels: ["bug"], states: OPEN) { totalCount }
    closedIssues: issues(states: CLOSED, first: 1) { totalCount }
    openIssues: issues(states: OPEN, first: 1) { totalCount }
    pullRequests(states: MERGED, last: 30, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        mergedAt
        author { login }
        authorAssociation
        commits(last: 1) {
          nodes {
            commit {
              statusCheckRollup { state }
            }
          }
        }
      }
    }
  }
}
"""

ISSUE_DETAIL_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      number
      title
      body
      createdAt
      updatedAt
      author { login }
      authorAssociation
      labels(first: 20) { nodes { name } }
      reactions { totalCount }
      comments { totalCount }
      assignees(first: 5) { nodes { login } }
    }
  }
}
"""

PR_COMMENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      comments(first: 50) {
        nodes {
          body
          author { login }
          authorAssociation
          createdAt
        }
      }
      reviews(first: 30) {
        nodes {
          body
          state
          author { login }
          authorAssociation
          createdAt
        }
      }
    }
  }
}
"""


class GraphQLClient:
    def __init__(self, gh: GitHubCLIProtocol) -> None:
        self._gh = gh

    async def repo_profile(self, owner: str, name: str) -> dict[str, Any]:
        result = await self._gh.graphql(REPO_PROFILE_QUERY, {"owner": owner, "name": name})
        data = result.get("data", {}).get("repository")
        if data is None:
            logger.warning("repo_profile_empty", owner=owner, name=name)
            return {}
        return data

    async def issue_detail(self, owner: str, name: str, number: int) -> dict[str, Any]:
        result = await self._gh.graphql(ISSUE_DETAIL_QUERY, {"owner": owner, "name": name, "number": str(number)})
        data = result.get("data", {}).get("repository", {}).get("issue")
        if data is None:
            logger.warning("issue_detail_empty", owner=owner, name=name, number=number)
            return {}
        return data

    async def pr_comments(self, owner: str, name: str, number: int) -> dict[str, Any]:
        result = await self._gh.graphql(PR_COMMENTS_QUERY, {"owner": owner, "name": name, "number": str(number)})
        data = result.get("data", {}).get("repository", {}).get("pullRequest")
        if data is None:
            return {}
        return data
