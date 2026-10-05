import streamlit as st
import os

from rag import add_pdf_to_database, generate_answer

st.set_page_config(
    page_title="Smart PDF AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background-color: #f7f8fc;
}

.header {
    text-align: center;
    padding: 10px 0 25px 0;
}

.header h1 {
    font-size: 36px;
    margin-bottom: 5px;
}

.header p {
    color: #6b7280;
    font-size: 16px;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
}

.card {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 15px;
    padding: 18px;
    margin-bottom: 15px;
}

.welcome {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 35px;
    text-align: center;
    margin-top: 20px;
}

.welcome h2 {
    margin-bottom: 10px;
}

.example {
    background-color: #f8fafc;
    border-radius: 10px;
    padding: 12px;
    margin: 8px 0;
    text-align: left;
}

.status {
    padding: 12px;
    border-radius: 10px;
    background-color: #f0fdf4;
    border: 1px solid #bbf7d0;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0

st.markdown("""
<div class="header">
<h1>🤖 Smart PDF AI</h1>
<p>Your intelligent PDF question answering assistant</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:

    st.title("📄 Document")

    st.write("Upload your PDF and process it before asking questions.")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        os.makedirs("data", exist_ok=True)

        pdf_path = os.path.join(
            "data",
            uploaded_file.name
        )

        with open(pdf_path, "wb") as file:
            file.write(uploaded_file.getbuffer())

        st.markdown(
            f"""
            <div class="card">
                <b>📄 Selected document</b>
                <br><br>
                {uploaded_file.name}
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button(
            "⚡ Process Document",
            use_container_width=True
        ):

            with st.spinner("🔍 Reading your PDF..."):

                try:

                    chunk_count = add_pdf_to_database(
                        pdf_path
                    )

                    st.session_state.pdf_processed = True
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.chunk_count = chunk_count

                    st.success("✅ Document processed!")

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"❌ Processing error:\n{error}"
                    )

    st.divider()

    st.subheader("📊 Document Status")

    if st.session_state.pdf_processed:

        st.markdown(
            f"""
            <div class="status">
            🟢 <b>Ready to chat</b>
            <br><br>
            📄 {st.session_state.pdf_name}
            <br>
            🧩 {st.session_state.chunk_count} text chunks
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.warning("Upload and process a PDF first.")

    st.divider()

    if st.button(
        "🧹 Clear Conversation",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()

    st.divider()

    st.subheader("ℹ️ About")

    st.write(
        "This system uses Retrieval-Augmented Generation "
        "(RAG) to retrieve relevant information from your "
        "PDF before generating an answer."
    )

if len(st.session_state.messages) == 0:

    st.markdown("""
    <div class="welcome">

    <h2>👋 Welcome to Smart PDF AI</h2>

    <p>
    Upload a PDF from the sidebar and start asking questions.
    </p>

    <br>

    <b>💡 Try asking:</b>

    <div class="example">
    📌 What is this document about?
    </div>

    <div class="example">
    📌 Summarize the main points.
    </div>

    <div class="example">
    📌 Explain this topic in simple words.
    </div>

    <div class="example">
    📌 What are the important conclusions?
    </div>

    </div>
    """, unsafe_allow_html=True)

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )

question = st.chat_input(
    "💬 Ask anything about your PDF..."
)

if question:

    with st.chat_message("user"):

        st.markdown(question)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("assistant"):

        with st.spinner("🤖 Searching your PDF..."):

            try:

                answer = generate_answer(
                    question
                )

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

            except Exception as error:

                st.error(
                    f"❌ Error generating answer:\n{error}"
                )