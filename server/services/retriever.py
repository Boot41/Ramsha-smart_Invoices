from pydantic import BaseModel
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from fastapi import HTTPException
from db.db import get_pinecone_client, get_async_database
from models.llm import get_embedding_model, get_chat_model
from langchain_core.runnables import RunnablePassthrough, RunnableMap
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage
import os
import json
store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """ Retrieve or create a chat history for the session. """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]
def startRAG(retriever, user_id: str, file_name: str, user_prompt: str):
    """ Configure the RAG chain with retriever and model. """
    # Initialize the model
    try:
        model = get_chat_model()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize model: {str(e)}"
        )
    system_prompt = (
        f"{user_prompt}\n\n"
        "Use the following pieces of context to answer the question about the query provided by the user. "
        "Please generate your response by following these steps:\n"
        "1. You will be provided with relevant text chunks from the documents uploaded by the user. You need to judge the relevance of the text chunks to the user's query.\n"
        f"2. If the context doesn't provide enough information, just say that you don't know, don't try to make up an answer.\n"
        "3. Use three sentences maximum and keep the answer as concise as possible.\n"
        "4. Analyze Each Component: For each part, extract the most relevant information from the PDF file while considering the context of the conversation.\n"
        f"5. **IMPORTANT: Only use information from documents with the file name: '{file_name}'.**\n"
        "6. Present Your Final Response: Show only your final response without any additional explanations or details.\n\n"
        "{context}"
    )
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    def format_chat_history(chat_history):
        formatted_history = []
        for message in chat_history:
            if isinstance(message, HumanMessage):
                formatted_history.append(HumanMessage(content=message.content))
            elif isinstance(message, AIMessage):
                formatted_history.append(AIMessage(content=message.content))
        return formatted_history
    def execute_query(user_id, file_name, user_input):
        chat_history_memory = get_session_history(session_id=user_id)
        # Convert user input to an embedding
        try:
            embedding_model = get_embedding_model()
            query_embedding = embedding_model.embed_query(user_input)
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
        # Define the chain
        chain = (
            RunnableMap(
                {
                    "context": lambda x: context,  # Pass context directly
                    "input": lambda x: x["input"],
                    "chat_history": lambda x: format_chat_history(
                        x["chat_history_memory"].messages
                    ),
                }
            )
            | prompt
            | model
            | StrOutputParser()
        )
        # Invoke the chain
        try:
            response = chain.invoke(
                {
                    "input": user_input,
                    "chat_history_memory": chat_history_memory,
                }
            )
            # Update chat history
            chat_history_memory.add_user_message(user_input)
            chat_history_memory.add_ai_message(response)
            return response
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate response: {str(e)}"
            )
    return execute_query
import numpy as np
from fastapi import HTTPException
from pinecone import QueryResponse
from fastapi import HTTPException
import numpy as np
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
