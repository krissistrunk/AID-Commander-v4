#!/usr/bin/env python3
"""
Comprehensive tests for Memory Service
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime

from memory_service import MemoryBank, MemoryContext
from context_engine import ContextEngine
from quality_gates import QualityGatesEngine

class TestMemoryBank:
    """Test memory bank core functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.memory_bank = MemoryBank(str(self.test_dir))
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir)
    
    @pytest.mark.asyncio
    async def test_memory_bank_initialization(self):
        """Test memory bank initializes correctly"""
        await self.memory_bank._initialize_memory_structure()
        
        # Check all memory files exist
        expected_files = [
            "project_essence.md",
            "active_context.md", 
            "decision_history.md",
            "conversation_memory.md",
            "architecture_evolution.md",
            "task_patterns.md",
            "stakeholder_context.md",
            "integration_memory.md",
            "success_patterns.md",
            "failure_analysis.md"
        ]
        
        for file in expected_files:
            assert (self.memory_bank.memory_dir / file).exists()
        
        # Check database exists
        assert self.memory_bank._db_path.exists()
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_decision(self):
        """Test decision storage and retrieval"""
        decision = {
            'title': 'Test Decision',
            'context': 'Testing decision storage',
            'options': [
                {'name': 'Option A', 'pros': 'Fast', 'cons': 'Less robust'}
            ],
            'chosen_option': 'Option A',
            'rationale': 'Speed is critical for this test'
        }
        
        decision_id = await self.memory_bank.store_decision(decision)
        assert decision_id.startswith('decision_')
        
        # Retrieve and verify
        context = await self.memory_bank.get_relevant_context('Test Decision')
        assert context.decision_history
        
        stored_decision = context.decision_history[0]
        assert stored_decision['title'] == 'Test Decision'
        assert stored_decision['rationale'] == 'Speed is critical for this test'
    
    @pytest.mark.asyncio
    async def test_context_retrieval_with_empty_memory(self):
        """Test context retrieval with no stored data"""
        context = await self.memory_bank.get_relevant_context('nonexistent query')
        
        # Should return empty context without error
        assert isinstance(context, MemoryContext)
        assert context.direct_references == []
        assert context.decision_history == []
    
    @pytest.mark.asyncio
    async def test_conversation_tracking(self):
        """Test conversation tracking functionality"""
        interaction = {
            'type': 'test_interaction',
            'user_message': 'Test message',
            'ai_response': 'Test response',
            'context': 'Test context'
        }
        
        success = await self.memory_bank.track_conversation(interaction)
        assert success
    
    @pytest.mark.asyncio
    async def test_invalid_decision_storage(self):
        """Test error handling for invalid decision"""
        invalid_decision = {
            'title': 'Invalid Decision'
            # Missing required fields
        }
        
        with pytest.raises(ValueError):
            await self.memory_bank.store_decision(invalid_decision)
    
    @pytest.mark.asyncio
    async def test_encryption_key_generation(self):
        """Test encryption key is generated and persisted"""
        key1 = self.memory_bank._get_or_create_encryption_key()
        key2 = self.memory_bank._get_or_create_encryption_key()
        
        # Same key should be returned on subsequent calls
        assert key1 == key2
        
        # Key file should exist
        key_file = self.memory_bank.memory_dir / ".encryption_key"
        assert key_file.exists()
        assert key_file.read_text().strip() == key1

class TestContextEngine:
    """Test context engine functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.memory_bank = MemoryBank(str(self.test_dir))
        self.context_engine = ContextEngine(self.memory_bank)
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir)
    
    @pytest.mark.asyncio
    async def test_context_retrieval_integration(self):
        """Test context engine integration with memory bank"""
        # Store some test data first
        await self.memory_bank.store_decision({
            'title': 'Authentication Decision',
            'context': 'Need to choose auth method',
            'options': [],
            'chosen_option': 'JWT',
            'rationale': 'Stateless and scalable'
        })
        
        # Retrieve context for related query
        context = await self.context_engine.get_relevant_context('authentication system')
        
        assert context['direct_references'] is not None
        assert context['recent_decisions'] is not None
        assert 'timestamp' in context
    
    @pytest.mark.asyncio
    async def test_task_suggestion_empty_memory(self):
        """Test task suggestions with empty memory"""
        suggestions = await self.context_engine.suggest_tasks_from_memory('build web app')
        
        # Should return empty list without error
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_risk_prediction_empty_memory(self):
        """Test risk prediction with empty memory"""
        project_state = {
            'phase': 'implementation',
            'progress': '50%'
        }
        
        risks = await self.context_engine.predict_risk_factors(project_state)
        
        # Should return empty list without error
        assert isinstance(risks, list)
        assert len(risks) == 0
    
    @pytest.mark.asyncio
    async def test_key_terms_extraction(self):
        """Test key terms extraction"""
        text = "Build authentication system using JWT tokens for the web application"
        terms = self.context_engine._extract_key_terms(text)
        
        assert 'authentication' in terms
        assert 'system' in terms
        assert 'tokens' in terms
        assert 'application' in terms
        # Common words should be filtered out
        assert 'the' not in terms
        assert 'for' not in terms

class TestQualityGates:
    """Test quality gates functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.quality_gates = QualityGatesEngine(str(self.test_dir))
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir)
    
    @pytest.mark.asyncio
    async def test_prd_validation_basic(self):
        """Test basic PRD validation"""
        prd_content = """
        # Introduction & Product Vision
        This is a test PRD.
        
        # User Workflows & Experience
        Users will do things.
        
        # System Architecture & Technical Foundation
        We will use standard architecture.
        
        # Functional Requirements & Implementation Tasks
        The system must work.
        
        # Non-Functional Requirements
        Performance requirements here.
        
        # Testing Strategy
        We will test everything.
        """
        
        result = await self.quality_gates.validate_prd_completeness(prd_content)
        
        assert result.gate_name == "PRD Completeness"
        assert result.score > 50  # Should pass basic structure check
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)
    
    @pytest.mark.asyncio
    async def test_prd_validation_incomplete(self):
        """Test PRD validation with incomplete content"""
        prd_content = "This is a minimal PRD with no structure."
        
        result = await self.quality_gates.validate_prd_completeness(prd_content)
        
        assert result.score < 50  # Should fail with low score
        assert len(result.issues) > 0
        assert "missing critical sections" in result.issues[0].lower()
    
    @pytest.mark.asyncio
    async def test_task_validation_basic(self):
        """Test basic task validation"""
        tasks = [
            {
                'id': 'task1',
                'title': 'Setup authentication',
                'description': 'Implement JWT authentication',
                'dependencies': [],
                'estimate': '3 days'
            },
            {
                'id': 'task2', 
                'title': 'Create user interface',
                'description': 'Build login/signup forms',
                'dependencies': ['task1'],
                'estimate': '2 days'
            }
        ]
        
        prd_content = "System needs authentication and user interface"
        
        result = await self.quality_gates.validate_task_breakdown(tasks, prd_content)
        
        assert result.gate_name == "Task Breakdown"
        assert result.score > 0
        assert isinstance(result.blocking_issues, list)
    
    @pytest.mark.asyncio
    async def test_task_validation_empty(self):
        """Test task validation with empty task list"""
        tasks = []
        prd_content = "Some requirements"
        
        result = await self.quality_gates.validate_task_breakdown(tasks, prd_content)
        
        assert result.result.value == "blocked"
        assert len(result.blocking_issues) > 0
        assert "No tasks provided" in result.issues[0]
    
    @pytest.mark.asyncio
    async def test_implementation_validation_no_files(self):
        """Test implementation validation with no files"""
        code_files = []
        acceptance_criteria = ["System should work"]
        
        result = await self.quality_gates.validate_implementation_quality(code_files, acceptance_criteria)
        
        assert result.result.value == "blocked"
        assert "No code files provided" in result.issues[0]
    
    @pytest.mark.asyncio
    async def test_success_probability_calculation(self):
        """Test success probability calculation"""
        project_state = {
            'prd_content': 'Basic PRD content',
            'tasks': [{'id': 'task1', 'title': 'Test task'}],
            'code_files': []
        }
        
        probability = await self.quality_gates.calculate_success_probability(project_state)
        
        assert 0.0 <= probability <= 1.0
        assert isinstance(probability, float)

# Integration tests
class TestFullIntegration:
    """Test full system integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir)
    
    @pytest.mark.asyncio
    async def test_memory_to_quality_gates_integration(self):
        """Test memory bank feeding into quality gates"""
        memory_bank = MemoryBank(str(self.test_dir))
        quality_gates = QualityGatesEngine(str(self.test_dir))
        
        # Store decision in memory
        await memory_bank.store_decision({
            'title': 'Use React for frontend',
            'context': 'Need modern UI framework',
            'options': [
                {'name': 'React', 'pros': 'Popular, good ecosystem'},
                {'name': 'Vue', 'pros': 'Simpler learning curve'}
            ],
            'chosen_option': 'React',
            'rationale': 'Team expertise and ecosystem'
        })
        
        # Get memory context
        memory_context = await memory_bank.get_relevant_context('frontend framework')
        
        # Use in quality gates
        prd_content = "Build React frontend application"
        result = await quality_gates.validate_prd_completeness(prd_content, memory_context)
        
        assert result.memory_insights is not None
        assert result.memory_insights['decisions_considered'] >= 0
    
    @pytest.mark.asyncio
    async def test_context_engine_with_populated_memory(self):
        """Test context engine with populated memory bank"""
        memory_bank = MemoryBank(str(self.test_dir))
        context_engine = ContextEngine(memory_bank)
        
        # Populate memory with test data
        await memory_bank.store_decision({
            'title': 'Database Choice',
            'context': 'Need to select database',
            'options': [],
            'chosen_option': 'PostgreSQL',
            'rationale': 'ACID compliance and reliability'
        })
        
        await memory_bank.track_conversation({
            'type': 'user_question',
            'user_message': 'What database should we use?',
            'ai_response': 'PostgreSQL is recommended',
            'context': 'Database selection discussion'
        })
        
        # Test context retrieval
        context = await context_engine.get_relevant_context('database selection')
        
        # Should find relevant information
        assert len(context['recent_decisions']) > 0
        assert context['recent_decisions'][0]['title'] == 'Database Choice'
    
    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self):
        """Test a complete workflow from start to finish"""
        memory_bank = MemoryBank(str(self.test_dir))
        context_engine = ContextEngine(memory_bank)
        quality_gates = QualityGatesEngine(str(self.test_dir))
        
        # Step 1: Store initial project decision
        await memory_bank.store_decision({
            'title': 'Project Technology Stack',
            'context': 'Choose technologies for web application',
            'options': [],
            'chosen_option': 'Python Flask + React',
            'rationale': 'Team familiarity and rapid development'
        })
        
        # Step 2: Validate PRD
        prd_content = """
        # Introduction & Product Vision
        Build a task management web application
        
        # User Workflows & Experience  
        Users can create, edit, and delete tasks
        
        # System Architecture & Technical Foundation
        Python Flask backend with React frontend
        
        # Functional Requirements & Implementation Tasks
        - User authentication
        - Task CRUD operations
        - Task filtering and search
        
        # Non-Functional Requirements
        - Support 1000 concurrent users
        - 99.9% uptime
        
        # Testing Strategy
        Unit tests and integration tests
        """
        
        memory_context = await memory_bank.get_relevant_context('PRD validation')
        prd_result = await quality_gates.validate_prd_completeness(prd_content, memory_context)
        
        assert prd_result.result.value in ['pass', 'warning']
        assert prd_result.score > 70
        
        # Step 3: Generate and validate tasks
        tasks = [
            {
                'id': 'task1',
                'title': 'Setup Flask backend',
                'description': 'Initialize Flask application with basic structure',
                'dependencies': [],
                'estimate': '1 day'
            },
            {
                'id': 'task2',
                'title': 'Implement user authentication',
                'description': 'Add JWT-based authentication system',
                'dependencies': ['task1'],
                'estimate': '2 days'
            },
            {
                'id': 'task3',
                'title': 'Create React frontend',
                'description': 'Setup React application with routing',
                'dependencies': ['task1'],
                'estimate': '2 days'
            }
        ]
        
        task_result = await quality_gates.validate_task_breakdown(tasks, prd_content, memory_context)
        
        assert task_result.result.value in ['pass', 'warning']
        assert len(task_result.blocking_issues) == 0
        
        # Step 4: Calculate overall success probability
        project_state = {
            'prd_content': prd_content,
            'tasks': tasks,
            'code_files': []
        }
        
        success_probability = await quality_gates.calculate_success_probability(project_state, memory_context)
        
        assert success_probability > 0.5  # Should have reasonable success probability
        
        # Step 5: Track the complete workflow in memory
        await memory_bank.track_conversation({
            'type': 'workflow_completion',
            'workflow': 'PRD_to_tasks_validation',
            'prd_score': prd_result.score,
            'task_score': task_result.score,
            'success_probability': success_probability,
            'context': 'Complete workflow test'
        })
        
        # Verify everything was tracked
        final_context = await memory_bank.get_relevant_context('workflow completion')
        assert len(final_context.decision_history) >= 1
        assert final_context.decision_history[0]['title'] == 'Project Technology Stack'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])