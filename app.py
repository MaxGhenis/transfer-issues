import streamlit as st
import requests
from github import Github
from github.GithubException import GithubException, UnknownObjectException


def check_issue_exists(repo, issue_number):
    try:
        issue = repo.get_issue(issue_number)
        return True, issue
    except UnknownObjectException:
        return False, None


def transfer_issue(issue, target_repo_name, token):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "owner": target_repo_name.split("/")[0],
        "repo": target_repo_name.split("/")[1],
    }
    url = f"https://api.github.com/repos/{issue.repository.full_name}/issues/{issue.number}/transfer"

    try:
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            return f"Successfully transferred issue #{issue.number} to {target_repo_name}"
        elif response.status_code == 404:
            return f"Issue #{issue.number} not found or you don't have permission to transfer it. Please check if the issue exists and you have the necessary permissions."
        else:
            return f"Unexpected response code {response.status_code} when transferring issue #{issue.number}. Response content: {response.text}"

    except requests.exceptions.RequestException as e:
        return f"Failed to transfer issue #{issue.number}: {str(e)}"


def main():
    st.title("GitHub Issue Transfer App")

    github_token = st.text_input(
        "Enter your GitHub Personal Access Token", type="password"
    )

    if github_token:
        try:
            g = Github(github_token)
            user = g.get_user()
            st.success(f"Authenticated as {user.login}")

            source_repo = st.text_input(
                "Enter the source repository (format: owner/repo)"
            )
            if source_repo:
                try:
                    repo = g.get_repo(source_repo)
                    st.success(f"Source repository set to {source_repo}")

                    labels = [label.name for label in repo.get_labels()]
                    selected_labels = st.multiselect(
                        "Select labels (optional)", labels
                    )

                    target_repo = st.text_input(
                        "Enter the target repository (format: owner/repo)"
                    )

                    if st.button("Transfer Issues"):
                        if not target_repo:
                            st.error("Please enter a target repository.")
                        else:
                            try:
                                g.get_repo(target_repo)  # Validate target repo
                                issues = (
                                    repo.get_issues(
                                        state="open", labels=selected_labels
                                    )
                                    if selected_labels
                                    else repo.get_issues(state="open")
                                )

                                progress_bar = st.progress(0)
                                status_area = st.empty()

                                status_updates = []

                                total_issues = len(list(issues))
                                for i, issue in enumerate(issues):
                                    exists, checked_issue = check_issue_exists(
                                        repo, issue.number
                                    )
                                    if exists:
                                        result = transfer_issue(
                                            checked_issue,
                                            target_repo,
                                            github_token,
                                        )
                                    else:
                                        result = f"Issue #{issue.number} does not exist or you don't have permission to view it."

                                    status_updates.append(result)
                                    status_text = "\n".join(status_updates)
                                    status_area.text_area(
                                        "Transfer Status",
                                        status_text,
                                        height=200,
                                        key=f"status_{i}",
                                    )
                                    progress_bar.progress(
                                        (i + 1) / total_issues
                                    )

                                st.success("Issue transfer process completed!")
                            except GithubException as e:
                                st.error(f"Error: {str(e)}")

                except GithubException as e:
                    st.error(f"Error: {str(e)}")

        except GithubException as e:
            st.error(f"Authentication failed: {str(e)}")


if __name__ == "__main__":
    main()
