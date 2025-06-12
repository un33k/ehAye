
# ✅ Design Specification: Legal LLM Workstation (Mac mini M4 Pro, 64GB)

## 🎯 Use Case: Local AI Legal Assistant
- Offline AI system for law firms
- Legal document ingestion, embedding, search, and summarization
- Interactive legal Q&A

---

## 💻 Hardware: Mac mini M4 Pro
- **CPU**: 14-core
- **GPU**: 20-core
- **RAM**: 64 GB Unified
- **SSD**: 1 TB
- **Ethernet**: 10 Gb (recommended)
- **OS**: macOS Sonoma or later

---

## 🧠 LLM (Language Model)
- **Primary**: `Nous-Hermes-2 13B` (GGUF, Q5_K_M)
- **Secondary (faster)**: `Nous-Hermes-2 Mistral 7B` (Q4_K_M)

### Runtime:
- **Tool**: `llama.cpp`
- **Quantization Format**: GGUF
- **Command Example**:
  ```bash
  ./main -m nous-hermes-2-13b.Q5_K_M.gguf --interactive-first -n 4096 --color -c 4096 --threads 8 --n-gpu-layers 20 --temp 0.7
  ```

---

## 🗂️ Document Pipeline
### Ingestion
- File types: PDFs, Word Docs, TXT
- Drag-and-drop or monitored folder

### Chunking
- **Tool**: `LangChain RecursiveCharacterTextSplitter`
- Parameters:
  - Chunk size: 512
  - Overlap: 64

### Embedding
- **Model**: `intfloat/e5-small-v2` or `bge-small-en`
- **Library**: `sentence-transformers`

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/e5-small-v2")
```

### Vector Store
- **Preferred**: `FAISS`
- **Optional**: `Qdrant` (compiled for ARM)

### RAG Flow
- Use `LangChain` or custom search function
- Reranker improves final document context selection

---

## 🔁 LLM Integration
- Prompt injection + streaming response

Prompt Template:
```jinja
You are a legal assistant. Only answer based on the context.

Context:
{context}

Question:
{question}
```

---

## 📦 Required Tools and Packages
```bash
brew install llama.cpp langchain faiss tesseract
pip install sentence-transformers langchain fastapi uvicorn
```

---

## 🧠 Notes
- 64GB RAM limits model size: 34B possible at Q4_K_M, but 13B is ideal
- Very fast with 7B and 13B, supports concurrent user queries
- Mac mini M4 Pro offers Studio-level inference in compact form factor

---

## 🔐 Legal Considerations
- All processing stays local
- Use in air-gapped environments
- Optional redaction + audit logging pipeline before ingestion

---

## 🧩 Optional UI / Features
- Tauri or Electron UI
- Summarization of uploaded cases
- Internal file search + view
- PDF OCR via `tesseract` for scanned case files
