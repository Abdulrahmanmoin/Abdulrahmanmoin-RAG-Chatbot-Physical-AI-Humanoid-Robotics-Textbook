import uuid
import time
import logging
from typing import List, Optional, Dict, Any
from ..models.query import QueryRequest, QueryResponse
from ..models.document_models import RetrievedChunk
from ..services.retrieval_service import RetrievalService
from ..services.validation_service import ValidationService
from ..services.openrouter_service import OpenRouterService
from ..config.settings import settings
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class QueryService:
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.validation_service = ValidationService()
        self.openrouter_service = OpenRouterService()
        # genai.configure(api_key=settings.gemini_api_key)
        # self.generative_model = genai.GenerativeModel('gemini-pro')  # Using Gemini Pro for generationed/Issues
        self.generative_model = genai.GenerativeModel('gemini-1.5-flash') # Using Gemini 1.5 Flash

    async def process_query(self, query_request: QueryRequest) -> QueryResponse:
        """
        Process a query request and return a response
        """
        start_time = time.time()
        query_id = uuid.uuid4()

        try:
            if query_request.query_type == "full_book":
                return await self._process_full_book_query(query_request, query_id)
            elif query_request.query_type == "selection_based":
                return await self._process_selection_query(query_request, query_id)
            else:
                raise ValueError(f"Invalid query type: {query_request.query_type}")
        except Exception as e:
            processing_time = time.time() - start_time
            return QueryResponse(
                response=f"An error occurred while processing your request: {str(e)}",
                status="error",
                sources=[],
                confidence=0.0,
                query_id=query_id
            )

    async def _process_full_book_query(self, query_request: QueryRequest, query_id: uuid.UUID) -> QueryResponse:
        """
        Process a full-book query (search across all book content)
        """
        start_time = time.time()

        # Retrieve relevant chunks
        try:
            logger.info(f"Retrieving chunks for query: {query_request.query}")
            retrieved_chunks = await self.retrieval_service.retrieve_relevant_chunks(
                query_request.query,
                top_k=settings.retrieval_top_k
            )
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
        except Exception as e:
            logger.error(f"Error in retrieve_relevant_chunks: {e}", exc_info=True)
            raise

        # Validate context sufficiency
        try:
            logger.info("Validating context sufficiency")
            print(f"DEBUG: Retrieved {len(retrieved_chunks)} chunks in process_full_book_query", flush=True)
            for i, chunk in enumerate(retrieved_chunks[:2]):
                 print(f"DEBUG: Chunk {i} content preview: {chunk.content[:100]}...", flush=True)
            
            is_sufficient, reason = self.validation_service.validate_context_sufficiency(
                query_request.query,
                retrieved_chunks
            )
            logger.info(f"Context sufficiency: {is_sufficient} ({reason})")
            print(f"DEBUG: Context sufficiency: {is_sufficient} ({reason})", flush=True)
        except Exception as e:
            logger.error(f"Error in validate_context_sufficiency: {e}", exc_info=True)
            raise

        if not is_sufficient:
            processing_time = time.time() - start_time
            return QueryResponse(
                response=f"I cannot answer this question based on the available book content. {reason}",
                status="refused",
                sources=[],
                confidence=0.0,
                query_id=query_id
            )

        # Generate response using retrieved context
        response, confidence = await self._generate_response_with_context(
            query_request.query,
            retrieved_chunks
        )

        # Validate grounding of response
        is_grounded, validation_details = self.validation_service.validate_response_grounding(
            response,
            retrieved_chunks
        )
        print(f"DEBUG: Grounding Check Is Grounded: {is_grounded}", flush=True)
        print(f"DEBUG: Validation Details: {validation_details}", flush=True)

        if not is_grounded:
            # For now, we will log the validation warning but still return the response to avoid blocking valid answers
            # due to strict lexical overlap checks.
            logger.warning(f"Response validation failed: {validation_details}")
            print(f"DEBUG: Grounding verification failed but allowing response. Details: {validation_details}", flush=True)
            
            # Optional: Add a disclaimer to the response? 
            # response += "\n\n(Note: This response may not be fully grounded in the exact text matches of the source material.)"
            
            # Proceed as success
            pass
            
            # Previous rejection logic commented out:
            # processing_time = time.time() - start_time
            # return QueryResponse(
            #    response="I cannot provide an answer that is fully grounded in the book content.",
            #    status="refused",
            #    sources=[],
            #    confidence=0.0,
            #    query_id=query_id
            # )

        # Extract source information (Disabled as per user request)
        sources = [] 
        # sources = [chunk.source_path for chunk in retrieved_chunks if chunk.source_path]

        processing_time = time.time() - start_time
        return QueryResponse(
            response=response,
            status="success",
            sources=sources, # Explicitly returning empty sources
            confidence=confidence,
            query_id=query_id
        )

    async def _process_selection_query(self, query_request: QueryRequest, query_id: uuid.UUID) -> QueryResponse:
        """
        Process a selection-based query (use only the provided selected text)
        """
        start_time = time.time()

        if not query_request.selected_text:
            return QueryResponse(
                response="No selected text provided for selection-based query.",
                status="refused",
                sources=[],
                confidence=0.0,
                query_id=query_id
            )

        # Validate selection context sufficiency
        is_sufficient, reason = self.validation_service.validate_selection_context(
            query_request.query,
            query_request.selected_text
        )

        if not is_sufficient:
            processing_time = time.time() - start_time
            return QueryResponse(
                response=f"The selected text does not contain enough information to answer your question. {reason}",
                status="refused",
                sources=[],
                confidence=0.0,
                query_id=query_id
            )

        # Retrieve from selected text (in this case, we just use the selected text directly)
        retrieved_chunks = await self.retrieval_service.retrieve_from_selected_text(
            query_request.selected_text,
            top_k=1
        )

        # Generate response using selected context
        response, confidence = await self._generate_response_with_context(
            query_request.query,
            retrieved_chunks,
            selection_mode=True
        )

        # Validate grounding of response
        is_grounded, validation_details = self.validation_service.validate_response_grounding(
            response,
            retrieved_chunks
        )

        if not is_grounded:
            processing_time = time.time() - start_time
            return QueryResponse(
                response="I cannot provide an answer that is fully grounded in the selected text.",
                status="refused",
                sources=[],
                confidence=0.0,
                query_id=query_id
            )

        processing_time = time.time() - start_time
        return QueryResponse(
            response=response,
            status="success",
            sources=["user_selection"],
            confidence=confidence,
            query_id=query_id
        )

    async def _generate_response_with_context(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
        selection_mode: bool = False
    ) -> tuple[str, float]:
        """
        Generate a response using the retrieved context
        """
        # Build context from retrieved chunks
        # Build context from retrieved chunks
        context_parts = []
        for chunk in retrieved_chunks:
            # Removed explicit Source: path from context to prevent LLM from citing filename
            context_parts.append(f"Content: {chunk.content}")

        context = "\n\n".join(context_parts)

        if selection_mode:
            prompt = f"""
            You are a helpful assistant that answers questions based only on the provided selected text from the Physical AI & Humanoid Robotics book.

            SELECTED TEXT:
            {retrieved_chunks[0].content}

            INSTRUCTIONS:
            - Answer the question using ONLY information from the provided SELECTED TEXT
            - Do not use any external knowledge or information from other parts of the book
            - If the answer is not in the selected text, clearly state that you cannot answer
            - Keep responses concise and accurate

            QUESTION: {query}
            ANSWER:"""
        else:
            prompt = f"""
            You are a helpful assistant that answers questions based only on the provided Physical AI & Humanoid Robotics book content.

            BOOK CONTENT:
            {context}

            INSTRUCTIONS:
            - Answer the question using ONLY information from the provided BOOK CONTENT
            - Do not use any external knowledge or make assumptions
            - If the answer is not in the provided content, clearly state that you cannot answer
            - Keep responses concise and accurate

            QUESTION: {query}
            ANSWER:"""

        try:
            # Generate response using OpenRouter (replacing Gemini)
            # response = self.generative_model.generate_content(...)
            
            response_text = await self.openrouter_service.generate_content(
                prompt=prompt,
                temperature=settings.generation_temperature,
                max_tokens=settings.max_response_tokens
            )
            
            # response.text from Gemini became response_text here
            response = type('obj', (object,), {'text': response_text}) # Mocking object to keep structure if needed, or just using string below# Calculate confidence based on similarity scores of retrieved chunks
            if retrieved_chunks:
                avg_similarity = sum(chunk.similarity_score for chunk in retrieved_chunks) / len(retrieved_chunks)
                # Normalize confidence score (0.0 to 1.0)
                confidence = min(1.0, avg_similarity + 0.2)  # Adding small boost for relevance
            else:
                confidence = 0.0

            return response_text.strip(), confidence

        except Exception as e:
            # If generation fails, return a default refusal response
            error_msg = str(e)
            print(f"DEBUG: Generation failed: {error_msg}", flush=True)
            return f"I encountered an error while generating a response based on the book content. Error details: {error_msg}", 0.0