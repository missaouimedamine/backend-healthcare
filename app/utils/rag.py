
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
import warnings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain, LLMChain, StuffDocumentsChain
warnings.filterwarnings("ignore")
import os


def get_chain_infos(llm, vectorstore):
# Prompt templates
    prompt_template = ChatPromptTemplate.from_template("""
You are a knowledgeable and precise medical assistant. Your task is to extract and summarize key information 
from the raw disease content into a structured, clean, and medically accurate Python dictionary format with the following keys:
['Title', 'Overview', 'Symptoms', 'Causes', 'Risk factors', 'Complications', 'Prevention',
 'When to see a doctor', 'Diagnosis', 'Treatment', 'Lifestyle and home remedies', 'Medical Recommendation']

Disease Raw Info:
{context}

Guidelines:
- Provide concise, factual, and medically sound content for each field.
- For 'Medical Recommendation':
  • Give the most accurate and actionable advice based on the disease context.
  • If medical consultation is required, specify the **exact medical specialty** (e.g., cardiologist, neurologist).
  • If home care is sufficient, describe **precise steps or remedies** clearly and briefly.
  • Keep it **tailored, specific, and informative**—avoid vague generalities.
  • When applicable, be brief without sacrificing clarity or accuracy.

Output:
Return only a valid JSON-like Python dictionary containing the summarized disease information under each specified key. Do not include any extra commentary or explanation.
""")
    # Initialize the RetrievalQA chain
    info_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 1}),
    chain_type="stuff",  # or "map_reduce", etc. depending on what you want
    chain_type_kwargs={"prompt": prompt_template},
    return_source_documents=False
)

    return info_chain

def get_chain_disease(llm, vectorstore):

    prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a medical diagnosis assistant.

Use the context below to identify which disease best matches the given symptoms.

Return your response in this format as a JSON array of objects WITHOUT any additional text:
[
  {{
    "disease": "Disease Name",
    "probability": 87
  }},
  {{
    "disease": "Other Likely Disease",
    "probability": 13
  }}
]

### Context:
{context}

### Symptoms:
{question}
"""
)

# RAG Chains
    diagnosis_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=False
)
    return diagnosis_chain

def get_chain_chat(llm, vectorstore):
    # Memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # Prompts
    answer_prompt_template = ChatPromptTemplate.from_template("""
You are a bilingual knowledgeable and precise medical assistant fluent in both English and French. Your task is to provide accurate and concise answers to medical queries.
Detect the language of the query (English or French) and respond in the same language.
When answering, please ensure that your response is clear with no extra explanation. If the question is ambiguous or requires further clarification, ask for more details.

Context: {context}
Question: {question}
Answer:
""")

    qa_llm_chain = LLMChain(llm=llm, prompt=answer_prompt_template)

    combine_docs_chain = StuffDocumentsChain(
        llm_chain=qa_llm_chain,
        document_variable_name="context"
    )

    condense_question_prompt = PromptTemplate.from_template("""
Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question.

Chat History:
{chat_history}
Follow-Up Input: {question}
Standalone question:
""")

    question_generator = LLMChain(llm=llm, prompt=condense_question_prompt)

    # Conversational chain
    chat_chain = ConversationalRetrievalChain(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
        memory=memory,
        question_generator=question_generator,
        combine_docs_chain=combine_docs_chain,
        return_source_documents=False
    )
    return chat_chain
