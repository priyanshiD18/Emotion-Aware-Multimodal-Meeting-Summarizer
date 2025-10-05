"""
Agent for verifying context and referencing previous meetings
"""

from typing import Dict, Any, List, Optional
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import logging
from pathlib import Path
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ContextVerificationAgent(BaseAgent):
    """Verifies context and retrieves information from previous meetings"""
    
    def __init__(
        self,
        chroma_persist_dir: Path,
        embedding_provider: str = "openai",
        **kwargs
    ):
        """
        Initialize context verification agent
        
        Args:
            chroma_persist_dir: Directory for ChromaDB persistence
            embedding_provider: Provider for embeddings ("openai" or "google")
            **kwargs: Additional arguments for BaseAgent
        """
        super().__init__(**kwargs)
        self.chroma_persist_dir = chroma_persist_dir
        self.embedding_provider = embedding_provider
        
        # Initialize embeddings
        if embedding_provider == "openai":
            self.embeddings = OpenAIEmbeddings()
        elif embedding_provider == "google":
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}")
        
        # Initialize vector store
        self.vector_store = self._initialize_vector_store()
        
        logger.info(f"Initialized ContextVerificationAgent with {embedding_provider} embeddings")
    
    def _initialize_vector_store(self) -> Chroma:
        """Initialize or load ChromaDB vector store"""
        try:
            vector_store = Chroma(
                persist_directory=str(self.chroma_persist_dir),
                embedding_function=self.embeddings,
                collection_name="meeting_history"
            )
            logger.info("Vector store initialized")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create prompt template for context verification"""
        template = """You are an AI assistant specialized in analyzing meeting transcripts in the context of previous meetings and organizational knowledge.

Your task is to:
1. Identify topics and action items that reference previous discussions
2. Provide relevant context from previous meetings
3. Highlight follow-ups on prior commitments
4. Identify recurring themes or patterns

Current Meeting Summary:
{current_meeting}

Relevant Context from Previous Meetings:
{previous_context}

Return your analysis in the following JSON format:
{{
    "contextual_references": [
        {{
            "topic": "referenced topic",
            "current_mention": "how it's mentioned in current meeting",
            "previous_context": "relevant info from previous meetings",
            "continuity_status": "follow-up/new/recurring/resolved"
        }}
    ],
    "action_item_followups": [
        {{
            "previous_action": "action from previous meeting",
            "current_status": "mentioned/completed/pending/not_mentioned",
            "details": "any updates or discussion in current meeting"
        }}
    ],
    "recurring_themes": [
        {{
            "theme": "recurring theme",
            "frequency": "how often it appears",
            "evolution": "how the discussion has evolved"
        }}
    ],
    "missing_followups": [
        {{
            "item": "item that should have been followed up",
            "last_mentioned": "when it was last discussed",
            "recommendation": "suggested action"
        }}
    ],
    "organizational_insights": {{
        "patterns": ["observed patterns across meetings"],
        "concerns": ["recurring concerns or blockers"],
        "progress_indicators": ["signs of progress on initiatives"]
    }}
}}

Provide insightful analysis connecting current and past meeting contexts.
"""
        return PromptTemplate(
            template=template,
            input_variables=["current_meeting", "previous_context"]
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify context and provide historical insights
        
        Args:
            input_data: Dictionary with current meeting data
            
        Returns:
            Dictionary with context verification results
        """
        logger.info("Verifying context with previous meetings...")
        
        # Get current meeting summary
        current_meeting = self._format_current_meeting(input_data)
        
        # Retrieve relevant previous context
        previous_context = self._retrieve_previous_context(current_meeting)
        
        # Format prompt
        prompt = self.format_prompt(
            current_meeting=current_meeting,
            previous_context=previous_context
        )
        
        # Invoke LLM
        response = self.invoke_llm(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info("Context verification complete")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "contextual_references": [],
                "action_item_followups": [],
                "recurring_themes": [],
                "missing_followups": [],
                "organizational_insights": {},
                "raw_response": response
            }
    
    def _format_current_meeting(self, input_data: Dict[str, Any]) -> str:
        """Format current meeting data for context retrieval"""
        lines = []
        
        # Add transcript summary
        segments = input_data.get("segments", [])
        if segments:
            lines.append("TRANSCRIPT SUMMARY:")
            for seg in segments[:10]:  # First 10 segments
                speaker = seg.get("speaker", "UNKNOWN")
                text = seg.get("text", "")
                lines.append(f"{speaker}: {text}")
        
        # Add action items if available
        actions = input_data.get("action_items", [])
        if actions:
            lines.append("\nACTION ITEMS:")
            for action in actions:
                lines.append(f"- {action.get('task', '')} ({action.get('assignee', 'UNKNOWN')})")
        
        # Add decisions if available
        decisions = input_data.get("decisions", [])
        if decisions:
            lines.append("\nDECISIONS:")
            for decision in decisions:
                lines.append(f"- {decision.get('decision', '')}")
        
        return "\n".join(lines)
    
    def _retrieve_previous_context(
        self,
        query: str,
        k: int = 5
    ) -> str:
        """
        Retrieve relevant context from previous meetings
        
        Args:
            query: Query text (current meeting summary)
            k: Number of relevant documents to retrieve
            
        Returns:
            Formatted string of previous context
        """
        try:
            # Search vector store
            results = self.vector_store.similarity_search(query, k=k)
            
            if not results:
                return "No previous meeting context available."
            
            # Format results
            context_lines = []
            for i, doc in enumerate(results, 1):
                context_lines.append(f"--- Previous Meeting {i} ---")
                context_lines.append(doc.page_content)
                context_lines.append("")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Failed to retrieve previous context: {e}")
            return "Error retrieving previous context."
    
    def store_meeting(
        self,
        meeting_data: Dict[str, Any],
        meeting_id: str
    ) -> None:
        """
        Store meeting in vector database for future reference
        
        Args:
            meeting_data: Meeting data to store
            meeting_id: Unique meeting identifier
        """
        try:
            # Format meeting for storage
            meeting_text = self._format_meeting_for_storage(meeting_data)
            
            # Add to vector store
            self.vector_store.add_texts(
                texts=[meeting_text],
                metadatas=[{
                    "meeting_id": meeting_id,
                    "timestamp": meeting_data.get("timestamp", ""),
                    "participants": ",".join(meeting_data.get("speakers", []))
                }]
            )
            
            # Persist
            self.vector_store.persist()
            
            logger.info(f"Stored meeting {meeting_id} in vector database")
            
        except Exception as e:
            logger.error(f"Failed to store meeting: {e}")
    
    def _format_meeting_for_storage(self, meeting_data: Dict[str, Any]) -> str:
        """Format meeting data for vector storage"""
        lines = []
        
        # Add metadata
        lines.append(f"Meeting ID: {meeting_data.get('meeting_id', 'unknown')}")
        lines.append(f"Date: {meeting_data.get('timestamp', 'unknown')}")
        lines.append(f"Participants: {', '.join(meeting_data.get('speakers', []))}")
        lines.append("")
        
        # Add summary
        lines.append("SUMMARY:")
        segments = meeting_data.get("segments", [])
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            text = seg.get("text", "")
            lines.append(f"{speaker}: {text}")
        
        lines.append("")
        
        # Add action items
        actions = meeting_data.get("action_items", [])
        if actions:
            lines.append("ACTION ITEMS:")
            for action in actions:
                lines.append(
                    f"- {action.get('task', '')} "
                    f"(Assigned to: {action.get('assignee', 'UNKNOWN')})"
                )
        
        # Add decisions
        decisions = meeting_data.get("decisions", [])
        if decisions:
            lines.append("\nDECISIONS:")
            for decision in decisions:
                lines.append(f"- {decision.get('decision', '')}")
        
        return "\n".join(lines)

