"""
Streamlit Real-time Audience Voting and ATL Chatbot App

This multi-page Streamlit application includes two components:
1. A real-time audience voting system with four configurable choices that tracks
   voters by identifier, prevents duplicate votes, stores results in a CSV on
   GitHub, and displays live results to all users.
2. An ATL chatbot interface that allows users to log in (simple in-memory
   credentials) and ask questions about the Arts Tech Lab. The chatbot
   communicates with an external API specified via secrets or environment
   variables.

Both components are accessible via a sidebar menu without authentication for
voting but requiring login for the chatbot.
"""

import os
import io
import base64
import datetime
import requests
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# GitHub repository details for storing votes
GITHUB_REPO = os.environ.get("GITHUB_REPO", "aidenyan12/EngagementSystem")
VOTES_FILE = os.environ.get("VOTES_FILE", "votes.csv")
BRANCH_NAME = os.environ.get("BRANCH_NAME", "main")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# -----------------------------------------------------------------------------
# Voting functionality
# -----------------------------------------------------------------------------

def load_votes_from_github():
    """Load votes CSV from GitHub and return DataFrame and SHA."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{VOTES_FILE}?ref={BRANCH_NAME}"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        csv_content = base64.b64decode(data['content']).decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_content))
        sha = data['sha']
        return df, sha
    else:
        return pd.DataFrame(columns=["identifier", "choice", "timestamp"]), None


def update_votes_on_github(df: pd.DataFrame, sha: str | None) -> bool:
    """Update the votes CSV on GitHub."""
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


def vote_page():
    """Render the voting page."""
    st.title("Real-Time Audience Voting")
    st.write(
        "Participate by entering your name or identifier and selecting one of the "
        "four choices below. Results update in near real-time."
    )

    # Auto-refresh every 5 seconds to update results
    st_autorefresh(interval=5_000, limit=None, key="vote-autorefresh")

    # Load current votes
    df, sha = load_votes_from_github()

    # Configurable choices via secrets
    default_choices = ["Choice A", "Choice B", "Choice C", "Choice D"]
    choices = st.secrets.get("choices", default_choices)

    with st.form("vote_form", clear_on_submit=False):
        identifier = st.text_input("Enter your name or identifier:", max_chars=100).strip()
        choice = st.radio("Select your choice:", options=choices)
        submitted = st.form_submit_button("Submit Vote")
        if submitted:
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

    st.header("Current Results")
    if not df.empty:
        vote_counts = df['choice'].value_counts().reindex(choices, fill_value=0)
        st.bar_chart(vote_counts)
        st.subheader("Detailed Votes")
        st.dataframe(df)
    else:
        st.info("No votes recorded yet.")

# -----------------------------------------------------------------------------
# Chatbot functionality
# -----------------------------------------------------------------------------

def ensure_logged_in() -> bool:
    """Simple login system with two roles: admin and user. Returns True if logged in."""
    if "role" not in st.session_state:
        st.session_state.role = None
    if st.session_state.role:
        return True
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Example static credentials for demonstration
        credentials = {"admin": "adminpass", "user": "userpass"}
        if username in credentials and password == credentials[username]:
            st.session_state.role = username
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    return False


def chat_interface():
    """Render the ATL chatbot interface."""
    st.title("ATL Chatbot")
    st.write("Ask our chatbot questions about the Arts Tech Lab.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Type your message here...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        api_url = st.secrets.get("chat_api_url", os.environ.get("CHAT_API_URL", "http://localhost:8000/chat"))
        bot_reply = ""
        try:
            response = requests.post(api_url, json={"message": prompt})
            if response.status_code == 200:
                data = response.json()
                bot_reply = data.get("response", "")
            else:
                bot_reply = f"API returned status code {response.status_code}"
        except Exception as e:
            bot_reply = f"Error contacting API: {e}"
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.chat_message("assistant").markdown(bot_reply)


def chatbot_page():
    """Wrap chat page with login check."""
    if ensure_logged_in():
        chat_interface()

# -----------------------------------------------------------------------------
# Main application
# -----------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Voting & Chatbot App", page_icon="🗳️", layout="centered")

    # Sidebar for navigation
    page = st.sidebar.selectbox("Select a page", ["Vote", "Chatbot"])
    if page == "Vote":
        vote_page()
    elif page == "Chatbot":
        chatbot_page()


if __name__ == "__main__":
    main()
