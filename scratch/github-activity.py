#!/usr/bin/python3

import argparse
import json
import logging
import requests
import time
from pathlib import Path
from typing import Callable, Optional

# Default cache directory
CACHE_DIR = Path(__file__).parent / ".gh-issues-cache"

# Set up logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="  [%(levelname)s] %(message)s"
    )


def get_cache_path(cache_key: str) -> Path:
    """Get the file path for a cache key."""
    return CACHE_DIR / f"{cache_key}.json"


def load_from_cache(cache_key: str) -> Optional[dict]:
    """
    Load cached data from disk.

    Args:
        cache_key: Unique key for the cached data

    Returns:
        Cached data if found, None otherwise
    """
    cache_path = get_cache_path(cache_key)
    if cache_path.exists():
        try:
            logger.debug("Loading from cache: %s", cache_path)
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            logger.debug("Cache file corrupted: %s", cache_path)
            return None
    return None


def save_to_cache(cache_key: str, data: dict) -> None:
    """
    Save data to disk cache.

    Args:
        cache_key: Unique key for the cached data
        data: Data to cache
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = get_cache_path(cache_key)
    logger.debug("Saving to cache: %s", cache_path)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def clear_cache() -> int:
    """
    Clear all cached data.

    Returns:
        Number of cache files deleted
    """
    if not CACHE_DIR.exists():
        return 0

    count = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        cache_file.unlink()
        count += 1
    return count


def get_user_issues_count(username: str, year: int = 2025, token: Optional[str] = None) -> dict:
    """
    Get the count of issues opened by a user in a specific year.

    Args:
        username: GitHub username
        year: Year to search (default: 2025)
        token: Optional GitHub Personal Access Token for authentication

    Returns:
        Dictionary with username and issue count
    """
    url = "https://api.github.com/search/issues"
    params = {
        'q': f'author:{username} type:issue created:{year}-01-01..{year}-12-31'
    }

    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        logger.debug("GET %s?q=%s", url, params['q'])
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        logger.debug("Response: %s", response.status_code)

        data = response.json()
        return {
            'username': username,
            'issue_count': data['total_count'],
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        return {
            'username': username,
            'issue_count': 0,
            'status': 'error',
            'error': str(e)
        }


def get_user_prs_count(username: str, year: int = 2025, token: Optional[str] = None) -> dict:
    """
    Get the count of PRs opened and merged by a user in a specific year.

    Args:
        username: GitHub username
        year: Year to search (default: 2025)
        token: Optional GitHub Personal Access Token for authentication

    Returns:
        Dictionary with username, opened PR count, and merged PR count
    """
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        # Query for opened PRs
        opened_url = "https://api.github.com/search/issues"
        opened_params = {
            'q': f'author:{username} type:pr created:{year}-01-01..{year}-12-31'
        }

        logger.debug("GET %s?q=%s", opened_url, opened_params['q'])
        opened_response = requests.get(opened_url, params=opened_params, headers=headers)
        opened_response.raise_for_status()
        logger.debug("Response: %s", opened_response.status_code)
        opened_count = opened_response.json()['total_count']

        # Small delay between requests
        time.sleep(5)

        # Query for merged PRs
        merged_url = "https://api.github.com/search/issues"
        merged_params = {
            'q': f'author:{username} type:pr is:merged merged:{year}-01-01..{year}-12-31'
        }

        logger.debug("GET %s?q=%s", merged_url, merged_params['q'])
        merged_response = requests.get(merged_url, params=merged_params, headers=headers)
        merged_response.raise_for_status()
        logger.debug("Response: %s", merged_response.status_code)
        merged_count = merged_response.json()['total_count']

        return {
            'username': username,
            'opened': opened_count,
            'merged': merged_count,
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        return {
            'username': username,
            'opened': 0,
            'merged': 0,
            'status': 'error',
            'error': str(e)
        }


def get_user_commits_count(username: str, year: int = 2025, token: Optional[str] = None) -> dict:
    """
    Get the count of commits made by a user in a specific year.

    Args:
        username: GitHub username
        year: Year to search (default: 2025)
        token: Optional GitHub Personal Access Token for authentication

    Returns:
        Dictionary with username and commit count
    """
    url = "https://api.github.com/search/commits"
    params = {
        'q': f'author:{username} committer-date:{year}-01-01..{year}-12-31'
    }

    headers = {
        'Accept': 'application/vnd.github.cloak-preview'  # Required for commit search
    }
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        logger.debug("GET %s?q=%s", url, params['q'])
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        logger.debug("Response: %s", response.status_code)

        data = response.json()
        return {
            'username': username,
            'commit_count': data['total_count'],
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        return {
            'username': username,
            'commit_count': 0,
            'status': 'error',
            'error': str(e)
        }


def get_user_commits_detailed(username: str, year: int = 2025, token: Optional[str] = None) -> dict:
    """
    Get detailed commit statistics including authored vs committed counts.

    Args:
        username: GitHub username
        year: Year to search (default: 2025)
        token: Optional GitHub Personal Access Token for authentication

    Returns:
        Dictionary with username, authored commits, and committed commits
    """
    headers = {
        'Accept': 'application/vnd.github.cloak-preview'
    }
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        # Query for commits by author-date (when the commit was originally created)
        authored_url = "https://api.github.com/search/commits"
        authored_params = {
            'q': f'author:{username} author-date:{year}-01-01..{year}-12-31'
        }

        logger.debug("GET %s?q=%s", authored_url, authored_params['q'])
        authored_response = requests.get(authored_url, params=authored_params, headers=headers)
        authored_response.raise_for_status()
        logger.debug("Response: %s", authored_response.status_code)
        authored_count = authored_response.json()['total_count']

        # Small delay between requests
        time.sleep(5)

        # Query for commits by committer-date (when the commit was applied)
        committed_url = "https://api.github.com/search/commits"
        committed_params = {
            'q': f'committer:{username} committer-date:{year}-01-01..{year}-12-31'
        }

        logger.debug("GET %s?q=%s", committed_url, committed_params['q'])
        committed_response = requests.get(committed_url, params=committed_params, headers=headers)
        committed_response.raise_for_status()
        logger.debug("Response: %s", committed_response.status_code)
        committed_count = committed_response.json()['total_count']

        return {
            'username': username,
            'authored': authored_count,
            'committed': committed_count,
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        return {
            'username': username,
            'authored': 0,
            'committed': 0,
            'status': 'error',
            'error': str(e)
        }


def get_user_comments_count(username: str, year: int = 2025, token: Optional[str] = None) -> dict:
    """
    Get the count of issues/PRs where a user has commented in a specific year.

    Note: This counts issues/PRs with at least one comment from the user,
    not the total number of comments made.

    Args:
        username: GitHub username
        year: Year to search (default: 2025)
        token: Optional GitHub Personal Access Token for authentication

    Returns:
        Dictionary with username and count of issues/PRs commented on
    """
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'

    try:
        url = "https://api.github.com/search/issues"

        # Issues commented on
        issue_params = {
            'q': f'commenter:{username} type:issue updated:{year}-01-01..{year}-12-31'
        }
        logger.debug("GET %s?q=%s", url, issue_params['q'])
        issue_response = requests.get(url, params=issue_params, headers=headers)
        issue_response.raise_for_status()
        logger.debug("Response: %s", issue_response.status_code)
        issues_commented = issue_response.json()['total_count']

        time.sleep(5)

        # PRs commented on
        pr_params = {
            'q': f'commenter:{username} type:pr updated:{year}-01-01..{year}-12-31'
        }
        logger.debug("GET %s?q=%s", url, pr_params['q'])
        pr_response = requests.get(url, params=pr_params, headers=headers)
        pr_response.raise_for_status()
        logger.debug("Response: %s", pr_response.status_code)
        prs_commented = pr_response.json()['total_count']

        return {
            'username': username,
            'issues_commented': issues_commented,
            'prs_commented': prs_commented,
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        return {
            'username': username,
            'issues_commented': 0,
            'prs_commented': 0,
            'status': 'error',
            'error': str(e)
        }


def fetch_user_stats(usernames: list[str], fetch_func: Callable, year: int, token: Optional[str],
                     format_success: Callable[[dict], str], use_cache: bool = True) -> list[dict]:
    """
    Fetch statistics for a list of users using the provided fetch function.

    Args:
        usernames: List of GitHub usernames
        fetch_func: Function to call for each user (signature: func(username, year, token) -> dict)
        year: Year to query
        token: GitHub token for authentication
        format_success: Function to format success message (signature: func(result) -> str)
        use_cache: Whether to use cached results (default: True)

    Returns:
        List of result dictionaries
    """
    results = []
    func_name = fetch_func.__name__

    for username in usernames:
        cache_key = f"{func_name}_{username}_{year}"

        # Try to load from cache first
        if use_cache:
            cached_result = load_from_cache(cache_key)
            if cached_result is not None:
                print(f"Loading {username}... [cached] ✓ {format_success(cached_result)}")
                results.append(cached_result)
                continue

        # Fetch from API
        print(f"Querying {username}...", end=' ')
        result = fetch_func(username, year, token)
        results.append(result)

        if result['status'] == 'success':
            print(f"✓ {format_success(result)}")
            # Save successful results to cache
            save_to_cache(cache_key, result)
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")

        time.sleep(5)

    return results


def print_issue_summary(results: list[dict]):
    """Print summary for issue statistics."""
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    for result in results:
        if result['status'] == 'success':
            print(f"{result['username']:20} {result['issue_count']:6} issues")
        else:
            print(f"{result['username']:20} ERROR")

    total = sum(r['issue_count'] for r in results if r['status'] == 'success')
    print(f"\n{'Total':20} {total:6} issues")


def print_pr_summary(results: list[dict]):
    """Print summary for PR statistics."""
    print("\n" + "="*70)
    print("SUMMARY")
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


def print_commits_summary(results: list[dict]):
    """Print summary for simple commit statistics."""
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    for result in results:
        if result['status'] == 'success':
            print(f"{result['username']:20} {result['commit_count']:6} commits")
        else:
            print(f"{result['username']:20} ERROR")

    total = sum(r['commit_count'] for r in results if r['status'] == 'success')
    print(f"\n{'Total':20} {total:6} commits")


def print_commits_detailed_summary(results: list[dict]):
    """Print summary for detailed commit statistics (authored vs committed)."""
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'Username':<20} {'Authored':>12} {'Committed':>12}")
    print("-"*70)

    for result in results:
        if result['status'] == 'success':
            authored = result['authored']
            committed = result['committed']
            print(f"{result['username']:<20} {authored:>12} {committed:>12}")
        else:
            print(f"{result['username']:<20} {'ERROR':>12} {'ERROR':>12}")

    print("-"*70)
    total_authored = sum(r['authored'] for r in results if r['status'] == 'success')
    total_committed = sum(r['committed'] for r in results if r['status'] == 'success')
    print(f"{'Total':<20} {total_authored:>12} {total_committed:>12}")


def print_comments_summary(results: list[dict]):
    """Print summary for comment statistics (issues/PRs commented on)."""
    print("\n" + "="*70)
    print("SUMMARY (Issues/PRs with at least one comment)")
    print("="*70)
    print(f"{'Username':<20} {'Issues':>12} {'PRs':>12} {'Total':>12}")
    print("-"*70)

    for result in results:
        if result['status'] == 'success':
            issues = result['issues_commented']
            prs = result['prs_commented']
            total = issues + prs
            print(f"{result['username']:<20} {issues:>12} {prs:>12} {total:>12}")
        else:
            print(f"{result['username']:<20} {'ERROR':>12} {'ERROR':>12} {'ERROR':>12}")

    print("-"*70)
    total_issues = sum(r['issues_commented'] for r in results if r['status'] == 'success')
    total_prs = sum(r['prs_commented'] for r in results if r['status'] == 'success')
    print(f"{'Total':<20} {total_issues:>12} {total_prs:>12} {total_issues + total_prs:>12}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch GitHub issue and PR statistics for users"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache and fetch fresh data from API"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the cache and exit"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Year to query (default: 2025)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including API calls"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Set up logging based on verbosity
    setup_logging(args.verbose)

    # Handle cache clearing
    if args.clear_cache:
        count = clear_cache()
        print(f"Cleared {count} cached file(s)")
        return

    # Configuration
    GITHUB_TOKEN = None
    YEAR = args.year
    use_cache = not args.no_cache

    logger.debug("Year: %s", YEAR)
    logger.debug("Cache enabled: %s", use_cache)
    logger.debug("Cache directory: %s", CACHE_DIR)

    if not use_cache:
        print("[Cache disabled - fetching fresh data]\n")

    usernames = [
        "djach7",
        "jbenc",
        "kgiusti",
        "mcattamoredhat",
        "mmartinv",
        "pcdubs",
        "runcom",
        "sarmahaj",
        "say-paul",
        "yih-redhat",
    ]

    # Fetch and display issue statistics
    print(f"Fetching issue counts for {YEAR}...\n")
    issue_results = fetch_user_stats(
        usernames,
        get_user_issues_count,
        YEAR,
        GITHUB_TOKEN,
        lambda r: f"{r['issue_count']} issues",
        use_cache=use_cache
    )
    print_issue_summary(issue_results)

    # Fetch and display PR statistics
    print(f"\nFetching PR statistics for {YEAR}...\n")
    pr_results = fetch_user_stats(
        usernames,
        get_user_prs_count,
        YEAR,
        GITHUB_TOKEN,
        lambda r: f"Opened: {r['opened']}, Merged: {r['merged']}",
        use_cache=use_cache
    )
    print_pr_summary(pr_results)

    # Fetch and display commit statistics
    print(f"\nFetching commit statistics for {YEAR}...\n")
    commit_results = fetch_user_stats(
        usernames,
        get_user_commits_detailed,
        YEAR,
        GITHUB_TOKEN,
        lambda r: f"Authored: {r['authored']}, Committed: {r['committed']}",
        use_cache=use_cache
    )
    print_commits_detailed_summary(commit_results)

    # Fetch and display comment statistics
    print(f"\nFetching comment statistics for {YEAR}...\n")
    comment_results = fetch_user_stats(
        usernames,
        get_user_comments_count,
        YEAR,
        GITHUB_TOKEN,
        lambda r: f"Issues: {r['issues_commented']}, PRs: {r['prs_commented']}",
        use_cache=use_cache
    )
    print_comments_summary(comment_results)


if __name__ == "__main__":
    main()
