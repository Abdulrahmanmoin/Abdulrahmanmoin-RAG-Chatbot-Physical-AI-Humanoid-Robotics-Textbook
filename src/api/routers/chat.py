from fastapi import APIRouter, HTTPException
import logging
from ...models.query import QueryRequest, QueryResponse
from ...services.query_service import QueryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """
    Main chat endpoint that handles user queries and returns AI-generated responses
    based on the Physical AI & Humanoid Robotics book content.
    """
    try:
        logger.info(f"Received query: {request.query[:50]}... (type: {request.query_type})")

        # Validate input
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Using settings for max query length if available, otherwise default to 1000
        from ...config.settings import settings
        if len(request.query) > settings.max_query_length:
            raise HTTPException(status_code=400, detail=f"Query exceeds maximum length of {settings.max_query_length} characters")

        if request.query_type not in ["full_book", "selection_based"]:
            raise HTTPException(status_code=400, detail="Invalid query type")

        if request.query_type == "selection_based" and not request.selected_text:
            raise HTTPException(status_code=400, detail="Selected text required for selection-based queries")

        # Initialize and use the query service
        query_service = QueryService()

        # Process the query
        response = await query_service.process_query(request)

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/chat/test")
async def test_chat():
    """
    Test endpoint to verify the chat service is working
    """
    return {"message": "Chat endpoint is working"}