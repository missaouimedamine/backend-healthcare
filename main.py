from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import analysis, reports, chatbot, infos
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from app.utils.rag import get_chain_disease, get_chain_infos, get_chain_chat
import os, asyncio
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

@asynccontextmanager
async def lifespan(app: FastAPI):
    embedding_model = await asyncio.to_thread(
        HuggingFaceEmbeddings,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"use_auth_token": HUGGINGFACE_API_KEY}
    )

    vectorstore = await asyncio.to_thread(
        FAISS.load_local,
        r"app/data/faiss_db",
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )

    llm = ChatOpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=MISTRAL_API_KEY,
        model_name="mistral-medium"
    )

    app.state.diagnosis_chain = get_chain_disease(llm, vectorstore)
    app.state.info_chain = get_chain_infos(llm, vectorstore)
    app.state.chat_chain = get_chain_chat(llm=llm, vectorstore=vectorstore)

    yield

app = FastAPI(
    title="Symptom Checker API",
    description="API for symptom checking and analysis",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(infos.router, prefix="/api/infos", tags=["infos"])
app.include_router(reports.router, prefix="/api/reports", tags=["report"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Symptom Checker API is running"}
