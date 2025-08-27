import streamlit as st
import requests
import time

st.set_page_config(page_title="Memory Research Assistant", layout="wide")

API_BASE_URL = "http://localhost:8000"

def call_api(endpoint, method="GET", data=None, files=None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "POST":
            if files:
                response = requests.post(url, files=files, data=data)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Start server: python app.py")
        return None

def show_thinking_process(steps, metadata):
    """Display AI thinking process"""
    with st.expander("AI Thinking Process", expanded=False):
        st.write("**Processing Steps:**")
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")
        
        st.write("**Analysis Results:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Complexity: {metadata.get('complexity_level')}")
            st.write(f"Processing time: {metadata.get('processing_time')}s")
        with col2:
            st.write(f"Memory: {metadata.get('session_messages')} messages")
            st.write(f"Facts: {metadata.get('session_facts')} stored")

def main():
    st.title("Memory-Persistent Research Assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("Document Upload")
        uploaded_file = st.file_uploader("Upload PDF/TXT", type=['pdf', 'txt'])
        
        if uploaded_file and st.button("Index Document"):
            files = {"file": uploaded_file}
            with st.spinner("Indexing..."):
                result = call_api("/upload", method="POST", files=files)
                if result and result.get('success'):
                    st.success(f"Indexed: {result.get('sections')} sections")
                else:
                    st.error("Failed to index")
        
        st.header("Session")
        if 'session_id' in st.session_state and st.session_state.session_id:
            session_info = call_api(f"/session/{st.session_state.session_id}")
            if session_info:
                st.write(f"Messages: {session_info['message_count']}")
                st.write(f"Facts: {session_info['facts_count']}")
                
                if st.button("Clear Session"):
                    call_api(f"/session/{st.session_state.session_id}", method="DELETE")
                    st.session_state.clear()
                    st.rerun()
    
    # Initialize session
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    
    # Chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            if message["role"] == "assistant" and "thinking_steps" in message:
                show_thinking_process(message["thinking_steps"], message["metadata"])
    
    # Chat input
    if prompt := st.chat_input("Ask about documents or research questions..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Assistant response
        with st.chat_message("assistant"):
            # Show real-time thinking
            thinking_container = st.container()
            response_container = st.container()
            
            with thinking_container:
                thinking_placeholder = st.empty()
                
                # Simulate thinking steps
                steps = [
                    "Analyzing query...",
                    "Checking memory...", 
                    "Searching documents...",
                    "Processing workflow...",
                    "Generating response..."
                ]
                
                for step in steps:
                    thinking_placeholder.write(f"Thinking: {step}")
                    time.sleep(0.3)
                
                thinking_placeholder.empty()
            
            # API call
            api_data = {"query": prompt, "session_id": st.session_state.session_id}
            response = call_api("/query", method="POST", data=api_data)
            
            if response:
                # Update session ID
                if not st.session_state.session_id:
                    st.session_state.session_id = response["session_id"]
                
                # Display response
                with response_container:
                    st.write(response["response"])
                    show_thinking_process(response["thinking_steps"], response["metadata"])
                
                # Save to session
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["response"],
                    "thinking_steps": response["thinking_steps"],
                    "metadata": response["metadata"]
                })
            else:
                st.error("Failed to process query")

if __name__ == "__main__":
    main()