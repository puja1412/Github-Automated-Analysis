import streamlit as st
from github import Github
import openai
import requests
from constants import openai_key, github_token

# Set up the OpenAI API credentials
openai.api_key = openai_key

# Constants
MAX_TOKENS = 500  # Maximum tokens for GPT completion


# Analyze code complexity using LangChain
def analyze_code_complexity(prompt):
    # Make a request to LangChain for code complexity analysis
    response = openai.Completion.create(
        engine='text-davinci-003',  # Specify the LangChain model
        prompt=prompt,
        max_tokens=MAX_TOKENS,  # Set the desired length of the generated completion
        n=1,
        temperature=0.70,  # Number of completions to generate
        stop=None,  # Specify any stopping criteria if needed
    )

    # Process the response to retrieve the complexity score
    model_resp = response.choices[0].text.strip()

    return model_resp


def analyze_github_repository(user_url):
    '''
    Analyzes the complexity of a GitHub repository.
    :param user_url: The GitHub user URL.
    :return: A dictionary containing the complexity score.
    '''
    # Create a PyGitHub instance using your personal access token
    g = Github(github_token)

    # Extract the username from the GitHub user URL
    username = user_url.split('/')[-1]

    def fetch_repo():
        try:
            # Make a GET request to the GitHub API to fetch the user's repositories
            response = requests.get(f"https://api.github.com/users/{username}/repos")

            if response.status_code == 200:
                # Parse the JSON response
                repositories = response.json()
                return repositories
            else:
                print(f"Error: Failed to fetch repositories (Status code: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to fetch repositories - {e}")
            return None

    def fork_status(repo):
        try:
            response = requests.get(f"https://api.github.com/repos/{username}/{repo}")
            if response.status_code == 200:
                stats = response.json()
                is_forked = stats['fork']
                return is_forked
            else:
                print(f"Error: Failed to fetch fork status (Status code: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to check fork status - {e}")
            return None

        return None

    def fork_count(repo):
        try:
            response = requests.get(f"https://api.github.com/repos/{username}/{repo}")
            if response.status_code == 200:
                stats = response.json()
                fork = stats['forks_count']
                return fork
            else:
                print(f"Error: Failed to fetch fork count (Status code: {response.status_code})")
        except Exception as e:
            print(f"Error: {e}")

        return None

    def total_commits(repo):
        try:
            response = requests.get(f"https://api.github.com/repos/{username}/{repo}/commits")
            if response.status_code == 200:
                commit = response.json()
                total_commit = len(commit)
                return total_commit
            else:
                print(f"Error: Failed to fetch commits (Status code: {response.status_code})")
        except Exception as e:
            print(f"Error: {e}")

        return None

    def contributors(repo):
        try:
            response = requests.get(f"https://api.github.com/repos/{username}/{repo}/contributors")
            if response.status_code == 200:
                contro = response.json()
                contributors = [c for c in contro]
                return contributors
        except Exception as e:
            print(f"Error: {e}")

    def get_repository_issues(username, repo):
        # Make a request to the GitHub API to fetch the repository information
        response = requests.get(f"https://api.github.com/repos/{username}/{repo}")
        if response.status_code == 200:
            repo_data = response.json()
            # Extract the issue count information
            open_issues_count = repo_data['open_issues_count']

            # Make a request to the GitHub API to fetch the list of issues
            issues_response = requests.get(f"https://api.github.com/repos/{username}/{repo}/issues?state=all")
            if issues_response.status_code == 200:
                issues_data = issues_response.json()
                resolved_issues_count = 0
                unresolved_issues_count = 0

                # Calculate the count of resolved and unresolved issues
                for issue in issues_data:
                    if issue['state'] == 'open':
                        unresolved_issues_count += 1
                    else:
                        resolved_issues_count += 1

                return resolved_issues_count, unresolved_issues_count

        return 0, 0

    try:
        repo_names = []
        reponame_list = []
        rep = fetch_repo()
        for repo in rep:
            repo_name = repo["name"]
            if not fork_status(repo_name):
                repo_names.append(repo)
                reponame_list.append(repo['name'])

        forks_list = []
        resolved_issue = []
        unresolved_issue = []
        total_commits_list = []
        total_contributers = []

        # Iterate through each repository
        for repo in repo_names:
            forks_count = fork_count(repo['name'])
            total_commits_count = total_commits(repo['name'])
            resolved_issues_count, unresolved_issues_count = get_repository_issues(username, repo['name'])
            contributors = contributors(repo['name'])
            contributors_count = len(contributors)

            forks_list.append(forks_count)
            resolved_issue.append(resolved_issues_count)
            unresolved_issue.append(unresolved_issues_count)
            total_commits_list.append(total_commits_count)
            total_contributers.append(contributors_count)

        prompt = f'''You are given a list of metrics of respective GitHub repositories {reponame_list} as follows:

Total commits: {total_commits_list}
Forks: {forks_list}
Resolved issues: {resolved_issue}
Unresolved issues: {unresolved_issue}
Contributor count: {total_contributers}

Using the given metrics, determine the strongest repository and calculate the complexity score'''

        model_resp = analyze_code_complexity(prompt)

        main_resp = {"model_resp": model_resp}
        return main_resp

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Streamlit app
def main():
    st.title('Github Automated Analysis')
    user_url = st.text_input("Enter the GitHub user URL")
    if st.button("Analyze"):
        if user_url:
            main_resp = analyze_github_repository(user_url)
            if main_resp:
                st.write("Model output:", main_resp['model_resp'])
            else:
                st.write("No repositories found or an error occurred.")


if __name__ == '__main__':
    main()
