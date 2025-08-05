from fastapi import APIRouter, UploadFile, File,Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path
import time
import numpy as np
import faiss
import pickle
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from fastapi import HTTPException
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.database.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter()

UPLOAD_DIR = Path("docs")
UPLOAD_DIR.mkdir(exist_ok=True)

# Store text mapping to vector IDs (so you can later retrieve documents)
id_to_text = {}

@router.post("/upload_files")
async def upload(files: List[UploadFile] = File(...),
                current_user: User = Depends(get_current_user)):
    print(current_user)
    if not current_user:
        raise HTTPException(status_code=400, detail="User Is Not Signed In.")
    
    # Read all files at once into memory BEFORE the generator
    file_contents = []
    for file in files:
        content = await file.read()
        file_contents.append((file.filename, content))
    
    async def stream_chunks():
        try:
            yield "Starting processing... 0%\n"

            all_chunks = []
            total_files = len(file_contents)
            processed_files = 0

            for filename, content in file_contents:
                file_path = UPLOAD_DIR / filename
                with open(file_path, "wb") as f:
                    f.write(content)

                progress = int((processed_files / total_files) * 30)  # File processing is 30% of total
                yield f"Saved {filename}... {progress}%\n"

                # Load file
                if filename.endswith(".pdf"):
                    loader = PyPDFLoader(str(file_path))
                elif filename.endswith(".txt"):
                    loader = TextLoader(str(file_path), encoding="utf-8")
                else:
                    yield f"Unsupported file type: {filename} {progress}%\n"
                    continue

                docs = loader.load()
                splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = splitter.split_documents(docs)
                all_chunks.extend(chunks)

                processed_files += 1
                progress = int((processed_files / total_files) * 30)
                yield f"Split {filename} into {len(chunks)} chunks... {progress}%\n"

            if not all_chunks:
                yield "No valid documents to index. 30%\n"
                return

            # Create embeddings for chunks
            yield "Generating embeddings... 40%\n"
            embeddings_model = HuggingFaceEmbeddings()
            texts = [chunk.page_content for chunk in all_chunks]
            yield f"Generating {len(texts)} embeddings... 50%\n"
            embeddings = embeddings_model.embed_documents(texts)
            dim = len(embeddings[0])

            yield "Creating FAISS index... 80%\n"
            # Convert embeddings to float32 numpy array
            embeddings_np = np.array(embeddings).astype("float32")

            # Create FAISS index
            index = faiss.IndexFlatL2(dim)
            index.add(embeddings_np)

            yield "Saving index... 90%\n"
            Path("faiss_indecies").mkdir(exist_ok=True)
            faiss.write_index(index, f"faiss_indecies/{current_user.id}.faiss")
            with open(f"faiss_indecies/{current_user.id}.pkl", "wb") as f:
                pickle.dump(chunks, f)
            yield "All documents processed and indexed successfully. 100%\n"
        
        except Exception as e:
            yield f"Error: {str(e)} 0%\n"

    return StreamingResponse(stream_chunks(), media_type="text/plain")