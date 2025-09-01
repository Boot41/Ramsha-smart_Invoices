from pydantic import BaseModel
from fastapi import HTTPException
from db.db import get_pinecone_client, get_async_database
from models.llm.embedding import get_embedding_service
from models.llm.base import get_model
from typing import Dict, List, Any
import os
import json
# Simple in-memory chat history store
chat_history_store: Dict[str, List[Dict[str, str]]] = {}

def get_session_history(session_id: str) -> List[Dict[str, str]]:
    """ Retrieve or create a chat history for the session. """
    if session_id not in chat_history_store:
        chat_history_store[session_id] = []
    return chat_history_store[session_id]

def add_to_chat_history(session_id: str, role: str, message: str):
    """Add a message to the chat history"""
    history = get_session_history(session_id)
    history.append({"role": role, "content": message})
    
    # Keep only last 10 messages to avoid context overflow
    if len(history) > 10:
        chat_history_store[session_id] = history[-10:]
def startRAG(retriever, user_id: str, file_name: str, user_prompt: str):
    """ Configure the RAG system using native google-adk implementation. """
    # Initialize the model and embedding service
    try:
        model = get_model()
        embedding_service = get_embedding_service()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize model or embedding service: {str(e)}"
        )
    
    def create_system_prompt(context: str, history_str: str = "") -> str:
        return f"""{user_prompt}

Use the following pieces of context to answer the question about the query provided by the user.
Please generate your response by following these steps:
1. You will be provided with relevant text chunks from the documents uploaded by the user. Judge the relevance of the text chunks to the user's query.
2. If the context doesn't provide enough information, just say that you don't know, don't try to make up an answer.
3. Use three sentences maximum and keep the answer as concise as possible.
4. Analyze each component: Extract the most relevant information from the PDF file while considering the context of the conversation.
5. **IMPORTANT: Only use information from documents with the file name: '{file_name}'.**
6. Present your final response: Show only your final response without any additional explanations or details.

{history_str}

Context:
{context}"""
    
    def format_chat_history(chat_history: List[Dict[str, str]]) -> str:
        """Format chat history for inclusion in prompt"""
        if not chat_history:
            return ""
        
        formatted_lines = []
        for message in chat_history[-5:]:  # Only include last 5 messages
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "user":
                formatted_lines.append(f"Human: {content}")
            elif role == "assistant":
                formatted_lines.append(f"Assistant: {content}")
        
        if formatted_lines:
            return "Recent conversation history:\n" + "\n".join(formatted_lines) + "\n"
        return ""
    def execute_query(user_id, file_name, user_input):
        chat_history = get_session_history(session_id=user_id)
        # Convert user input to an embedding
        try:
            query_embedding = embedding_service.embed_query(user_input)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embedding: {str(e)}"
            )
        # Retrieve relevant context from Pinecone
        try:
            retrieved_doc_metadata = load_vector_store_for_user(
                user_id, query_embedding
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve documents: {str(e)}"
            )
        # Fetch and prepare context from document store using text chunks
        if retrieved_doc_metadata:
            documents_content = [
                doc["metadata"].get("text", "")
                for doc in retrieved_doc_metadata
                if "metadata" in doc and "text" in doc["metadata"]
            ]
            context = " ".join(documents_content)
            if not context:
                context = "No relevant documents found"
        else:
            context = "No documents found"
        # Generate response using google-adk model directly
        try:
            # Format chat history and create prompt
            history_str = format_chat_history(chat_history)
            full_prompt = create_system_prompt(context, history_str)
            full_prompt += f"\n\nUser Question: {user_input}\n\nAnswer:"
            
            # Generate response using the model
            response_obj = model.generate_content(full_prompt)
            response = response_obj.text
            
            # Update chat history
            add_to_chat_history(user_id, "user", user_input)
            add_to_chat_history(user_id, "assistant", response)
            
            return response
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate response: {str(e)}"
            )
    return execute_query

import numpy as np
from pinecone import QueryResponse
def load_vector_store_for_user(user_id: str, query_embedding: np.ndarray):
    """
    Load all vector documents from Pinecone based on user_id only.
    Perform similarity search on the vectors for a given query embedding.
    Args:
        user_id (str): The user ID.
        query_embedding (numpy.ndarray): The query embedding for similarity search.
        index: Pinecone index instance.
    Returns:
        list: List of top matching vector documents sorted by similarity.
    Raises:
        HTTPException: If no documents are found or an error occurs.
    """
    try:
        # Normalize the query embedding (optional, but can be a good practice)
        # normalized_query = query_embedding / np.linalg.norm(query_embedding)
        # Query the Pinecone index
        index = get_pinecone_client()
        response: QueryResponse = index.query(
            vector=query_embedding,
            top_k=10,  # You can adjust top_k as needed
            include_metadata=True,
            filter={
                "user_id": user_id,
            },
        )
        # Check if results are found
        if not response.matches:
            print(f"No documents found for user_id: {user_id}")
            raise HTTPException(
                status_code=404,
                detail="No documents found for user in vector store",
            )
        print(f"Found documents: {[match.id for match in response.matches]}")
        # Extract vectors and metadata from the query results
        vector_data = []
        for match in response.matches:
            metadata = match.metadata if match.metadata else {}
            vector_data.append(
                {
                    "vector": np.array(match.values, dtype=np.float32),
                    "metadata": {
                        "id": match.id,
                        **metadata,  # Include all metadata fields
                    },
                    "similarity": match.score,
                }
            )
        if not vector_data:
            print(f"No valid vectors found for user_id: {user_id}")
            raise HTTPException(
                status_code=404,
                detail="No valid vectors found in vector store"
            )
        return vector_data
    except Exception as e:
        print(f"Error while querying Pinecone: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error while querying vector store: {str(e)}"
        )
