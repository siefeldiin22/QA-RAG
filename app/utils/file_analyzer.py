from langchain.text_splitter import RecursiveCharacterTextSplitter
def chunk_text(text, chunk_size=1024, overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "؟", "،", " "],  # Arabic punctuation
        add_start_index=True
    )
    return splitter.split_text(text)

def chunk_docs(docs):
    all_chunks = []
    sources = []
    for doc in docs:
        chunks = chunk_text(doc["text"])  # your existing chunk_text function
        all_chunks.extend(chunks)
        sources.extend([doc["source"]] * len(chunks))
    return all_chunks,sources