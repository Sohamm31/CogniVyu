import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .ai_logic import classify_domain, retrieve_docs, generate_answer, DOMAIN_METADATA_MAP
from .database import get_db
from . import schemas
from .models import User, Message
from .ai_logic import classify_domain, retrieve_docs, generate_answer
from .auth_routes import get_current_user

router = APIRouter()


@router.post("/ask", response_model=schemas.QueryResponse)
def ask_query(request: schemas.QueryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    intended_domain = ""
    if request.domain and request.domain != "auto":
        intended_domain = request.domain
    else:
        intended_domain = classify_domain(request.query)

    retrieved_docs_with_scores = retrieve_docs(request.query, intended_domain)

    print("\n" + "="*50)
    print(f"DEBUGGING RETRIEVAL for Query: '{request.query}'")
    print(f"Intended Domain for Filter: '{intended_domain}' -> Metadata Tag: '{DOMAIN_METADATA_MAP.get(intended_domain)}'")
    print(f"Found {len(retrieved_docs_with_scores)} documents.")
    print("-"*50)

    if retrieved_docs_with_scores:
        for i, (doc, score) in enumerate(retrieved_docs_with_scores):
            print(f"  Document {i+1}:")
            print(f"    Score: {score:.4f}")
            print(f"    Metadata: {doc.metadata}")
            print(f"    Content Snippet: '{doc.page_content[:200].strip().replace('\\n', ' ')}...'")
            print("-"*20)
    else:
        print("  No documents were retrieved.")
    print("="*50 + "\n")

    retrieved_docs = [doc for doc, score in retrieved_docs_with_scores]

    validated_docs = []
    if request.domain and request.domain != "auto":
        expected_metadata_tag = DOMAIN_METADATA_MAP.get(request.domain)
        if expected_metadata_tag:
            for doc in retrieved_docs:
                if doc.metadata.get("domain") == expected_metadata_tag:
                    validated_docs.append(doc)
    else:
        validated_docs = retrieved_docs

    recent_messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(desc(Message.timestamp)).limit(5).all()
    recent_messages.reverse()
    chat_history = [(msg.human_message, msg.bot_message) for msg in recent_messages]

    answer = generate_answer(request.query, validated_docs, chat_history)

    new_message = Message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        human_message=request.query,
        bot_message=answer,
        domain=intended_domain,
    )
    db.add(new_message)
    db.commit()

    return schemas.QueryResponse(domain=intended_domain, answer=answer, conversation_id=conversation_id)



@router.get("/conversations", response_model=list[schemas.Conversation])
def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversations = (
        db.query(Message.conversation_id, Message.human_message)
        .filter(Message.user_id == current_user.id)
        .group_by(Message.conversation_id)
        .order_by(desc(Message.timestamp)) 
        .all()
    )
    
    return [schemas.Conversation(id=conv_id, title=title) for conv_id, title in conversations]


@router.get("/messages/{conversation_id}", response_model=list[schemas.MessageHistory])
def get_messages_for_conversation(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id,
            Message.user_id == current_user.id
        )
        .order_by(Message.timestamp)
        .all()
    )
    return messages
