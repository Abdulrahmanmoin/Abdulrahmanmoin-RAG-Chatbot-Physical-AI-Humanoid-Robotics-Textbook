from typing import Dict, Any, List
from ..models.document_models import RetrievedChunk
from ..services.query_service import QueryService
from ..services.retrieval_service import RetrievalService
from ..services.validation_service import ValidationService
from ..services.openrouter_service import OpenRouterService
from ..config.settings import settings


class RAGAgent:
    def __init__(self):
        self.query_service = QueryService()
        self.retrieval_service = RetrievalService()
        self.validation_service = ValidationService()
        self.openrouter_service = OpenRouterService()

    def execute(self, query: str, context_chunks: List[RetrievedChunk], query_type: str = "full_book") -> Dict[str, Any]:
        """
        Execute the RAG agent to generate a response based on the query and context
        """
        try:
            # Build the prompt with context
            context_text = self._build_context_text(context_chunks)

            # Create the appropriate prompt based on query type
            if query_type == "selection_based":
                prompt = self._create_selection_prompt(query, context_text)
            else:
                prompt = self._create_full_book_prompt(query, context_text)

            # Generate response using OpenRouter
            response_text = self.openrouter_service.generate_content(
                prompt,
                temperature=settings.generation_temperature,
                max_tokens=settings.max_response_tokens,
            )

            # Validate the response is grounded in the provided context
            if response_text:
                is_grounded, validation_details = self.validation_service.validate_response_grounding(
                    response_text,
                    context_chunks
                )

                if not is_grounded:
                    return {
                        "response": "I cannot provide an answer that is fully grounded in the provided context.",
                        "status": "refused",
                        "confidence": 0.0,
                        "validation_details": validation_details
                    }

                # Calculate confidence based on context quality
                confidence = self._calculate_response_confidence(context_chunks, validation_details)

                return {
                    "response": response_text,
                    "status": "success",
                    "confidence": confidence,
                    "validation_details": validation_details
                }
            else:
                return {
                    "response": "I couldn't generate a response based on the provided context.",
                    "status": "refused",
                    "confidence": 0.0,
                    "validation_details": {"error": "No response generated"}
                }

        except Exception as e:
            return {
                "response": f"An error occurred during response generation: {str(e)}",
                "status": "error",
                "confidence": 0.0,
                "validation_details": {"error": str(e)}
            }

    def _build_context_text(self, context_chunks: List[RetrievedChunk]) -> str:
        """
        Build context text from retrieved chunks
        """
        context_parts = []
        for chunk in context_chunks:
            context_parts.append(f"Source: {chunk.source_path}\nContent: {chunk.content}")
        return "\n\n".join(context_parts)

    def _create_full_book_prompt(self, query: str, context: str) -> str:
        """
        Create prompt for full-book query mode
        """
        return f"""
        You are an AI assistant for the Physical AI & Humanoid Robotics book. Your purpose is to answer questions based only on the provided book content.

        BOOK CONTENT:
        {context}

        INSTRUCTIONS:
        1. Answer the user's question using ONLY the information provided in the BOOK CONTENT
        2. Do not use any external knowledge or general information
        3. If the answer is not available in the provided content, clearly state that you cannot answer
        4. When possible, cite the source of information
        5. Keep your responses accurate and concise

        QUESTION: {query}
        RESPONSE:"""

    def _create_selection_prompt(self, query: str, context: str) -> str:
        """
        Create prompt for selection-based query mode
        """
        return f"""
        You are an AI assistant for the Physical AI & Humanoid Robotics book. Your purpose is to answer questions based only on the provided selected text.

        SELECTED TEXT:
        {context}

        INSTRUCTIONS:
        1. Answer the user's question using ONLY the information provided in the SELECTED TEXT
        2. Do not use any other book content or external knowledge
        3. If the answer is not available in the selected text, clearly state that you cannot answer
        4. Keep your responses accurate and concise

        QUESTION: {query}
        RESPONSE:"""

    def _calculate_response_confidence(self, context_chunks: List[RetrievedChunk], validation_details: Dict[str, Any]) -> float:
        """
        Calculate response confidence based on context quality and validation results
        """
        if not context_chunks:
            return 0.0

        # Base confidence on average similarity score of retrieved chunks
        avg_similarity = sum(chunk.similarity_score for chunk in context_chunks) / len(context_chunks)

        # Adjust based on grounding validation
        grounding_score = validation_details.get("grounding_score", 0.0)

        # Combine scores (average of similarity and grounding)
        confidence = (avg_similarity + grounding_score) / 2

        return min(1.0, max(0.0, confidence))  # Ensure between 0 and 1