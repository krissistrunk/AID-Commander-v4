#!/usr/bin/env python3
"""
Claude Code Integration for AID Commander v4.0
Manages conversational AI interface with guaranteed memory access
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from memory_service import MemoryBank, MemoryContext
from context_engine import ContextEngine
from quality_gates import QualityGatesEngine
from utils.performance import measure_performance
from config.settings import get_settings

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages Claude Code conversations with memory integration"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memory_bank = MemoryBank(project_path)
        self.context_engine = ContextEngine(self.memory_bank)
        self.quality_gates = QualityGatesEngine(project_path)
        self.settings = get_settings()
        self.conversation_id = self._initialize_conversation()
        
    def _initialize_conversation(self) -> str:
        """Initialize conversation with persistent ID"""
        timestamp = datetime.now().isoformat()
        return f"claude_conversation_{timestamp}"
    
    @measure_performance
    async def process_user_request(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user request with full memory context injection"""
        try:
            # Build comprehensive context for Claude Code
            enhanced_context = await self._build_claude_code_context(user_message, context)
            
            # Generate memory-enhanced system prompt
            system_prompt = await self._build_memory_enhanced_prompt(enhanced_context)
            
            # Prepare the complete request for Claude Code
            claude_request = {
                'system_prompt': system_prompt,
                'user_message': user_message,
                'conversation_id': self.conversation_id,
                'project_context': enhanced_context,
                'timestamp': datetime.now().isoformat()
            }
            
            # Track the interaction
            await self.memory_bank.track_conversation({
                'type': 'claude_code_request',
                'user_message': user_message,
                'context_size': len(str(enhanced_context)),
                'conversation_id': self.conversation_id
            })
            
            return claude_request
            
        except Exception as e:
            logger.error(f"Failed to process user request: {e}")
            raise
    
    async def process_ai_response(self, ai_response: str, user_message: str, 
                                 outcome: str = "unknown") -> Dict[str, Any]:
        """Process and learn from AI response"""
        try:
            # Analyze response quality and effectiveness
            response_analysis = await self._analyze_response_quality(ai_response, user_message)
            
            # Store interaction for learning
            interaction_record = {
                'type': 'claude_code_interaction',
                'user_message': user_message,
                'ai_response': ai_response,
                'outcome': outcome,
                'quality_score': response_analysis.get('quality_score', 0),
                'conversation_id': self.conversation_id,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.memory_bank.track_conversation(interaction_record)
            
            # Extract any decisions made in the response
            decisions = await self._extract_decisions_from_response(ai_response)
            for decision in decisions:
                await self.memory_bank.store_decision(decision)
            
            # Update active context based on response
            context_updates = await self._extract_context_updates(ai_response)
            if context_updates:
                await self.memory_bank.update_active_context(context_updates)
            
            return {
                'analysis': response_analysis,
                'decisions_extracted': len(decisions),
                'context_updated': bool(context_updates),
                'learning_complete': True
            }
            
        except Exception as e:
            logger.error(f"Failed to process AI response: {e}")
            return {'learning_complete': False, 'error': str(e)}
    
    async def get_conversation_context(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent conversation context for continuity"""
        try:
            # Get recent interactions
            recent_conversations = await self._get_conversation_history(limit)
            
            # Get current project state
            project_state = await self._get_current_project_state()
            
            # Get active decisions
            active_decisions = await self._get_active_decisions()
            
            return {
                'recent_conversations': recent_conversations,
                'project_state': project_state,
                'active_decisions': active_decisions,
                'conversation_id': self.conversation_id,
                'session_start': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return {}
    
    async def suggest_next_questions(self, current_context: Dict[str, Any]) -> List[str]:
        """Suggest follow-up questions based on context and memory"""
        try:
            suggestions = []
            
            # Get memory context for suggestions
            memory_context = await self.memory_bank.get_relevant_context("next steps")
            
            # Basic suggestions based on project state
            project_state = current_context.get('project_state', {})
            
            if not project_state.get('prd_completed'):
                suggestions.append("Should we focus on completing the PRD first?")
            
            if project_state.get('prd_completed') and not project_state.get('tasks_generated'):
                suggestions.append("Would you like me to generate implementation tasks?")
            
            if project_state.get('tasks_generated') and not project_state.get('implementation_started'):
                suggestions.append("Shall we begin implementing the highest priority tasks?")
            
            # Memory-based suggestions
            if memory_context.success_patterns:
                suggestions.append("Would you like me to check our approach against successful patterns?")
            
            if memory_context.failure_patterns:
                suggestions.append("Should I review potential risks based on past project failures?")
            
            # Quality gates suggestions
            if project_state.get('needs_validation'):
                suggestions.append("Would you like me to run quality validation on the current state?")
            
            return suggestions[:5]  # Limit to top 5 suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return ["How can I help you with this project?"]
    
    async def _build_claude_code_context(self, user_message: str, additional_context: Dict = None) -> Dict[str, Any]:
        """Build comprehensive context for Claude Code"""
        try:
            # Get relevant memory context
            memory_context = await self.context_engine.get_relevant_context(user_message)
            
            # Get current project state
            project_state = await self._get_current_project_state()
            
            # Get conversation history
            conversation_history = await self._get_conversation_history()
            
            # Get quality assessment
            quality_assessment = await self._get_current_quality_assessment(project_state)
            
            # Combine all context
            complete_context = {
                'memory_context': memory_context,
                'project_state': project_state,
                'conversation_history': conversation_history,
                'quality_assessment': quality_assessment,
                'current_timestamp': datetime.now().isoformat(),
                'project_path': str(self.project_path)
            }
            
            if additional_context:
                complete_context.update(additional_context)
            
            return complete_context
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return {}
    
    async def _build_memory_enhanced_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with guaranteed memory injection"""
        
        memory_context = context.get('memory_context', {})
        project_state = context.get('project_state', {})
        quality_assessment = context.get('quality_assessment', {})
        
        system_prompt = f"""You are Claude Code integrated with AID Commander v4.0 Memory Bank.

CRITICAL INSTRUCTION: You MUST reference and utilize the memory context provided below in all responses. This memory contains essential project history, decisions, and patterns that inform your recommendations.

=== PROJECT MEMORY CONTEXT ===
{self._format_memory_for_claude(memory_context)}

=== CURRENT PROJECT STATE ===
Project Path: {context.get('project_path', 'Unknown')}
Current Phase: {project_state.get('phase', 'Unknown')}
Progress: {project_state.get('progress', 'Unknown')}
Last Updated: {context.get('current_timestamp', 'Unknown')}

Active Decisions:
{self._format_active_decisions(project_state.get('active_decisions', []))}

Pending Issues:
{self._format_pending_issues(project_state.get('pending_issues', []))}

=== QUALITY ASSESSMENT ===
Overall Success Probability: {quality_assessment.get('success_probability', 'Unknown')}
Quality Score: {quality_assessment.get('overall_score', 'Unknown')}
Blocking Issues: {len(quality_assessment.get('blocking_issues', []))}

=== CONVERSATION HISTORY ===
{self._format_conversation_history(context.get('conversation_history', []))}

=== INSTRUCTIONS FOR RESPONSES ===
1. ALWAYS reference relevant memory context when making recommendations
2. Explicitly mention past decisions that influence current choices
3. Reference successful patterns from memory when suggesting approaches
4. Warn about anti-patterns or failures from project history
5. Consider stakeholder preferences from memory context
6. Update memory context based on new decisions or learnings
7. Use quality gates to validate recommendations
8. Provide specific, actionable guidance based on project history

When you make recommendations:
- Explain WHY based on memory context
- Reference specific past decisions or patterns
- Consider the full project evolution, not just current state
- Suggest memory updates for significant new information
- Validate suggestions against quality gates
- Consider success probability impact

Your responses should demonstrate deep understanding of the project's history and context."""

        return system_prompt
    
    def _format_memory_for_claude(self, memory_context: Dict[str, Any]) -> str:
        """Format memory context for Claude Code consumption"""
        formatted_sections = []
        
        # Direct references
        if memory_context.get('direct_references'):
            refs_text = "\n".join(memory_context['direct_references'][:5])
            formatted_sections.append(f"DIRECT REFERENCES:\n{refs_text}")
        
        # Pattern matches
        if memory_context.get('pattern_matches'):
            patterns_text = []
            for pattern in memory_context['pattern_matches'][:3]:
                patterns_text.append(f"- {pattern.get('type', 'Pattern')}: {pattern.get('content', 'No description')[:100]}...")
            formatted_sections.append(f"SIMILAR PATTERNS:\n" + "\n".join(patterns_text))
        
        # Recent decisions
        if memory_context.get('recent_decisions'):
            decisions_text = []
            for decision in memory_context['recent_decisions'][:3]:
                decisions_text.append(f"- {decision.get('title', 'Unknown')}: {decision.get('rationale', 'No rationale')}")
            formatted_sections.append(f"RECENT DECISIONS:\n" + "\n".join(decisions_text))
        
        # Success patterns
        if memory_context.get('success_patterns'):
            success_text = []
            for pattern in memory_context['success_patterns'][:2]:
                success_text.append(f"- {pattern.get('description', 'Pattern')}: {pattern.get('success_rate', 'Unknown')}% success")
            formatted_sections.append(f"SUCCESS PATTERNS:\n" + "\n".join(success_text))
        
        # Conflict warnings
        if memory_context.get('conflict_warnings'):
            conflicts_text = []
            for conflict in memory_context['conflict_warnings'][:2]:
                conflicts_text.append(f"- WARNING: {conflict.get('description', 'Potential conflict')}")
            formatted_sections.append(f"CONFLICT WARNINGS:\n" + "\n".join(conflicts_text))
        
        return "\n\n".join(formatted_sections) if formatted_sections else "No specific memory context available."
    
    def _format_active_decisions(self, decisions: List[Dict]) -> str:
        """Format active decisions for display"""
        if not decisions:
            return "No active decisions pending."
        
        formatted = []
        for decision in decisions[:3]:  # Show top 3
            status = decision.get('status', 'Unknown')
            title = decision.get('title', 'Untitled')
            formatted.append(f"- [{status.upper()}] {title}")
        
        return "\n".join(formatted)
    
    def _format_pending_issues(self, issues: List[Dict]) -> str:
        """Format pending issues for display"""
        if not issues:
            return "No pending issues."
        
        formatted = []
        for issue in issues[:3]:  # Show top 3
            priority = issue.get('priority', 'Unknown')
            description = issue.get('description', 'No description')
            formatted.append(f"- [{priority.upper()}] {description}")
        
        return "\n".join(formatted)
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format recent conversation history"""
        if not history:
            return "No previous conversation history."
        
        formatted = []
        for interaction in history[-3:]:  # Last 3 interactions
            timestamp = interaction.get('timestamp', 'Unknown time')
            user_msg = interaction.get('user_message', '')[:50] + "..." if len(interaction.get('user_message', '')) > 50 else interaction.get('user_message', '')
            formatted.append(f"- {timestamp}: {user_msg}")
        
        return "\n".join(formatted)
    
    # Helper methods for data retrieval
    async def _get_current_project_state(self) -> Dict[str, Any]:
        """Get current project state"""
        try:
            # Read active context from memory bank
            active_context = await self.memory_bank._read_memory_file("active_context.md")
            
            # Parse basic project state (simplified)
            state = {
                'phase': 'planning',  # Would be parsed from active context
                'progress': '0%',     # Would be calculated
                'active_decisions': [],
                'pending_issues': [],
                'last_updated': datetime.now().isoformat()
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to get project state: {e}")
            return {}
    
    async def _get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        try:
            # This would query the memory bank for recent conversations
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def _get_active_decisions(self) -> List[Dict]:
        """Get currently active decisions"""
        try:
            # Query memory bank for pending decisions
            return []
            
        except Exception as e:
            logger.error(f"Failed to get active decisions: {e}")
            return []
    
    async def _get_current_quality_assessment(self, project_state: Dict) -> Dict[str, Any]:
        """Get current quality assessment"""
        try:
            # Use quality gates to assess current state
            probability = await self.quality_gates.calculate_success_probability(project_state)
            
            return {
                'success_probability': f"{probability:.1%}",
                'overall_score': 'Calculating...',
                'blocking_issues': []
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality assessment: {e}")
            return {}
    
    async def _analyze_response_quality(self, response: str, user_message: str) -> Dict[str, Any]:
        """Analyze AI response quality"""
        try:
            quality_score = 0.5  # Base score
            
            # Basic quality indicators
            if len(response) > 100:  # Reasonable detail
                quality_score += 0.2
            
            if "memory" in response.lower() or "previous" in response.lower():  # Memory reference
                quality_score += 0.2
            
            if "because" in response.lower() or "rationale" in response.lower():  # Explanation
                quality_score += 0.1
            
            return {
                'quality_score': min(quality_score, 1.0),
                'has_memory_reference': "memory" in response.lower(),
                'has_rationale': "because" in response.lower(),
                'response_length': len(response)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze response quality: {e}")
            return {'quality_score': 0.0}
    
    async def _extract_decisions_from_response(self, response: str) -> List[Dict]:
        """Extract any decisions made in the AI response"""
        try:
            decisions = []
            
            # Simple pattern matching for decisions
            # In production, this would use more sophisticated NLP
            if "decide" in response.lower() or "recommendation" in response.lower():
                decisions.append({
                    'title': 'AI Recommendation',
                    'context': 'Extracted from AI response',
                    'options': [],
                    'chosen_option': 'AI suggestion',
                    'rationale': response[:500],  # First 500 chars as rationale
                    'decision_maker': 'AI Assistant',
                    'status': 'suggested'
                })
            
            return decisions
            
        except Exception as e:
            logger.error(f"Failed to extract decisions: {e}")
            return []
    
    async def _extract_context_updates(self, response: str) -> Dict[str, Any]:
        """Extract context updates from AI response"""
        try:
            updates = {}
            
            # Look for progress indicators
            if "progress" in response.lower():
                updates['progress_noted'] = datetime.now().isoformat()
            
            # Look for phase changes
            if "next phase" in response.lower() or "move to" in response.lower():
                updates['phase_transition_suggested'] = datetime.now().isoformat()
            
            return updates
            
        except Exception as e:
            logger.error(f"Failed to extract context updates: {e}")
            return {}

# CLI interface for conversation manager
async def cli_main():
    """CLI interface for conversation manager"""
    import typer
    app = typer.Typer()
    
    @app.command()
    def process_request(project_path: str, message: str):
        """Process a user request and generate Claude Code context"""
        async def _process():
            conv_manager = ConversationManager(project_path)
            request = await conv_manager.process_user_request(message)
            print("=== SYSTEM PROMPT ===")
            print(request['system_prompt'])
            print("\n=== USER MESSAGE ===")
            print(request['user_message'])
        
        asyncio.run(_process())
    
    @app.command()
    def get_context(project_path: str):
        """Get current conversation context"""
        async def _get_context():
            conv_manager = ConversationManager(project_path)
            context = await conv_manager.get_conversation_context()
            print(json.dumps(context, indent=2, default=str))
        
        asyncio.run(_get_context())
    
    @app.command()
    def suggest_questions(project_path: str):
        """Get suggested follow-up questions"""
        async def _suggest():
            conv_manager = ConversationManager(project_path)
            context = await conv_manager.get_conversation_context()
            suggestions = await conv_manager.suggest_next_questions(context)
            
            print("Suggested questions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion}")
        
        asyncio.run(_suggest())
    
    app()

if __name__ == "__main__":
    cli_main()