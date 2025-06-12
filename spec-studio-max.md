
# ✅ Design Specification: Legal LLM Workstation (Mac Studio M4 Max, 128GB)

## 🎯 Use Case: Local AI Legal Assistant
- Fully offline, air-gapped system
- Support for legal document upload, embedding, storage, and retrieval
- LLM-powered Q&A with legal awareness
- Real-time streaming responses

---

## 💻 Hardware: Mac Studio M4 Max
- **CPU**: 16-core
- **GPU**: 40-core
- **RAM**: 128 GB Unified
- **SSD**: 1–2 TB (flexible, at least 1 TB recommended)
- **OS**: macOS Sonoma (latest)

---

## 🧠 LLM (Language Model)
- **Primary**: `Nous-Hermes-2 13B` (GGUF, Q5_K_M quant)
- **Alternatives**:
  - `Mixtral-8x7B Instruct` (MoE, Q4_K_M)
  - `Yi-34B` (Q4_K_M)

### Runtime:
- **Tool**: `llama.cpp`
- **Quantization Format**: GGUF
- **Inference Params**:
  ```bash
  ./main -m nous-hermes-2-13b.Q5_K_M.gguf --interactive-first -n 4096 --color -c 4096 --threads 10 --n-gpu-layers 40 --temp 0.7
  ```

---

## 🗂️ Document Pipeline
### Ingestion
- Accepts: PDF, Word, plain text
- File watcher (optional)

### Chunking
- **Chunker**: `LangChain RecursiveCharacterTextSplitter`
- Settings:
  - Chunk size: 512
  - Overlap: 64

### Embedding
- **Model**: `intfloat/e5-small-v2` or `BAAI/bge-small-en`
- **Tool**: `sentence-transformers`
- Offline capable

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/e5-small-v2")
```

### Vector Store
- **Option 1**: `FAISS` (lightweight, no server)
- **Option 2**: `Qdrant` (with ARM-native build for macOS)

### RAG Layer
- **Framework**: `LangChain` or `custom FastAPI`
- Smart retrieval → reranker → prompt injection

---

## 🔁 LLM Integration
- Streaming Q&A
- Prompt Template:
  ```jinja
  You are a legal assistant. Answer based only on the context.

  Context:
  {context}

  Question:
  {question}
  ```

---

## 🧩 Optional Enhancements
- Summarization step per doc (using same LLM)
- Frontend UI: Tauri / Electron or Flask+React local app
- Add OCR for scanned PDFs using `tesseract`

---

## 📦 Packages List
```bash
brew install llama.cpp qdrant langchain tesseract
pip install sentence-transformers faiss-cpu langchain fastapi uvicorn
```

---

## 🧠 Notes
- You can run 65B models but will sacrifice speed and concurrency
- LLM runs directly with Metal acceleration via `llama.cpp`
- 13B Q5_K is optimal for legal Q&A latency vs quality trade-off

---

## 🔐 Legal Angle
- Trained/fine-tuned on public legal corpora
- Ensure client doc redaction before local training (optional phase 2)
- 100% offline model = safe for privacy-sensitive workflows
