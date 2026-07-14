import httpx

class GitHubAgent:
    def __init__(self):
        self.base_url = "https://api.github.com"

    def _get_headers(self, token: str):
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Luna-AI-OS-X"
        }

    async def get_user_repos(self, token: str):
        headers = self._get_headers(token)
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/user/repos?sort=updated&per_page=8", headers=headers)
            if response.status_code != 200:
                raise Exception(f"GitHub API returned {response.status_code}: {response.text}")
            repos = response.json()
            result = []
            for r in repos:
                result.append({
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "description": r.get("description") or "No description provided.",
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "open_issues_count": r.get("open_issues_count", 0),
                    "branch": r.get("default_branch", "main"),
                    "url": r.get("html_url")
                })
            return result

    async def get_repo_details(self, token: str, owner: str, repo: str):
        headers = self._get_headers(token)
        async with httpx.AsyncClient() as client:
            # Fetch commits
            commits_resp = await client.get(f"{self.base_url}/repos/{owner}/{repo}/commits?per_page=5", headers=headers)
            commits = []
            if commits_resp.status_code == 200:
                for c in commits_resp.json():
                    commit_data = c.get("commit", {})
                    commits.append({
                        "sha": c.get("sha")[:7],
                        "message": commit_data.get("message"),
                        "author": commit_data.get("author", {}).get("name"),
                        "date": commit_data.get("author", {}).get("date")
                    })

            # Fetch issues and PRs
            issues_resp = await client.get(f"{self.base_url}/repos/{owner}/{repo}/issues?state=open&per_page=15", headers=headers)
            open_issues_count = 0
            open_prs_count = 0
            recent_issues = []
            if issues_resp.status_code == 200:
                for issue in issues_resp.json():
                    is_pr = "pull_request" in issue
                    if is_pr:
                        open_prs_count += 1
                    else:
                        open_issues_count += 1
                        recent_issues.append({
                            "number": issue.get("number"),
                            "title": issue.get("title"),
                            "user": issue.get("user", {}).get("login"),
                            "created_at": issue.get("created_at")
                        })
            
            return {
                "commits": commits,
                "open_issues_count": open_issues_count,
                "open_prs_count": open_prs_count,
                "recent_issues": recent_issues
            }

    async def get_user_profile(self, token: str):
        headers = self._get_headers(token)
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/user", headers=headers)
            if response.status_code != 200:
                raise Exception(f"GitHub API returned {response.status_code}: {response.text}")
            user_data = response.json()
            return {
                "login": user_data.get("login"),
                "avatar_url": user_data.get("avatar_url"),
                "name": user_data.get("name") or user_data.get("login"),
                "html_url": user_data.get("html_url"),
                "bio": user_data.get("bio") or "",
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "public_repos": user_data.get("public_repos", 0)
            }

    async def get_repo_extended_details(self, token: str, owner: str, repo: str):
        headers = self._get_headers(token)
        async with httpx.AsyncClient() as client:
            # Fetch contributors
            contribs_resp = await client.get(f"{self.base_url}/repos/{owner}/{repo}/contributors?per_page=5", headers=headers)
            contribs = []
            if contribs_resp.status_code == 200:
                for c in contribs_resp.json():
                    contribs.append({
                        "login": c.get("login"),
                        "contributions": c.get("contributions"),
                        "avatar_url": c.get("avatar_url")
                    })
            
            # Fetch releases
            releases_resp = await client.get(f"{self.base_url}/repos/{owner}/{repo}/releases?per_page=5", headers=headers)
            releases = []
            if releases_resp.status_code == 200:
                for r in releases_resp.json():
                    releases.append({
                        "tag_name": r.get("tag_name"),
                        "name": r.get("name") or r.get("tag_name"),
                        "published_at": r.get("published_at"),
                        "html_url": r.get("html_url")
                    })
                    
            # Fetch actions/workflow runs
            runs_resp = await client.get(f"{self.base_url}/repos/{owner}/{repo}/actions/runs?per_page=5", headers=headers)
            runs = []
            if runs_resp.status_code == 200:
                for r in runs_resp.json().get("workflow_runs", []):
                    runs.append({
                        "id": r.get("id"),
                        "name": r.get("name"),
                        "status": r.get("status"),
                        "conclusion": r.get("conclusion"),
                        "event": r.get("event"),
                        "html_url": r.get("html_url"),
                        "commit_message": r.get("head_commit", {}).get("message", "")
                     })
                     
            return {
                "contributors": contribs,
                "releases": releases,
                "workflow_runs": runs
            }

github_agent = GitHubAgent()
