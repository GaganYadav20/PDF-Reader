# PDF Reader AI

PDF Reader AI is a Streamlit application that lets you upload a PDF and ask
natural-language questions about its contents. It uses a retrieval-augmented
generation (RAG) pipeline:

1. Extract text from the uploaded PDF.
2. Split the extracted text into overlapping chunks.
3. Generate OpenAI embeddings for the chunks.
4. Store the embeddings in an in-memory FAISS vector index.
5. Retrieve the most relevant chunks for each question.
6. Ask `gpt-4o-mini` to answer using only the retrieved PDF context.

The interface also displays the source pages and a short text preview for the
chunks used to answer each question.

## Features

- Upload PDF files directly from the browser.
- Extract text from every readable PDF page using `PyPDFLoader`.
- Chunk long documents into searchable sections.
- Semantic search over document chunks with FAISS.
- Question answering using OpenAI's `gpt-4o-mini` model.
- Conversation history for the current browser session.
- Source-page references for retrieved context.
- Clear feedback while a PDF is being processed or a response is generated.

## Requirements

- Python 3.12 or later. The repository pins Python 3.12 in
  `.python-version` and declares `>=3.12` in `pyproject.toml`.
- An OpenAI API key with access to:
  - `text-embedding-3-small`
  - `gpt-4o-mini`
- Internet access when creating embeddings and generating answers.
- A PDF containing extractable text. Scanned/image-only PDFs require OCR,
  which this application does not currently perform.

## Installation

### 1. Clone or open the project

From a terminal, change to the project directory:

```powershell
cd D:\Projects\pdf-Reader
```

### 2. Create and activate a virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation because of the execution policy, activate
the environment through Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The runtime dependencies are maintained in `requirements.txt`. The current
`pyproject.toml` contains project metadata but does not duplicate that
dependency list, so install from `requirements.txt` for this application.

### 4. Configure the OpenAI API key

Create a file named `.env` in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
```

Do not commit `.env` or share the API key. The application loads this file
with `python-dotenv` before it initializes the Streamlit interface. If the key
is missing, the application displays an error and stops.

## Running the application

With the virtual environment activated, start Streamlit:

```powershell
python -m streamlit run app.py
```

Streamlit normally opens the application in a browser. If it does not, open
the URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Using the application

1. Open the Streamlit URL.
2. Select a PDF with the **Upload your PDF** control.
3. Click **Process PDF**.
4. Wait for the success message showing how many chunks were created.
5. Enter a question in the chat input.
6. Review the answer and expand **View source pages** to inspect the retrieved
   page numbers and text previews.

Processing happens only after clicking **Process PDF**. Uploading a file alone
does not create the index.

To switch documents, upload another PDF and process it. The new document
replaces the previous in-memory vector store and clears the displayed chat
history.

## How the code works

The application is implemented in `app.py`.

### Startup and configuration

- `load_dotenv()` loads environment variables from `.env`.
- `st.set_page_config()` sets the page title and icon.
- The application checks `OPENAI_API_KEY` before proceeding.
- Streamlit session state stores:
  - `vectorstore`: the current FAISS index.
  - `chat_history`: messages displayed in the current session.

### PDF processing pipeline

When **Process PDF** is clicked:

1. The uploaded bytes are written to a temporary `.pdf` file.
2. `PyPDFLoader` reads the file into page-level LangChain documents.
3. `RecursiveCharacterTextSplitter` creates chunks with:
   - `chunk_size=1000`
   - `chunk_overlap=200`
4. If no chunks are produced, the application reports that the PDF has no
   readable text.
5. `FAISS.from_documents()` generates embeddings with
   `text-embedding-3-small` and builds the vector index.
6. The temporary file is deleted in a `finally` block.

The index is held in Streamlit session memory; it is not saved to disk.

### Question-answering pipeline

For each question:

1. The FAISS index is exposed as a retriever.
2. The four most relevant chunks are retrieved (`k=4`).
3. Their page content is joined into the prompt context.
4. A system prompt instructs the model to answer only from that context and
   to say when the PDF does not contain enough information.
5. `gpt-4o-mini` generates the response with `temperature=0`.
6. The answer is added to the session chat history.
7. Each retrieved document's page number and first 500 characters are shown
   in the source expander.

## Project structure

```text
pdf-Reader/
├── app.py             # Streamlit UI and PDF RAG pipeline
├── requirements.txt   # Runtime Python dependencies
├── pyproject.toml     # Project metadata and Python requirement
├── .python-version    # Local Python version selection
├── .env               # Local API key configuration (not committed)
└── README.md          # Project documentation
```

The `.venv/` directory is a local virtual environment and is excluded from
version control.

## Configuration and tuning

The main RAG settings are currently constants in `app.py`:

| Setting | Current value | Purpose |
| --- | ---: | --- |
| Embedding model | `text-embedding-3-small` | Creates vectors for PDF chunks |
| Chat model | `gpt-4o-mini` | Generates answers |
| Temperature | `0` | Makes answers more deterministic |
| Chunk size | `1000` characters | Maximum text size per chunk |
| Chunk overlap | `200` characters | Preserves context between chunks |
| Retrieved chunks | `4` | Amount of context sent per question |
| Source preview | `500` characters | Text shown per retrieved chunk |

These values can be adjusted in `app.py` if document size, answer quality,
latency, or API cost requirements change. Increasing the number of retrieved
chunks provides more context but also increases prompt size and cost.

## Limitations

- Only PDF uploads are accepted.
- Text extraction depends on the PDF's embedded text. Image-only scans are
  not OCR-processed.
- The FAISS index is in memory and is lost when the Streamlit session ends or
  the application restarts.
- Chat history is session-local and is not persisted.
- Each processed PDF creates new embedding requests.
- OpenAI API usage can incur charges and requires network access.
- The model can only be as accurate as the extracted text and retrieved
  chunks. Questions requiring information outside the PDF are intentionally
  answered with an insufficient-context response.
- There is no authentication or multi-user access control in the application.
  Do not expose the development server publicly without adding appropriate
  security controls.

## Troubleshooting

### `Please configure OPENAI_API_KEY in your .env file.`

Confirm that:

- The file is named exactly `.env`.
- It is located in the same project directory as `app.py`.
- The variable is spelled `OPENAI_API_KEY`.
- The key is active and has permission to use the configured models.

Restart Streamlit after changing `.env`.

### No readable text found in PDF

The PDF likely contains scanned pages or images rather than an embedded text
layer. Run OCR on the document first, then upload the OCR-enabled PDF.

### Import or module errors

Make sure the virtual environment is activated and reinstall the declared
dependencies:

```powershell
python -m pip install -r requirements.txt
```

Also verify that the command is using the expected interpreter:

```powershell
python --version
python -m pip --version
```

### Processing is slow or expensive

Large PDFs require more extraction, embedding, and indexing work. Consider
processing a smaller document, reducing the chunk count, or changing the
embedding model only after evaluating answer quality and compatibility.

### Answers do not contain the expected information

Check the source-page previews first. If the relevant passage was not
retrieved, the document may need different chunking settings, a higher
retrieval count, or cleaner extracted text.

## Security and privacy

The application sends PDF-derived text to OpenAI when it creates embeddings
and generates answers. Do not upload confidential or regulated documents
unless that use is permitted by your organization's policies and OpenAI
account configuration.

Keep the API key only in environment configuration. Never place it in
`app.py`, commit it to source control, or include it in screenshots and logs.

## Development notes

There are currently no automated tests or persistent storage components in the
project. When changing the RAG pipeline, manually verify at least:

1. A normal text PDF can be processed.
2. A PDF with no extractable text shows the expected error.
3. A question displays an answer and source-page previews.
4. Processing a second PDF clears the previous chat history.

## License

No license file or license declaration is currently included in the project.
Add an explicit license before distributing the application.