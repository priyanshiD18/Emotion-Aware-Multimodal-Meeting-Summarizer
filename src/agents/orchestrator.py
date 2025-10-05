"""
Multi-agent orchestrator that coordinates all agents
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from .action_agent import ActionExtractionAgent
from .sentiment_agent import SentimentAnalysisAgent
from .context_agent import ContextVerificationAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple agents to analyze meeting data comprehensively"""
    
    def __init__(
        self,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4-turbo-preview",
        llm_temperature: float = 0.3,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        chroma_persist_dir: Optional[Path] = None,
        enable_context_agent: bool = True
    ):
        """
        Initialize agent orchestrator
        
        Args:
            llm_provider: LLM provider ("openai" or "google")
            llm_model: Model identifier
            llm_temperature: Sampling temperature
            openai_api_key: OpenAI API key
            google_api_key: Google API key
            chroma_persist_dir: Directory for ChromaDB
            enable_context_agent: Whether to use context verification agent
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.enable_context_agent = enable_context_agent
        
        # Determine API key
        api_key = openai_api_key if llm_provider == "openai" else google_api_key
        
        logger.info("Initializing Agent Orchestrator...")
        
        # Initialize agents
        self.action_agent = ActionExtractionAgent(
            llm_provider=llm_provider,
            model_name=llm_model,
            temperature=llm_temperature,
            api_key=api_key
        )
        
        self.sentiment_agent = SentimentAnalysisAgent(
            llm_provider=llm_provider,
            model_name=llm_model,
            temperature=llm_temperature,
            api_key=api_key
        )
        
        # Initialize context agent if enabled
        self.context_agent = None
        if enable_context_agent and chroma_persist_dir:
            self.context_agent = ContextVerificationAgent(
                chroma_persist_dir=chroma_persist_dir,
                embedding_provider="openai",  # Use OpenAI for embeddings
                llm_provider=llm_provider,
                model_name=llm_model,
                temperature=llm_temperature,
                api_key=api_key
            )
        
        logger.info("Agent Orchestrator initialized successfully")
    
    def process_meeting(
        self,
        meeting_data: Dict[str, Any],
        meeting_id: Optional[str] = None,
        store_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process meeting through all agents
        
        Args:
            meeting_data: Dictionary containing meeting segments and metadata
            meeting_id: Optional unique meeting identifier
            store_context: Whether to store this meeting for future context
            
        Returns:
            Comprehensive analysis from all agents
        """
        logger.info("Starting multi-agent meeting analysis...")
        
        # Generate meeting ID if not provided
        if meeting_id is None:
            meeting_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            "meeting_id": meeting_id,
            "timestamp": datetime.now().isoformat(),
            "speakers": self._extract_speakers(meeting_data.get("segments", [])),
        }
        
        # Phase 1: Action Extraction
        logger.info("Phase 1: Extracting actions and decisions...")
        try:
            action_results = self.action_agent.process(meeting_data)
            results["actions"] = action_results
        except Exception as e:
            logger.error(f"Action extraction failed: {e}")
            results["actions"] = {"error": str(e)}
        
        # Phase 2: Sentiment Analysis
        logger.info("Phase 2: Analyzing sentiment and emotions...")
        try:
            sentiment_results = self.sentiment_agent.process(meeting_data)
            results["sentiment"] = sentiment_results
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            results["sentiment"] = {"error": str(e)}
        
        # Phase 3: Context Verification (if enabled)
        if self.context_agent:
            logger.info("Phase 3: Verifying context with previous meetings...")
            try:
                # Merge action results into meeting data for context
                context_input = {
                    **meeting_data,
                    "action_items": results["actions"].get("action_items", []),
                    "decisions": results["actions"].get("decisions", [])
                }
                
                context_results = self.context_agent.process(context_input)
                results["context"] = context_results
                
                # Store this meeting for future reference
                if store_context:
                    full_meeting_data = {
                        "meeting_id": meeting_id,
                        "timestamp": results["timestamp"],
                        "speakers": results["speakers"],
                        "segments": meeting_data.get("segments", []),
                        **results["actions"]
                    }
                    self.context_agent.store_meeting(full_meeting_data, meeting_id)
                    
            except Exception as e:
                logger.error(f"Context verification failed: {e}")
                results["context"] = {"error": str(e)}
        
        # Generate executive summary
        results["executive_summary"] = self._generate_executive_summary(results)
        
        logger.info("Multi-agent analysis complete!")
        return results
    
    def _extract_speakers(self, segments: list) -> list:
        """Extract unique speakers from segments"""
        speakers = set()
        for seg in segments:
            speaker = seg.get("speaker")
            if speaker and speaker != "UNKNOWN":
                speakers.add(speaker)
        return sorted(list(speakers))
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary from all agent results
        
        Args:
            results: Combined results from all agents
            
        Returns:
            Executive summary dictionary
        """
        summary = {
            "meeting_id": results.get("meeting_id"),
            "timestamp": results.get("timestamp"),
            "participants": results.get("speakers", []),
            "key_highlights": []
        }
        
        # Extract key action items
        actions = results.get("actions", {})
        action_items = actions.get("action_items", [])
        if action_items:
            summary["key_highlights"].append(
                f"{len(action_items)} action items identified"
            )
            summary["top_actions"] = action_items[:5]  # Top 5 actions
        
        # Extract key decisions
        decisions = actions.get("decisions", [])
        if decisions:
            summary["key_highlights"].append(
                f"{len(decisions)} decisions made"
            )
            summary["top_decisions"] = decisions[:3]  # Top 3 decisions
        
        # Extract sentiment insights
        sentiment = results.get("sentiment", {})
        overall_sentiment = sentiment.get("overall_sentiment", {})
        if overall_sentiment:
            mood = overall_sentiment.get("mood", "unknown")
            tone = overall_sentiment.get("tone", "unknown")
            summary["key_highlights"].append(
                f"Meeting mood: {mood}, tone: {tone}"
            )
            summary["overall_mood"] = mood
            summary["overall_tone"] = tone
        
        # Extract context insights
        context = results.get("context", {})
        if context and not context.get("error"):
            recurring = context.get("recurring_themes", [])
            if recurring:
                summary["key_highlights"].append(
                    f"{len(recurring)} recurring themes identified"
                )
        
        return summary
    
    def analyze_transcript_only(
        self,
        transcript_text: str,
        segments: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Quick analysis when only transcript is available
        
        Args:
            transcript_text: Raw transcript text
            segments: Optional list of segments
            
        Returns:
            Analysis results
        """
        # Create minimal meeting data
        meeting_data = {
            "transcript": transcript_text,
            "segments": segments or []
        }
        
        # Process through action agent only
        action_results = self.action_agent.process(meeting_data)
        
        return {
            "transcript": transcript_text,
            "analysis": action_results
        }

