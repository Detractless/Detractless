import os
import urllib.request
import urllib.error
import json
import re
from collections import Counter

def get_stats(username, token):
    # We use GitHub's GraphQL API to fetch accurate and combined user stats efficiently
    query = """
    query userInfo($login: String!) {
      user(login: $login) {
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
          totalCount
          nodes {
            stargazerCount
            primaryLanguage {
              name
            }
            openIssues: issues(states: OPEN) {
              totalCount
            }
            closedIssues: issues(states: CLOSED) {
              totalCount
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
        }
      }
    }
    """

    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json'
    }
    data = json.dumps({'query': query, 'variables': {'login': username}}).encode('utf-8')

    req = urllib.request.Request('https://api.github.com/graphql', data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching data from GitHub: {e}")
        return None

    user_data = result.get('data', {}).get('user')
    if not user_data:
        print("Could not retrieve user data.")
        return None

    # Calculate statistics
    repos = user_data['repositories']['nodes']
    stars = sum(repo['stargazerCount'] for repo in repos)
    repo_count = user_data['repositories']['totalCount']
    commits = user_data['contributionsCollection']['totalCommitContributions']
    open_issues = sum(repo['openIssues']['totalCount'] for repo in repos)
    closed_issues = sum(repo['closedIssues']['totalCount'] for repo in repos)

    # Determine most frequent language
    languages = [repo['primaryLanguage']['name'] for repo in repos if repo.get('primaryLanguage')]
    top_lang = Counter(languages).most_common(1)[0][0] if languages else "Markdown"

    return {
        'lang': top_lang,
        'commits': str(commits),
        'stars': str(stars),
        'repos': str(repo_count),
        'open': str(open_issues),
        'closed': str(closed_issues)
    }

def update_svg(file_path, stats):
    with open(file_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Find elements by ID and replace their inner text
    for key, val in stats.items():
        # This matches: <text id="val-lang" ...>Old Text</text>
        pattern = rf'(<text\s+id="val-{key}"[^>]*>)(.*?)(</text>)'
        svg_content = re.sub(pattern, rf'\g<1>{val}\g<3>', svg_content, flags=re.DOTALL)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

if __name__ == "__main__":
    username = os.environ.get('GITHUB_USERNAME', 'Detractless')
    token = os.environ.get('GITHUB_TOKEN')

    if not token:
        print("GITHUB_TOKEN is missing! Make sure secrets.GITHUB_TOKEN is passed in the Action.")
        exit(1)

    stats = get_stats(username, token)
    if stats:
        print(f"Fetched stats successfully: {stats}")
        update_svg('assets/header.svg', stats)
        print("Updated assets/header.svg")
