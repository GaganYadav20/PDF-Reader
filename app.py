
import os
import tempfile
import streamlit as st

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Configure Streamlit
st.set_page_config(
    page_title="PDF Reader AI",
    page_icon="📚"
)

st.title("📚 Chat with your PDF")
st.write("Upload a PDF and ask questions about its content.")

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please configure OPENAI_API_KEY in your .env file.")
    st.stop()

# Initialize session state
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# OpenAI models
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# PDF uploader
uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)

# Process PDF
if uploaded_file:

    if st.button("Process PDF"):

        with st.spinner("Reading PDF..."):

            # Save uploaded PDF temporarily
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_file:

                temp_file.write(uploaded_file.getvalue())
                pdf_path = temp_file.name

            try:
                # Load PDF
                loader = PyPDFLoader(pdf_path)
                documents = loader.load()

                # Split text into chunks
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )

                chunks = splitter.split_documents(documents)

                if not chunks:
                    st.error("No readable text found in PDF.")
                    st.stop()

                # Create embeddings and FAISS database
                vectorstore = FAISS.from_documents(
                    documents=chunks,
                    embedding=embeddings
                )

                st.session_state.vectorstore = vectorstore
                st.session_state.chat_history = []

                st.success(
                    f"PDF processed successfully! "
                    f"{len(chunks)} chunks created."
                )

            finally:
                os.remove(pdf_path)


# Chat interface
if st.session_state.vectorstore:

    st.subheader("Ask questions about your PDF")

    # Display previous messages
    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    question = st.chat_input("Ask something about your PDF...")

    if question:

        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                # Retrieve relevant chunks
                retriever = st.session_state.vectorstore.as_retriever(
                    search_kwargs={"k": 4}
                )

                relevant_docs = retriever.invoke(question)

                context = "\n\n".join(
                    doc.page_content
                    for doc in relevant_docs
                )

                # Prompt template
                prompt = ChatPromptTemplate.from_messages([
                    (
                        "system",
                        """You are a helpful PDF assistant.

                        Answer the question using only the
                        provided PDF context.

                        If the answer is not available in the
                        context, say that the PDF does not
                        contain sufficient information.

                        PDF Context:
                        {context}
                        """
                    ),
                    (
                        "human",
                        "{question}"
                    )
                ])

                # Generate answer
                chain = prompt | llm

                response = chain.invoke({
                    "context": context,
                    "question": question
                })

                answer = response.content

                st.markdown(answer)

                # Show source pages
                with st.expander("View source pages"):

                    for doc in relevant_docs:

                        page = doc.metadata.get(
                            "page", "Unknown"
                        )

                        st.write(
                            f"Page {int(page) + 1 if isinstance(page, int) else page}"
                        )

                        st.write(doc.page_content[:500])

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

else:
    st.info("Upload and process a PDF to start chatting.")
    