"""
Streamlit Real-time Audience Voting App

This app allows audience members to vote in real-time. It offers four
configurable choices, tracks who voted by a user-specified identifier,
prevents duplicate votes, and stores votes in a CSV file on GitHub.
Votes and results are visible to all users.
"""

import os
import io
import base64
import datetime
import requests
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Details for the GitHub repository and file used to store votes
GITHUB_REPO = os.environ.get("GITHUB_REPO", "aidenyan12/EngagementSystem")
VOTES_FILE = os.environ.get("VOTES_FILE", "votes.csv")
BRANCH_NAME = os.environ.get("BRANCH_NAME", "main")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # PAT for committing changes


def load_votes_from_github():
    """Fetch the CSV file containing votes from GitHub.

    Returns
    -------
    pandas.DataFrame
        DataFrame of recorded votes with columns [identifier, choice, timestamp]
    str or None
        SHA of the existing file on GitHub, needed for updating the file.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VOTES_FILE}?ref={BRANCH_NAME}"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_data = response.json()
        csv_content = base64.b64decode(file_data['content']).decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_content))
        sha = file_data['sha']
        return df, sha
    else:
        # If the file doesn't exist yet or an error occurred, return an empty DataFrame
        return pd.DataFrame(columns=["identifier", "choice", "timestamp"]), None


def update_votes_on_github(df: pd.DataFrame, sha: str | None) -> bool:
    """Push the updated votes DataFrame back to GitHub.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to upload.
    sha : str or None
        The SHA of the existing file on GitHub; required to update existing file.

    Returns
    -------
    bool
        True if the update was successful, False otherwise.
    """
    # Convert DataFrame to CSV
    csv_str = df.to_csv(index=False)
    b64_content = base64.b64encode(csv_str.encode('utf-8')).decode('utf-8')

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VOTES_FILE}"
    data = {
        "message": "Update votes",
        "content": b64_content,
        "branch": BRANCH_NAME,
    }
    if sha:
        data["sha"] = sha

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.put(url, headers=headers, json=data)

    return response.status_code in (200, 201)


def main():
    st.set_page_config(page_title="Real-Time Voting App", page_icon="🗳️", layout="centered")
    st.title("Real-Time Audience Voting")
    st.write(
        "Participate by entering your name or identifier and selecting one of the four choices below. "
        "Results update in near real-time."
    )

    # Automatically refresh the page every 5 seconds
    st_autorefresh(interval=5_000, limit=None, key="auto-refresh")

    # Default choices; can be overridden via Streamlit secrets
    default_choices = ["Choice A", "Choice B", "Choice C", "Choice D"]
    choices = st.secrets.get("choices", default_choices)

    # Load current votes
    df, sha = load_votes_from_github()

    with st.form("vote_form", clear_on_submit=False):
        identifier = st.text_input("Enter your name or identifier:", max_chars=100).strip()
        choice = st.radio("Select your choice:", options=choices)
        submitted = st.form_submit_button("Submit Vote")

        if submitted:
            # Validate input
            if not identifier:
                st.error("Please enter your name or identifier.")
            elif identifier in df["identifier"].values:
                st.warning("You have already voted. Duplicate votes are not allowed.")
            else:
                timestamp = datetime.datetime.utcnow().isoformat()
                new_row = {"identifier": identifier, "choice": choice, "timestamp": timestamp}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

                if GITHUB_TOKEN:
                    success = update_votes_on_github(df, sha)
                    if success:
                        st.success("Your vote has been recorded!")
                    else:
                        st.error("There was an error saving your vote. Please try again later.")
                else:
                    st.error("GitHub token is not configured. Votes will not be saved.")

    # Display results
    st.header("Current Results")
    if not df.empty:
        # Count votes for each choice and align to defined choices order
        vote_counts = df['choice'].value_counts().reindex(choices, fill_value=0)
        st.bar_chart(vote_counts)
        st.subheader("Detailed Votes")
        st.dataframe(df)
    else:
        st.info("No votes recorded yet.")


if __name__ == "__main__":
    main()
