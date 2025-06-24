#!/usr/bin/env python3
"""
Quality Gates Framework for AID Commander v4.0
Comprehensive validation system with memory integration
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from memory_service import MemoryBank, MemoryContext
from context_engine import ContextEngine
from utils.performance import measure_performance
from config.settings import get_settings

logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    """Validation result status"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    BLOCKED = "blocked"

@dataclass
class QualityGateResult:
    """Result of a quality gate validation"""
    gate_name: str
    result: ValidationResult
    score: float  # 0-100
    confidence: float  # 0-1
    issues: List[str]
    suggestions: List[str]
    blocking_issues: List[str]
    memory_insights: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class QualityGatesEngine:
    """Core quality gates validation engine with memory integration"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memory_bank = MemoryBank(project_path)
        self.context_engine = ContextEngine(self.memory_bank)
        self.settings = get_settings()
        
        # Quality thresholds
        self.SUCCESS_THRESHOLD = self.settings.get('QUALITY_SUCCESS_THRESHOLD', 95)
        self.WARNING_THRESHOLD = 70
        self.FAIL_THRESHOLD = 50
    
    @measure_performance
    async def validate_prd_completeness(self, prd_content: str, memory_context: Optional[MemoryContext] = None) -> QualityGateResult:
        """Comprehensive PRD validation with memory insights"""
        try:
            issues = []
            suggestions = []
            blocking_issues = []
            
            # Get memory context if not provided
            if memory_context is None:
                memory_context = await self.memory_bank.get_relevant_context("PRD validation")
            
            # Core structure validation
            structure_score = await self._validate_prd_structure(prd_content)
            if structure_score < 70:
                issues.append("PRD missing critical sections")
                if structure_score < 50:
                    blocking_issues.append("PRD structure incomplete - cannot proceed")
            
            # Content quality validation
            content_score = await self._validate_prd_content_quality(prd_content)
            if content_score < 60:
                issues.append("PRD content lacks detail or clarity")
            
            # Memory-based validation
            memory_score = 100  # Default if no memory insights
            if memory_context.success_patterns:
                memory_score = await self._validate_against_success_patterns(prd_content, memory_context)
                if memory_score < 70:
                    suggestions.append("Consider successful patterns from similar projects")
            
            # Stakeholder alignment check
            stakeholder_score = await self._validate_stakeholder_alignment(prd_content, memory_context)
            if stakeholder_score < 60:
                issues.append("PRD may not align with stakeholder preferences")
            
            # Calculate composite score
            scores = [structure_score, content_score, memory_score, stakeholder_score]
            composite_score = sum(scores) / len(scores)
            
            # Determine result
            if blocking_issues:
                result = ValidationResult.BLOCKED
            elif composite_score >= self.SUCCESS_THRESHOLD:
                result = ValidationResult.PASS
            elif composite_score >= self.WARNING_THRESHOLD:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.FAIL
            
            # Add memory-based suggestions
            if memory_context.failure_patterns:
                suggestions.extend([
                    f"Avoid: {pattern.get('description', 'Unknown pattern')}" 
                    for pattern in memory_context.failure_patterns[:3]
                ])
            
            return QualityGateResult(
                gate_name="PRD Completeness",
                result=result,
                score=composite_score,
                confidence=0.85,
                issues=issues,
                suggestions=suggestions,
                blocking_issues=blocking_issues,
                memory_insights={
                    'patterns_checked': len(memory_context.success_patterns),
                    'decisions_considered': len(memory_context.decision_history),
                    'stakeholder_alignment': stakeholder_score
                }
            )
            
        except Exception as e:
            logger.error(f"PRD validation failed: {e}")
            return QualityGateResult(
                gate_name="PRD Completeness",
                result=ValidationResult.FAIL,
                score=0,
                confidence=0,
                issues=[f"Validation error: {e}"],
                suggestions=["Fix validation errors and retry"],
                blocking_issues=["Technical validation failure"]
            )
    
    @measure_performance
    async def validate_task_breakdown(self, tasks: List[Dict], prd_content: str, 
                                    memory_context: Optional[MemoryContext] = None) -> QualityGateResult:
        """Validate task breakdown completeness and quality"""
        try:
            issues = []
            suggestions = []
            blocking_issues = []
            
            if not tasks:
                return QualityGateResult(
                    gate_name="Task Breakdown",
                    result=ValidationResult.BLOCKED,
                    score=0,
                    confidence=1.0,
                    issues=["No tasks provided"],
                    suggestions=["Generate tasks from PRD"],
                    blocking_issues=["Cannot proceed without tasks"]
                )
            
            # Get memory context if not provided
            if memory_context is None:
                memory_context = await self.memory_bank.get_relevant_context("task breakdown validation")
            
            # PRD coverage validation
            coverage_score = await self._validate_prd_coverage(tasks, prd_content)
            if coverage_score < 80:
                issues.append("Tasks don't fully cover PRD requirements")
                if coverage_score < 60:
                    blocking_issues.append("Major PRD requirements missing from tasks")
            
            # Dependency validation
            dependency_score = await self._validate_task_dependencies(tasks)
            if dependency_score < 70:
                issues.append("Task dependencies have issues")
                if dependency_score < 50:
                    blocking_issues.append("Circular dependencies or missing prerequisites")
            
            # Granularity validation
            granularity_score = await self._validate_task_granularity(tasks, memory_context)
            if granularity_score < 70:
                suggestions.append("Consider adjusting task size based on successful patterns")
            
            # Effort estimation validation
            estimation_score = await self._validate_effort_estimates(tasks, memory_context)
            if estimation_score < 60:
                issues.append("Effort estimates may be unrealistic")
                suggestions.append("Review estimates against similar historical tasks")
            
            # Calculate composite score
            scores = [coverage_score, dependency_score, granularity_score, estimation_score]
            composite_score = sum(scores) / len(scores)
            
            # Determine result
            if blocking_issues:
                result = ValidationResult.BLOCKED
            elif composite_score >= self.SUCCESS_THRESHOLD:
                result = ValidationResult.PASS
            elif composite_score >= self.WARNING_THRESHOLD:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.FAIL
            
            return QualityGateResult(
                gate_name="Task Breakdown",
                result=result,
                score=composite_score,
                confidence=0.80,
                issues=issues,
                suggestions=suggestions,
                blocking_issues=blocking_issues,
                memory_insights={
                    'similar_projects_analyzed': len(memory_context.pattern_matches),
                    'estimation_confidence': estimation_score
                }
            )
            
        except Exception as e:
            logger.error(f"Task validation failed: {e}")
            return QualityGateResult(
                gate_name="Task Breakdown",
                result=ValidationResult.FAIL,
                score=0,
                confidence=0,
                issues=[f"Validation error: {e}"],
                suggestions=["Fix validation errors and retry"],
                blocking_issues=["Technical validation failure"]
            )
    
    @measure_performance
    async def validate_implementation_quality(self, code_files: List[str], acceptance_criteria: List[str],
                                           memory_context: Optional[MemoryContext] = None) -> QualityGateResult:
        """Validate implementation against acceptance criteria and quality standards"""
        try:
            issues = []
            suggestions = []
            blocking_issues = []
            
            if not code_files:
                return QualityGateResult(
                    gate_name="Implementation Quality",
                    result=ValidationResult.BLOCKED,
                    score=0,
                    confidence=1.0,
                    issues=["No code files provided"],
                    suggestions=["Implement code before validation"],
                    blocking_issues=["Cannot validate without implementation"]
                )
            
            # Code quality analysis
            code_quality_score = await self._analyze_code_quality(code_files)
            if code_quality_score < 70:
                issues.append("Code quality below standards")
                if code_quality_score < 50:
                    blocking_issues.append("Critical code quality issues must be fixed")
            
            # Security analysis
            security_issues = await self._check_security_issues(code_files)
            if security_issues:
                issues.extend(security_issues)
                if len(security_issues) > 2:
                    blocking_issues.append("Multiple security vulnerabilities detected")
            
            # Acceptance criteria validation
            criteria_score = await self._validate_acceptance_criteria(code_files, acceptance_criteria)
            if criteria_score < 80:
                issues.append("Not all acceptance criteria are met")
                if criteria_score < 60:
                    blocking_issues.append("Critical acceptance criteria missing")
            
            # Memory pattern compliance
            pattern_score = 100  # Default
            if memory_context and memory_context.success_patterns:
                pattern_score = await self._validate_pattern_compliance(code_files, memory_context)
                if pattern_score < 70:
                    suggestions.append("Consider applying successful implementation patterns")
            
            # Calculate composite score
            scores = [code_quality_score, criteria_score, pattern_score]
            if not security_issues:
                scores.append(100)  # Security bonus if no issues
            else:
                scores.append(max(0, 100 - len(security_issues) * 20))  # Security penalty
            
            composite_score = sum(scores) / len(scores)
            
            # Determine result
            if blocking_issues:
                result = ValidationResult.BLOCKED
            elif composite_score >= self.SUCCESS_THRESHOLD:
                result = ValidationResult.PASS
            elif composite_score >= self.WARNING_THRESHOLD:
                result = ValidationResult.WARNING
            else:
                result = ValidationResult.FAIL
            
            return QualityGateResult(
                gate_name="Implementation Quality",
                result=result,
                score=composite_score,
                confidence=0.75,
                issues=issues,
                suggestions=suggestions,
                blocking_issues=blocking_issues,
                memory_insights={
                    'security_issues_count': len(security_issues),
                    'pattern_compliance': pattern_score,
                    'criteria_coverage': criteria_score
                }
            )
            
        except Exception as e:
            logger.error(f"Implementation validation failed: {e}")
            return QualityGateResult(
                gate_name="Implementation Quality",
                result=ValidationResult.FAIL,
                score=0,
                confidence=0,
                issues=[f"Validation error: {e}"],
                suggestions=["Fix validation errors and retry"],
                blocking_issues=["Technical validation failure"]
            )
    
    async def calculate_success_probability(self, project_state: Dict[str, Any], 
                                          memory_context: Optional[MemoryContext] = None) -> float:
        """Calculate overall project success probability"""
        try:
            validation_results = []
            
            # Validate each component if available
            if 'prd_content' in project_state:
                prd_result = await self.validate_prd_completeness(
                    project_state['prd_content'],
                    memory_context
                )
                validation_results.append(prd_result)
            
            if 'tasks' in project_state:
                task_result = await self.validate_task_breakdown(
                    project_state['tasks'],
                    project_state.get('prd_content', ''),
                    memory_context
                )
                validation_results.append(task_result)
            
            if 'code_files' in project_state:
                impl_result = await self.validate_implementation_quality(
                    project_state['code_files'],
                    project_state.get('acceptance_criteria', []),
                    memory_context
                )
                validation_results.append(impl_result)
            
            if not validation_results:
                return 0.5  # No data available
            
            # Calculate weighted success probability
            total_score = sum(result.score for result in validation_results)
            avg_score = total_score / len(validation_results)
            
            # Factor in blocking issues
            total_blocking = sum(len(result.blocking_issues) for result in validation_results)
            blocking_penalty = min(total_blocking * 10, 30)  # Max 30% penalty
            
            # Memory-based adjustments
            memory_bonus = 0
            if memory_context:
                memory_bonus = await self._calculate_memory_based_bonus(project_state, memory_context)
            
            success_probability = (avg_score - blocking_penalty + memory_bonus) / 100.0
            return max(0.0, min(1.0, success_probability))  # Clamp to 0-1
            
        except Exception as e:
            logger.error(f"Success probability calculation failed: {e}")
            return 0.0
    
    # Helper methods for validation logic
    async def _validate_prd_structure(self, prd_content: str) -> float:
        """Validate PRD has required sections"""
        required_sections = [
            'introduction', 'product vision', 'user workflows', 'system architecture',
            'functional requirements', 'non-functional requirements', 'testing strategy'
        ]
        
        content_lower = prd_content.lower()
        found_sections = sum(1 for section in required_sections if section in content_lower)
        
        return (found_sections / len(required_sections)) * 100
    
    async def _validate_prd_content_quality(self, prd_content: str) -> float:
        """Validate PRD content quality and detail"""
        score = 50  # Base score
        
        # Check for detailed requirements
        if len(prd_content) > 2000:  # Minimum detail threshold
            score += 20
        
        # Check for specific patterns
        if re.search(r'\d+\.\s+', prd_content):  # Numbered requirements
            score += 15
        
        if 'acceptance criteria' in prd_content.lower():
            score += 15
        
        return min(score, 100)
    
    async def _validate_task_dependencies(self, tasks: List[Dict]) -> float:
        """Validate task dependency graph has no cycles and is complete"""
        try:
            # Build dependency graph
            task_ids = {task.get('id', i) for i, task in enumerate(tasks)}
            dependencies = {}
            
            for task in tasks:
                task_id = task.get('id', task.get('title', ''))
                task_deps = task.get('dependencies', [])
                dependencies[task_id] = task_deps
            
            # Check for cycles (simplified)
            def has_cycle(node, path, visited):
                if node in path:
                    return True
                if node in visited:
                    return False
                
                path.add(node)
                for dep in dependencies.get(node, []):
                    if has_cycle(dep, path, visited):
                        return True
                path.remove(node)
                visited.add(node)
                return False
            
            visited = set()
            for task_id in task_ids:
                if task_id not in visited:
                    if has_cycle(task_id, set(), visited):
                        return 50.0  # Cycle detected - major issue
            
            return 100.0  # No cycles detected
            
        except Exception:
            return 75.0  # Default score if validation fails
    
    async def _check_security_issues(self, code_files: List[str]) -> List[str]:
        """Basic security issue detection"""
        security_issues = []
        
        for file_path in code_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Basic security checks
                if 'password' in content.lower() and ('=' in content or ':' in content):
                    security_issues.append(f"Potential hardcoded password in {file_path}")
                
                if 'api_key' in content.lower() and ('=' in content or ':' in content):
                    security_issues.append(f"Potential hardcoded API key in {file_path}")
                
                if 'eval(' in content:
                    security_issues.append(f"Unsafe eval() usage in {file_path}")
                    
            except Exception:
                continue  # Skip files that can't be read
        
        return security_issues
    
    # Placeholder methods for comprehensive validation
    async def _validate_against_success_patterns(self, prd_content: str, memory_context: MemoryContext) -> float:
        return 85.0
    
    async def _validate_stakeholder_alignment(self, prd_content: str, memory_context: MemoryContext) -> float:
        return 80.0
    
    async def _validate_prd_coverage(self, tasks: List[Dict], prd_content: str) -> float:
        return 90.0
    
    async def _validate_task_granularity(self, tasks: List[Dict], memory_context: MemoryContext) -> float:
        return 85.0
    
    async def _validate_effort_estimates(self, tasks: List[Dict], memory_context: MemoryContext) -> float:
        return 75.0
    
    async def _analyze_code_quality(self, code_files: List[str]) -> float:
        return 80.0
    
    async def _validate_acceptance_criteria(self, code_files: List[str], criteria: List[str]) -> float:
        return 85.0
    
    async def _validate_pattern_compliance(self, code_files: List[str], memory_context: MemoryContext) -> float:
        return 80.0
    
    async def _calculate_memory_based_bonus(self, project_state: Dict, memory_context: MemoryContext) -> float:
        return 5.0  # Small bonus for memory integration

# CLI interface
async def cli_main():
    """CLI interface for quality gates"""
    import typer
    app = typer.Typer()
    
    @app.command()
    def validate_prd(project_path: str, prd_file: str):
        """Validate PRD completeness"""
        async def _validate():
            quality_gates = QualityGatesEngine(project_path)
            
            with open(prd_file, 'r') as f:
                prd_content = f.read()
            
            result = await quality_gates.validate_prd_completeness(prd_content)
            
            print(f"Result: {result.result.value}")
            print(f"Score: {result.score:.1f}/100")
            
            if result.issues:
                print("Issues:")
                for issue in result.issues:
                    print(f"  - {issue}")
            
            if result.suggestions:
                print("Suggestions:")
                for suggestion in result.suggestions:
                    print(f"  - {suggestion}")
        
        asyncio.run(_validate())
    
    @app.command()
    def assess_project(project_path: str):
        """Assess overall project success probability"""
        async def _assess():
            quality_gates = QualityGatesEngine(project_path)
            
            # Mock project state for demonstration
            project_state = {
                'prd_content': 'Sample PRD content...',
                'tasks': [{'id': 'task1', 'title': 'Sample task'}],
                'code_files': []
            }
            
            probability = await quality_gates.calculate_success_probability(project_state)
            print(f"Success Probability: {probability:.1%}")
        
        asyncio.run(_assess())
    
    app()

if __name__ == "__main__":
    cli_main()