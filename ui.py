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
    with st.expander("AI Thinking Process", expanded=False):
        st.write("**Processing Steps:**")
        for i, step in enumerate(steps, 1):
            st.write(f"{i}. {step}")
        
        st.write("**Analysis Results:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Complexity: {metadata.get('complexity_level')}")
            st.write(f"Decomposed: {metadata.get('decomposed', False)}")
        with col2:
            if 'memory_stats' in metadata:
                stats = metadata['memory_stats']
                st.write(f"Messages: {stats.get('short_term_messages', 0)}")
                st.write(f"Facts: {stats.get('long_term_facts', 0)}")

def main():
    st.title("Memory Research Assistant")
    
    # Sidebar
    with st.sidebar:
        st.header("System")
        
        if st.button("Run Evaluation"):
            with st.spinner("Running evaluation..."):
                result = call_api("/evaluate", method="POST")
                if result:
                    st.success(f"Overall Score: {result['overall_score']:.2%}")
                    for name, metrics in result['metrics'].items():
                        st.write(f"{name}: {metrics['score']:.2%}")
        
        if st.button("Run Benchmark"):
            with st.spinner("Running benchmark..."):
                result = call_api("/benchmark", method="POST")
                if result:
                    st.success(f"Avg Response Time: {result['avg_response_time']:.2f}s")
                    st.write(f"Success Rate: {result['success_rate']:.2%}")
        
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
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            thinking_container = st.container()
            response_container = st.container()
            
            with thinking_container:
                thinking_placeholder = st.empty()
                
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
            
            api_data = {"query": prompt, "session_id": st.session_state.session_id}
            response = call_api("/query", method="POST", data=api_data)
            
            if response:
                if not st.session_state.session_id:
                    st.session_state.session_id = response["session_id"]
                
                with response_container:
                    st.write(response["response"])
                    show_thinking_process(response["thinking_steps"], response["metadata"])
                
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