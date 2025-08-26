from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
import os
from .config import settings 


os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY


llm = ChatOpenAI(
    model="gpt-oss-20b:free",
    temperature=0,
    openai_api_key=settings.OPENROUTER_KEY,
    base_url="https://openrouter.ai/api/v1"
)

index_name = "all-in-one-agent"
embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

vectorstore = PineconeVectorStore.from_existing_index(index_name, embeddings)
DOMAIN_METADATA_MAP = {
    "Health & Wellness": "wellness",
    "Finance & Budgeting": "finance",
    "Home & DIY": "home_diy",
    "Travel & Local Guide": "travel",
}


template = """
You are a specialized assistant that answers questions STRICTLY based on the provided documents and chat history.

*** CRITICAL RULES ***
1.  **Grounding:** Your entire response MUST be based SOLELY on the information within the "Retrieved Documents" section below.
2.  **Domain Extraction:** If the question involves domains, you MUST return ONLY the unique values of the field "domain" from the retrieved documents.
      - Each domain should be listed on a new line.
      - Do not add explanations, summaries, or extra text.
3.  **Use Chat History:** Pay close attention to the "Chat History" to understand follow-up questions. If the user asks "what about the second one?", use the history to identify what "the second one" refers to.
4.  **No External Knowledge:** DO NOT use any external knowledge, personal opinions, or information you were trained on. Your knowledge is limited to the documents provided.
5.  **Handling Missing Information:** If the documents and history do not contain enough information to answer the question, you MUST explicitly state: "The provided materials do not contain enough information to answer this question."
6.  **Citation:** You must cite the source for every piece of information you provide, using the format [source_file | page]. 
      - If only domains are asked, citations are NOT required.
7.  **Conciseness & Formatting:** Keep the response under 400 words and use Markdown for clarity (headings, bullet points, bold text).

---
Chat History:
{chat_history}
---
Retrieved Documents:
{context}
---
Current Question:
{question}
"""




prompt_template = PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)



def classify_domain(query: str):
   
    domain_prompt = f"""
Classify the following question into ONE of the domains listed below.
Respond with ONLY the domain name, exactly as it appears in the list. Do not add numbers, punctuation, or any other text.

Domains:
- Finance & Budgeting
- Travel & Local Guide
- Home & DIY
- Hobbies & Skills
- Health & Wellness

Question: "{query}"

Domain:"""
    response = llm.invoke(domain_prompt)
    return response.content.strip()



def retrieve_docs(query: str, domain: str, k: int = 4):
    
    metadata_tag = DOMAIN_METADATA_MAP.get(domain)
    if not metadata_tag:
        return []

   
    docs_with_scores = vectorstore.similarity_search_with_score(
        query,
        k=k,
        filter={"domain": metadata_tag}
    )
    return docs_with_scores



def generate_answer(query: str, docs, chat_history=None):
    if chat_history:
        history_str = "\n".join([f"Human: {q}\nAI: {a}" for q, a in chat_history])
    else:
        history_str = "No history yet."

    context = "\n\n".join([
        f"[{d.metadata['domain']} | {d.metadata['source_file']} | page {d.metadata.get('page', '?')}]\n{d.page_content}"
        for d in docs
    ])

    final_prompt = prompt_template.format(
        chat_history=history_str,
        context=context,
        question=query
    )
    response = llm.invoke(final_prompt)
    return response.content