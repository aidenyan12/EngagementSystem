import os
import requests
import streamlit as st

def ensure_logged_in():
    """Simple in-memory login system with two roles: admin and user."""
    if "role" not in st.session_state:
        st.session_state.role = None
    if st.session_state.role:
        return True
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Example static credentials; replace with secure validation in production
        credentials = {"admin": "adminpass", "user": "userpass"}
        if username in credentials and password == credentials[username]:
            st.session_state.role = username
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")
    return False

def chat_interface():
    """Render the chat interface that calls the ATL chatbot API."""
    st.title("ATL Chatbot")
    st.write("Ask our chatbot questions about the Arts Tech Lab. The bot will respond based on the lab's resources.")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.chat_message("user").markdown(msg["content"])
        else:
            st.chat_message("assistant").markdown(msg["content"])

    # Input for the next message
    prompt = st.chat_input("Type your message here...")
    if prompt:
        # Append user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Call external chatbot API
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

        # Append bot reply to history and display
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.chat_message("assistant").markdown(bot_reply)

def main():
    if ensure_logged_in():
        chat_interface()

if __name__ == "__main__":
    main()
