#!/usr/bin/env python3
"""
GitLab User Activity Fetcher

Fetches issues and merge requests created by specified users.
Supports caching, verbose output, and PAT authentication.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

# Set up logger
logger = logging.getLogger(__name__)

# Default GitLab Personal Access Token (set here or use --token or GITLAB_TOKEN env var)
DEFAULT_TOKEN = None # e.g., "glpat-xxxxxxxxxxxxxxxxxxxx"

# Default usernames to query if none provided
DEFAULT_USERNAMES = [
    "amurdaca",
    "djachimo",
    "jbenc",
    "kgiusti",
    "mcattamo",
    "mmartinv",
    "pwhalen",
    "sarmahaj",
    "saypaul",
    "yih1",
]


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="  [%(levelname)s] %(message)s"
    )


class GitLabAPI:
    """Simple GitLab API client with caching."""

    def __init__(self, base_url: str, token: str, cache_dir: str = ".cache",
                 use_cache: bool = True):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.cache_dir = Path(cache_dir)
        self.use_cache = use_cache
        self.session = requests.Session()
        self.session.headers.update({
            'PRIVATE-TOKEN': token,
            'Content-Type': 'application/json'
        })

        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, cache_key: str) -> Path:
        """Generate cache file path."""
        safe_key = cache_key.replace('/', '_').replace('?', '_')
        return self.cache_dir / f"{safe_key}.json"

    def _read_cache(self, cache_key: str) -> Optional[Dict]:
        """Read from cache if exists and caching is enabled."""
        if not self.use_cache:
            logger.debug("Cache BYPASSED: %s", cache_key)
            return None
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            logger.debug("Cache HIT: %s", cache_key)
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        logger.debug("Cache MISS: %s", cache_key)
        return None

    def _write_cache(self, cache_key: str, data: Dict):
        """Write to cache."""
        cache_path = self._get_cache_path(cache_key)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.debug("Cached: %s", cache_key)

    def _make_request(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Make API request with pagination."""
        url = urljoin(f"{self.base_url}/api/v4/", endpoint)
        all_results = []
        page = 1
        per_page = 100

        if params is None:
            params = {}
        params['per_page'] = per_page

        while True:
            params['page'] = page
            logger.debug("GET %s (page %d)", endpoint, page)

            response = self.session.get(url, params=params)
            response.raise_for_status()

            results = response.json()
            if not results:
                break

            all_results.extend(results)

            # Check if there are more pages
            if 'x-next-page' not in response.headers or not response.headers['x-next-page']:
                break

            page += 1

        logger.debug("Retrieved %d items from %s", len(all_results), endpoint)
        return all_results

    def get_user_id(self, username: str) -> Optional[int]:
        """Get user ID from username."""
        cache_key = f"user_{username}"
        cached = self._read_cache(cache_key)

        if cached:
            return cached.get('id')

        try:
            users = self._make_request('users', {'username': username})
            if users:
                user_data = users[0]
                self._write_cache(cache_key, user_data)
                return user_data['id']
        except requests.exceptions.RequestException as e:
            logger.debug("Error fetching user %s: %s", username, e)

        return None

    def get_user_issues(self, username: str, year: int) -> List[Dict]:
        """Get issues created by user in a specific year."""
        cache_key = f"issues_{username}_{year}"
        cached = self._read_cache(cache_key)

        if cached:
            return cached

        try:
            issues = self._make_request('issues', {
                'author_username': username,
                'scope': 'all',
                'created_after': f"{year}-01-01T00:00:00Z",
                'created_before': f"{year}-12-31T23:59:59Z"
            })
            self._write_cache(cache_key, issues)
            return issues
        except requests.exceptions.RequestException as e:
            logger.debug("Error fetching issues for %s: %s", username, e)
            return []

    def get_user_merge_requests(self, username: str, year: int) -> List[Dict]:
        """Get merge requests created by user in a specific year."""
        cache_key = f"mrs_{username}_{year}"
        cached = self._read_cache(cache_key)

        if cached:
            return cached

        try:
            mrs = self._make_request('merge_requests', {
                'author_username': username,
                'scope': 'all',
                'created_after': f"{year}-01-01T00:00:00Z",
                'created_before': f"{year}-12-31T23:59:59Z"
            })
            self._write_cache(cache_key, mrs)
            return mrs
        except requests.exceptions.RequestException as e:
            logger.debug("Error fetching MRs for %s: %s", username, e)
            return []

    def get_user_mr_stats(self, username: str, year: int) -> Dict:
        """
        Get MR statistics for a user in a specific year.

        Returns:
            Dictionary with username, opened count, merged count, and status
        """
        try:
            mrs = self.get_user_merge_requests(username, year)

            # Count by state
            total = len(mrs)
            merged = sum(1 for mr in mrs if mr.get('state') == 'merged')

            return {
                'username': username,
                'opened': total,
                'merged': merged,
                'status': 'success'
            }
        except requests.exceptions.RequestException as e:
            logger.debug("Error getting MR stats for %s: %s", username, e)
            return {
                'username': username,
                'opened': 0,
                'merged': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_user_issue_stats(self, username: str, year: int) -> Dict:
        """
        Get issue statistics for a user in a specific year.

        Returns:
            Dictionary with username, issue count, and status
        """
        try:
            issues = self.get_user_issues(username, year)

            return {
                'username': username,
                'issue_count': len(issues),
                'status': 'success'
            }
        except requests.exceptions.RequestException as e:
            logger.debug("Error getting issue stats for %s: %s", username, e)
            return {
                'username': username,
                'issue_count': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_user_events(self, user_id: int, year: int, action: Optional[str] = None) -> List[Dict]:
        """
        Get events for a user in a specific year.

        Args:
            user_id: GitLab user ID
            year: Year to filter events
            action: Optional action filter (e.g., 'pushed', 'commented', 'opened')

        Returns:
            List of event dictionaries
        """
        action_suffix = f"_{action}" if action else ""
        cache_key = f"events_{user_id}_{year}{action_suffix}"
        cached = self._read_cache(cache_key)

        if cached:
            return cached

        try:
            params = {
                'after': f"{year}-01-01",
                'before': f"{year+1}-01-01"
            }
            if action:
                params['action'] = action

            events = self._make_request(f'users/{user_id}/events', params)
            self._write_cache(cache_key, events)
            return events
        except requests.exceptions.RequestException as e:
            logger.debug("Error fetching events for user %d: %s", user_id, e)
            return []

    def get_user_commit_stats(self, username: str, year: int) -> Dict:
        """
        Get commit statistics for a user in a specific year.

        Uses the Events API with action=pushed filter to count commits.

        Returns:
            Dictionary with username, commit count, and status
        """
        try:
            # First get the user ID
            user_id = self.get_user_id(username)
            if not user_id:
                return {
                    'username': username,
                    'commit_count': 0,
                    'status': 'error',
                    'error': 'User not found'
                }

            # Fetch push events for the user (using action=pushed filter)
            events = self.get_user_events(user_id, year, action='pushed')

            # Count commits from push events
            # push_data contains the commit count for each push
            commit_count = 0
            for event in events:
                push_data = event.get('push_data', {})
                commit_count += push_data.get('commit_count', 0)

            logger.debug("User %s: %d commits from %d push events",
                        username, commit_count, len(events))

            return {
                'username': username,
                'commit_count': commit_count,
                'status': 'success'
            }
        except requests.exceptions.RequestException as e:
            logger.debug("Error getting commit stats for %s: %s", username, e)
            return {
                'username': username,
                'commit_count': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_user_comment_stats(self, username: str, year: int) -> Dict:
        """
        Get comment statistics for a user in a specific year.

        Uses the Events API with action=commented filter to count comments.

        Returns:
            Dictionary with username, issues_commented, mrs_commented, and status
        """
        try:
            # First get the user ID
            user_id = self.get_user_id(username)
            if not user_id:
                return {
                    'username': username,
                    'issues_commented': 0,
                    'mrs_commented': 0,
                    'status': 'error',
                    'error': 'User not found'
                }

            # Fetch comment events (action=commented returns only comment events)
            events = self.get_user_events(user_id, year, action='commented')

            # Count by noteable_type: Issue, MergeRequest, or Commit
            issues_commented = sum(1 for e in events if e.get('note', {}).get('noteable_type') == 'Issue')
            mrs_commented = sum(1 for e in events if e.get('note', {}).get('noteable_type') == 'MergeRequest')

            return {
                'username': username,
                'issues_commented': issues_commented,
                'mrs_commented': mrs_commented,
                'status': 'success'
            }
        except requests.exceptions.RequestException as e:
            logger.debug("Error getting comment stats for %s: %s", username, e)
            return {
                'username': username,
                'issues_commented': 0,
                'mrs_commented': 0,
                'status': 'error',
                'error': str(e)
            }


def format_item(item: Dict, item_type: str) -> str:
    """Format issue or MR for display."""
    state = item.get('state', 'unknown')
    title = item.get('title', 'No title')
    web_url = item.get('web_url', '')
    created_at = item.get('created_at', '')[:10]  # Just date

    return f"  [{state}] {title}\n    {web_url} (created: {created_at})"


def print_issue_summary(results: List[Dict]):
    """Print summary for issue statistics."""
    print("\n" + "="*50)
    print("ISSUE SUMMARY")
    print("="*50)

    for result in results:
        if result['status'] == 'success':
            print(f"{result['username']:20} {result['issue_count']:6} issues")
        else:
            print(f"{result['username']:20} ERROR")

    total = sum(r['issue_count'] for r in results if r['status'] == 'success')
    print(f"\n{'Total':20} {total:6} issues")


def print_mr_summary(results: List[Dict]):
    """Print summary for MR statistics."""
    print("\n" + "="*70)
    print("MERGE REQUEST SUMMARY")
    print("="*70)
    print(f"{'Username':<20} {'Opened':>10} {'Merged':>10} {'Merge Rate':>15}")
    print("-"*70)

    for result in results:
        if result['status'] == 'success':
            opened = result['opened']
            merged = result['merged']
            merge_rate = f"{(merged/opened*100):.1f}%" if opened > 0 else "N/A"
            print(f"{result['username']:<20} {opened:>10} {merged:>10} {merge_rate:>15}")
        else:
            print(f"{result['username']:<20} {'ERROR':>10} {'ERROR':>10} {'ERROR':>15}")

    print("-"*70)
    total_opened = sum(r['opened'] for r in results if r['status'] == 'success')
    total_merged = sum(r['merged'] for r in results if r['status'] == 'success')
    overall_rate = f"{(total_merged/total_opened*100):.1f}%" if total_opened > 0 else "N/A"
    print(f"{'Total':<20} {total_opened:>10} {total_merged:>10} {overall_rate:>15}")


def print_commits_summary(results: List[Dict]):
    """Print summary for commit statistics."""
    print("\n" + "="*50)
    print("COMMIT SUMMARY")
    print("="*50)

    for result in results:
        if result['status'] == 'success':
            print(f"{result['username']:20} {result['commit_count']:6} commits")
        else:
            print(f"{result['username']:20} ERROR")

    total = sum(r['commit_count'] for r in results if r['status'] == 'success')
    print(f"\n{'Total':20} {total:6} commits")


def print_comments_summary(results: List[Dict]):
    """Print summary for comment statistics."""
    print("\n" + "="*70)
    print("COMMENT SUMMARY")
    print("="*70)
    print(f"{'Username':<20} {'Issues':>12} {'MRs':>12} {'Total':>12}")
    print("-"*70)

    for result in results:
        if result['status'] == 'success':
            issues = result['issues_commented']
            mrs = result['mrs_commented']
            total = issues + mrs
            print(f"{result['username']:<20} {issues:>12} {mrs:>12} {total:>12}")
        else:
            print(f"{result['username']:<20} {'ERROR':>12} {'ERROR':>12} {'ERROR':>12}")

    print("-"*70)
    total_issues = sum(r['issues_commented'] for r in results if r['status'] == 'success')
    total_mrs = sum(r['mrs_commented'] for r in results if r['status'] == 'success')
    print(f"{'Total':<20} {total_issues:>12} {total_mrs:>12} {total_issues + total_mrs:>12}")


def fetch_user_stats(api: GitLabAPI, usernames: List[str], year: int,
                     fetch_func: Callable, format_success: Callable[[Dict], str]) -> List[Dict]:
    """
    Fetch statistics for a list of users using the provided fetch function.

    Args:
        api: GitLabAPI instance
        usernames: List of GitLab usernames
        year: Year to query
        fetch_func: Method to call for each user (signature: func(username, year) -> dict)
        format_success: Function to format success message (signature: func(result) -> str)

    Returns:
        List of result dictionaries
    """
    results = []

    for username in usernames:
        # Verify user exists
        user_id = api.get_user_id(username)
        if not user_id:
            print(f"Querying {username}... ✗ User not found")
            # Return error result with appropriate fields based on fetch_func
            func_name = fetch_func.__name__
            if 'issue_stats' in func_name:
                results.append({
                    'username': username,
                    'issue_count': 0,
                    'status': 'error',
                    'error': 'User not found'
                })
            elif 'commit' in func_name:
                results.append({
                    'username': username,
                    'commit_count': 0,
                    'status': 'error',
                    'error': 'User not found'
                })
            elif 'comment' in func_name:
                results.append({
                    'username': username,
                    'issues_commented': 0,
                    'mrs_commented': 0,
                    'status': 'error',
                    'error': 'User not found'
                })
            else:
                results.append({
                    'username': username,
                    'opened': 0,
                    'merged': 0,
                    'status': 'error',
                    'error': 'User not found'
                })
            continue

        # Fetch stats
        print(f"Querying {username}...", end=' ')
        result = fetch_func(username, year)
        results.append(result)

        if result['status'] == 'success':
            print(f"✓ {format_success(result)}")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Fetch GitLab user activity (issues and merge requests)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s user1 user2 user3
  %(prog)s --token $GITLAB_TOKEN user1
  %(prog)s --verbose --clear-cache user1
  %(prog)s --gitlab-url https://gitlab.example.com user1
        """
    )

    parser.add_argument('usernames', nargs='*', help='GitLab usernames to query (uses defaults if not provided)')
    parser.add_argument('--token', '-t',
                        default=os.environ.get('GITLAB_TOKEN'),
                        help='GitLab Personal Access Token (or set GITLAB_TOKEN env var)')
    parser.add_argument('--gitlab-url', '-u',
                        default='https://gitlab.com',
                        help='GitLab instance URL (default: https://gitlab.com)')
    parser.add_argument('--cache-dir', '-c',
                        default='.gitlab_cache',
                        help='Cache directory (default: .gitlab_cache)')
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Show verbose output including API calls')
    parser.add_argument('--clear-cache',
                        action='store_true',
                        help='Clear cache before running')
    parser.add_argument('--no-cache',
                        action='store_true',
                        help='Bypass cache and fetch fresh data from API')
    parser.add_argument('--year', '-y',
                        type=int,
                        default=2025,
                        help='Year to query (default: 2025)')

    args = parser.parse_args()

    # Set up logging based on verbosity
    setup_logging(args.verbose)

    # Resolve token (priority: --token > GITLAB_TOKEN env > DEFAULT_TOKEN)
    token = args.token or DEFAULT_TOKEN
    if not token:
        print("Error: GitLab token required.")
        print("Provide via --token, GITLAB_TOKEN env var, or set DEFAULT_TOKEN in script.")
        sys.exit(1)

    # Clear cache if requested
    if args.clear_cache:
        cache_path = Path(args.cache_dir)
        if cache_path.exists():
            import shutil
            shutil.rmtree(cache_path)
            print(f"Cleared cache directory: {cache_path}")

    # Use default usernames if none provided
    usernames = args.usernames if args.usernames else DEFAULT_USERNAMES
    if not usernames:
        print("Error: No usernames provided and no defaults configured.")
        print("Either provide usernames as arguments or add them to DEFAULT_USERNAMES.")
        sys.exit(1)

    # Configuration
    use_cache = not args.no_cache
    year = args.year

    logger.debug("Year: %d", year)
    logger.debug("Cache enabled: %s", use_cache)
    logger.debug("Cache directory: %s", args.cache_dir)

    if not use_cache:
        print("[Cache disabled - fetching fresh data]\n")

    # Initialize API client
    api = GitLabAPI(
        base_url=args.gitlab_url,
        token=token,
        cache_dir=args.cache_dir,
        use_cache=use_cache
    )

    # Fetch and display issue statistics
    print(f"Fetching issue counts for {year}...\n")
    issue_results = fetch_user_stats(
        api,
        usernames,
        year,
        api.get_user_issue_stats,
        lambda r: f"{r['issue_count']} issues"
    )
    print_issue_summary(issue_results)

    # Fetch and display MR statistics
    print(f"\nFetching MR statistics for {year}...\n")
    mr_results = fetch_user_stats(
        api,
        usernames,
        year,
        api.get_user_mr_stats,
        lambda r: f"Opened: {r['opened']}, Merged: {r['merged']}"
    )
    print_mr_summary(mr_results)

    # Fetch and display commit statistics
    print(f"\nFetching commit statistics for {year}...\n")
    commit_results = fetch_user_stats(
        api,
        usernames,
        year,
        api.get_user_commit_stats,
        lambda r: f"{r['commit_count']} commits"
    )
    print_commits_summary(commit_results)

    # Fetch and display comment statistics
    print(f"\nFetching comment statistics for {year}...\n")
    comment_results = fetch_user_stats(
        api,
        usernames,
        year,
        api.get_user_comment_stats,
        lambda r: f"Issues: {r['issues_commented']}, MRs: {r['mrs_commented']}"
    )
    print_comments_summary(comment_results)


if __name__ == '__main__':
    main()
