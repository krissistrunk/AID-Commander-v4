#!/usr/bin/env python3
"""
Context Engine for AID Commander v4.0
Intelligent context retrieval and analysis
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from memory_service import MemoryBank, MemoryContext
from utils.performance import measure_performance, cache_result
from config.settings import get_settings

logger = logging.getLogger(__name__)

class ContextEngine:
    """Advanced context analysis and retrieval engine"""
    
    def __init__(self, memory_bank: MemoryBank):
        self.memory_bank = memory_bank
        self.settings = get_settings()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._context_cache = {}
        
    @measure_performance
    async def get_relevant_context(self, current_task: str, max_contexts: int = 10) -> Dict[str, Any]:
        """Multi-strategy context gathering for current task"""
        try:
            # Parallel context gathering for performance
            context_results = await asyncio.gather(
                self._find_direct_mentions(current_task),
                self._find_similar_patterns(current_task),
                self._get_dependency_context(current_task),
                self._get_recent_related_decisions(current_task),
                self._check_for_conflicts(current_task),
                self._get_applicable_success_patterns(current_task),
                self._get_stakeholder_preferences(),
                return_exceptions=True
            )
            
            # Process results and handle any exceptions
            (direct_refs, pattern_matches, dependency_context, 
             recent_decisions, conflicts, success_patterns, stakeholder_context) = context_results
            
            # Calculate relevance scores
            relevance_scores = await self._calculate_relevance_scores(
                current_task, direct_refs, pattern_matches, recent_decisions
            )
            
            return {
                'direct_references': direct_refs if not isinstance(direct_refs, Exception) else [],
                'pattern_matches': pattern_matches if not isinstance(pattern_matches, Exception) else [],
                'dependency_context': dependency_context if not isinstance(dependency_context, Exception) else {},
                'recent_decisions': recent_decisions if not isinstance(recent_decisions, Exception) else [],
                'conflict_warnings': conflicts if not isinstance(conflicts, Exception) else [],
                'success_patterns': success_patterns if not isinstance(success_patterns, Exception) else [],
                'stakeholder_context': stakeholder_context if not isinstance(stakeholder_context, Exception) else {},
                'relevance_scores': relevance_scores,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return self._get_empty_context()
    
    async def suggest_tasks_from_memory(self, requirements: str) -> List[Dict[str, Any]]:
        """Generate task suggestions based on memory patterns"""
        try:
            # Find similar past projects
            similar_projects = await self._find_similar_projects(requirements)
            
            # Extract successful task patterns
            task_suggestions = []
            for project in similar_projects:
                project_tasks = await self._get_project_tasks(project)
                successful_tasks = [task for task in project_tasks if task.get('success_rate', 0) > 0.8]
                task_suggestions.extend(successful_tasks)
            
            # Score and rank suggestions
            scored_suggestions = await self._score_task_suggestions(task_suggestions, requirements)
            
            return scored_suggestions[:10]  # Top 10 suggestions
            
        except Exception as e:
            logger.error(f"Task suggestion failed: {e}")
            return []
    
    async def identify_optimization_opportunities(self, current_approach: str) -> List[Dict[str, Any]]:
        """Suggest improvements based on past experience"""
        try:
            # Find similar approaches in memory
            similar_approaches = await self._find_similar_approaches(current_approach)
            
            # Identify what worked better
            optimizations = []
            for approach in similar_approaches:
                if approach.get('success_rate', 0) > 0.9:  # High success rate
                    optimization = {
                        'suggestion': approach.get('description'),
                        'rationale': approach.get('why_it_worked'),
                        'success_rate': approach.get('success_rate'),
                        'confidence': self._calculate_suggestion_confidence(approach, current_approach)
                    }
                    optimizations.append(optimization)
            
            return sorted(optimizations, key=lambda x: x['confidence'], reverse=True)
            
        except Exception as e:
            logger.error(f"Optimization identification failed: {e}")
            return []
    
    async def predict_risk_factors(self, project_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential issues based on historical patterns"""
        try:
            risk_factors = []
            
            # Check for known failure patterns
            failure_patterns = await self.memory_bank._get_failure_patterns("")
            for pattern in failure_patterns:
                risk_score = await self._calculate_pattern_risk_score(pattern, project_state)
                if risk_score > 0.6:  # High risk threshold
                    risk_factors.append({
                        'risk_type': pattern.get('type', 'Unknown'),
                        'description': pattern.get('description'),
                        'risk_score': risk_score,
                        'mitigation': pattern.get('mitigation_strategies', []),
                        'historical_impact': pattern.get('average_impact', 'Unknown')
                    })
            
            # Check for timeline risks
            timeline_risks = await self._assess_timeline_risks(project_state)
            risk_factors.extend(timeline_risks)
            
            # Check for scope creep indicators
            scope_risks = await self._assess_scope_risks(project_state)
            risk_factors.extend(scope_risks)
            
            return sorted(risk_factors, key=lambda x: x['risk_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Risk prediction failed: {e}")
            return []
    
    @cache_result(ttl=1800)  # Cache for 30 minutes
    async def _find_direct_mentions(self, task: str) -> List[str]:
        """Find direct mentions of task elements in memory"""
        try:
            # Extract key terms from task
            task_terms = self._extract_key_terms(task)
            
            direct_mentions = []
            for term in task_terms:
                mentions = await self.memory_bank._find_direct_references(term)
                direct_mentions.extend(mentions)
            
            # Remove duplicates and return most relevant
            unique_mentions = list(set(direct_mentions))
            return unique_mentions[:10]
            
        except Exception as e:
            logger.error(f"Direct mention search failed: {e}")
            return []
    
    async def _find_similar_patterns(self, task: str) -> List[Dict[str, Any]]:
        """Find similar task patterns using semantic analysis"""
        try:
            # Get all historical tasks
            historical_tasks = await self._get_all_historical_tasks()
            
            if not historical_tasks:
                return []
            
            # Vectorize current task and historical tasks
            all_tasks = [task] + [t.get('description', '') for t in historical_tasks]
            
            try:
                task_vectors = self.vectorizer.fit_transform(all_tasks)
                similarities = cosine_similarity(task_vectors[0:1], task_vectors[1:]).flatten()
                
                # Get top similar tasks
                similar_indices = similarities.argsort()[-5:][::-1]  # Top 5
                
                similar_patterns = []
                for idx in similar_indices:
                    if similarities[idx] > 0.3:  # Similarity threshold
                        pattern = historical_tasks[idx].copy()
                        pattern['similarity_score'] = float(similarities[idx])
                        similar_patterns.append(pattern)
                
                return similar_patterns
                
            except ValueError:
                # Fallback to keyword matching if TF-IDF fails
                return await self._keyword_based_similarity(task, historical_tasks)
            
        except Exception as e:
            logger.error(f"Pattern similarity search failed: {e}")
            return []
    
    async def _get_dependency_context(self, task: str) -> Dict[str, Any]:
        """Get context about task dependencies"""
        try:
            # Find tasks that are commonly prerequisites
            prerequisites = await self._find_common_prerequisites(task)
            
            # Find tasks that commonly follow
            dependents = await self._find_common_dependents(task)
            
            # Find blocking issues from similar tasks
            blocking_issues = await self._find_historical_blockers(task)
            
            return {
                'prerequisites': prerequisites,
                'dependents': dependents,
                'potential_blockers': blocking_issues,
                'estimated_dependencies': len(prerequisites) + len(dependents)
            }
            
        except Exception as e:
            logger.error(f"Dependency context retrieval failed: {e}")
            return {}
    
    async def _get_recent_related_decisions(self, task: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent decisions related to current task"""
        try:
            # Get recent decisions
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_decisions = await self.memory_bank._get_recent_decisions(limit=50)
            
            # Filter for relevance to current task
            related_decisions = []
            task_terms = self._extract_key_terms(task.lower())
            
            for decision in recent_decisions:
                decision_text = f"{decision.get('title', '')} {decision.get('context', '')}".lower()
                
                # Check if any task terms appear in decision
                relevance_score = 0
                for term in task_terms:
                    if term in decision_text:
                        relevance_score += 1
                
                if relevance_score > 0:
                    decision_copy = decision.copy()
                    decision_copy['relevance_score'] = relevance_score
                    related_decisions.append(decision_copy)
            
            # Sort by relevance and recency
            related_decisions.sort(
                key=lambda x: (x['relevance_score'], x.get('timestamp', '')), 
                reverse=True
            )
            
            return related_decisions[:5]  # Top 5 most relevant
            
        except Exception as e:
            logger.error(f"Related decisions retrieval failed: {e}")
            return []
    
    async def _check_for_conflicts(self, task: str) -> List[Dict[str, Any]]:
        """Check for potential conflicts with existing decisions"""
        try:
            conflicts = []
            
            # Get current active decisions
            active_decisions = await self._get_active_decisions()
            
            # Check for potential conflicts
            for decision in active_decisions:
                conflict_score = await self._calculate_conflict_score(task, decision)
                
                if conflict_score > 0.5:  # Conflict threshold
                    conflicts.append({
                        'decision_id': decision.get('id'),
                        'decision_title': decision.get('title'),
                        'conflict_type': self._identify_conflict_type(task, decision),
                        'conflict_score': conflict_score,
                        'recommendation': self._generate_conflict_resolution(task, decision)
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Conflict checking failed: {e}")
            return []
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for matching"""
        # Simple keyword extraction - in production would use NLP
        text = text.lower()
        words = re.findall(r'\b\w{3,}\b', text)  # Words with 3+ characters
        
        # Filter out common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
        
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        return meaningful_words[:10]  # Top 10 terms
    
    async def _calculate_relevance_scores(self, query: str, direct_refs: List[str], 
                                        pattern_matches: List[Dict], decisions: List[Dict]) -> Dict[str, float]:
        """Calculate relevance scores for context elements"""
        try:
            scores = {}
            
            # Score direct references
            if direct_refs:
                scores['direct_references'] = min(len(direct_refs) / 10.0, 1.0)
            
            # Score pattern matches
            if pattern_matches:
                avg_similarity = sum(p.get('similarity_score', 0) for p in pattern_matches) / len(pattern_matches)
                scores['pattern_matches'] = avg_similarity
            
            # Score decision relevance
            if decisions:
                avg_relevance = sum(d.get('relevance_score', 0) for d in decisions) / len(decisions)
                scores['decisions'] = min(avg_relevance / 5.0, 1.0)  # Normalize to 0-1
            
            return scores
            
        except Exception as e:
            logger.error(f"Relevance score calculation failed: {e}")
            return {}
    
    def _get_empty_context(self) -> Dict[str, Any]:
        """Return empty context structure"""
        return {
            'direct_references': [],
            'pattern_matches': [],
            'dependency_context': {},
            'recent_decisions': [],
            'conflict_warnings': [],
            'success_patterns': [],
            'stakeholder_context': {},
            'relevance_scores': {},
            'timestamp': datetime.now().isoformat()
        }
    
    # Placeholder methods for future implementation
    async def _find_similar_projects(self, requirements: str) -> List[Dict]:
        return []
    
    async def _get_project_tasks(self, project: Dict) -> List[Dict]:
        return []
    
    async def _score_task_suggestions(self, suggestions: List[Dict], requirements: str) -> List[Dict]:
        return suggestions
    
    async def _find_similar_approaches(self, approach: str) -> List[Dict]:
        return []
    
    def _calculate_suggestion_confidence(self, approach: Dict, current: str) -> float:
        return 0.5
    
    async def _calculate_pattern_risk_score(self, pattern: Dict, state: Dict) -> float:
        return 0.0
    
    async def _assess_timeline_risks(self, state: Dict) -> List[Dict]:
        return []
    
    async def _assess_scope_risks(self, state: Dict) -> List[Dict]:
        return []
    
    async def _get_all_historical_tasks(self) -> List[Dict]:
        return []
    
    async def _keyword_based_similarity(self, task: str, historical: List[Dict]) -> List[Dict]:
        # Simple keyword-based fallback
        task_words = set(self._extract_key_terms(task))
        similar = []
        
        for hist_task in historical:
            hist_words = set(self._extract_key_terms(hist_task.get('description', '')))
            overlap = len(task_words.intersection(hist_words))
            if overlap > 0:
                hist_task['similarity_score'] = overlap / len(task_words.union(hist_words))
                similar.append(hist_task)
        
        return sorted(similar, key=lambda x: x['similarity_score'], reverse=True)[:5]
    
    async def _find_common_prerequisites(self, task: str) -> List[str]:
        return []
    
    async def _find_common_dependents(self, task: str) -> List[str]:
        return []
    
    async def _find_historical_blockers(self, task: str) -> List[str]:
        return []
    
    async def _get_active_decisions(self) -> List[Dict]:
        return []
    
    async def _calculate_conflict_score(self, task: str, decision: Dict) -> float:
        return 0.0
    
    def _identify_conflict_type(self, task: str, decision: Dict) -> str:
        return "unknown"
    
    def _generate_conflict_resolution(self, task: str, decision: Dict) -> str:
        return "Review potential conflict"
    
    async def _get_applicable_success_patterns(self, task: str) -> List[Dict]:
        return []
    
    async def _get_stakeholder_preferences(self) -> Dict:
        return {}

# CLI interface for context engine
async def cli_main():
    """CLI interface for context engine operations"""
    import typer
    from memory_service import MemoryBank
    
    app = typer.Typer()
    
    @app.command()
    def analyze(project_path: str, task_description: str):
        """Analyze task and get relevant context"""
        async def _analyze():
            memory_bank = MemoryBank(project_path)
            context_engine = ContextEngine(memory_bank)
            context = await context_engine.get_relevant_context(task_description)
            print(json.dumps(context, indent=2, default=str))
        
        asyncio.run(_analyze())
    
    @app.command()
    def suggest_tasks(project_path: str, requirements: str):
        """Suggest tasks based on memory patterns"""
        async def _suggest():
            memory_bank = MemoryBank(project_path)
            context_engine = ContextEngine(memory_bank)
            suggestions = await context_engine.suggest_tasks_from_memory(requirements)
            print(json.dumps(suggestions, indent=2, default=str))
        
        asyncio.run(_suggest())
    
    app()

if __name__ == "__main__":
    cli_main()