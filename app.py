"""
Streamlit Real-time Audience Voting App

This application provides a simple interface for collecting votes from
audience members in real‑time. It offers four configurable choices,
tracks voter identifiers to prevent duplicate submissions, and stores
results in a CSV file hosted on GitHub.

Requirements
------------
* streamlit
* pandas
* requests
* streamlit‑autorefresh (optional, for automatic updates)

The app uses a GitHub personal access token (PAT) stored in the
``GITHUB_TOKEN`` environment variable to read and update the CSV file in
the repository. Without a token, the app falls back to reading a local
``votes.csv`` file and cannot persist votes across sessions.
"""

import base64
import json
import os
from datetime import datetime
from typing import Tuple, Optional

import pandas as pd
import requests
import streamlit as st


def load_votes_from_github(repo: str, path: str, branch: str = "main") -> Tuple[pd.DataFrame, Optional[str]]:
    """Load the votes CSV from GitHub.

    Parameters
    ----------
    repo : str
        The ``owner/repo`` string.
    path : str
        Path to the CSV file in the repository.
    branch : str, optional
        Branch where the file is stored, by default "main".

    Returns
    -------
    (pd.DataFrame, Optional[str])
        A tuple containing the dataframe and the file's SHA. If the file
        does not exist, the dataframe will be empty and SHA will be None.
    """
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        csv_str = base64.b64decode(content["content"]).decode("utf-8")
        df = pd.read_csv(pd.compat.StringIO(csv_str))
        sha = content.get("sha")
        return df, sha
    else:
        # Return an empty DataFrame if file doesn't exist or fetch fails
        empty_df = pd.DataFrame(columns=["identifier", "choice", "timestamp"])
        return empty_df, None


def update_votes_on_github(
    repo: str, path: str, df: pd.DataFrame, sha: Optional[str], branch: str = "main"
) -> bool:
    """Update the votes CSV on GitHub.

    This function writes the provided dataframe back to GitHub using the
    contents API. It requires the ``GITHUB_TOKEN`` environment variable
    to be set with a token that has ``repo`` scope.

    Parameters
    ----------
    repo : str
        The ``owner/repo`` string.
    path : str
        Path to the CSV file in the repository.
    df : pd.DataFrame
        Dataframe containing vote records.
    sha : Optional[str]
        The SHA of the existing file. Should be ``None`` if the file is
        being created for the first time.
    branch : str, optional
        Branch where the file is stored, by default "main".

    Returns
    -------
    bool
        True if the update succeeded, False otherwise.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return False
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    csv_str = df.to_csv(index=False)
    b64_content = base64.b64encode(csv_str.encode()).decode()
    commit_message = f"Update votes {datetime.utcnow().isoformat()}"
    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": branch,
        # Only include ``sha`` if updating an existing file
        **({"sha": sha} if sha else {}),
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    return response.status_code in (200, 201)


def main() -> None:
    """Main entry point for the Streamlit app."""
    st.set_page_config(page_title="Real‑Time Audience Voting", page_icon="🗳️", layout="wide")
    st.title("Real‑Time Audience Voting App")
    st.write(
        "Please enter your name or email and select one of the options below to cast your vote. "
        "Each participant can vote only once."
    )

    # Configuration: repository and CSV path
    repo = "aidenyan12/EngagementSystem"
    csv_path = "votes.csv"
    branch = "main"
    # Four configurable choices
    choices = [
        "Choice A",
        "Choice B",
        "Choice C",
        "Choice D",
    ]

    # Input fields
    identifier = st.text_input("Your name or email:", max_chars=100)
    selected_choice = st.radio("Select an option:", choices, key="choice_radio")

    # Load current votes
    votes_df, current_sha = load_votes_from_github(repo, csv_path, branch)

    # Submit vote button
    if st.button("Submit Vote"):
        if not identifier.strip():
            st.error("Please provide your name or email before submitting your vote.")
        else:
            # Check for duplicate
            if identifier.strip() in votes_df["identifier"].values:
                st.warning("You have already cast a vote. Duplicate votes are not allowed.")
            else:
                # Append the new vote
                new_row = {
                    "identifier": identifier.strip(),
                    "choice": selected_choice,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                updated_df = pd.concat([votes_df, pd.DataFrame([new_row])], ignore_index=True)
                # Try to update on GitHub
                success = update_votes_on_github(repo, csv_path, updated_df, current_sha, branch)
                if success:
                    st.success("Your vote has been recorded! Thank you for participating.")
                    # Reload data after successful update
                    votes_df, current_sha = load_votes_from_github(repo, csv_path, branch)
                else:
                    # Fallback: save locally and inform user of limited persistence
                    updated_df.to_csv(csv_path, index=False)
                    st.info(
                        "Your vote has been recorded locally, but it could not be saved to GitHub. "
                        "Please ensure a valid GITHUB_TOKEN secret is configured in your Streamlit deployment."
                    )

    # Display results section
    st.subheader("Current Results")
    if not votes_df.empty:
        # Ensure all choices are represented
        counts = votes_df["choice"].value_counts().reindex(choices, fill_value=0)
        # Display a bar chart
        st.bar_chart(counts)
        # Show the raw votes table if the user wants to inspect it
        with st.expander("Show raw vote data"):
            st.dataframe(votes_df)
    else:
        st.info("No votes have been recorded yet. Be the first to vote!")

    # Auto‑refresh results every 5 seconds (optional)
    try:
        from streamlit_autorefresh import st_autorefresh

        st_autorefresh(interval=5000, key="datarefresh")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
