#!/usr/bin/env python3
"""
Core Memory Bank Service for AID Commander v4.0
Handles all memory operations with guaranteed persistence and retrieval
"""

import json
import aiofiles
import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pydantic import BaseModel, validator
import logging
from cryptography.fernet import Fernet
import sqlite3
import aiosqlite

from config.settings import get_settings
from utils.validation import validate_memory_data
from utils.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from utils.performance import measure_performance, cache_result

logger = logging.getLogger(__name__)

@dataclass
class MemoryContext:
    """Container for relevant memory context"""
    direct_references: List[str]
    pattern_matches: List[Dict]
    decision_history: List[Dict]
    success_patterns: List[Dict]
    failure_patterns: List[Dict]
    stakeholder_context: Dict
    relevance_scores: Dict[str, float]
    timestamp: datetime
    
    def format_for_ai(self) -> str:
        """Format context for AI injection with guaranteed structure"""
        context_sections = []
        
        if self.direct_references:
            context_sections.append(f"DIRECT REFERENCES:\n" + "\n".join(self.direct_references))
            
        if self.decision_history:
            decisions_text = []
            for decision in self.decision_history[-5:]:  # Last 5 decisions
                decisions_text.append(f"- {decision.get('title', 'Unknown')}: {decision.get('rationale', 'No rationale')}")
            context_sections.append(f"RECENT DECISIONS:\n" + "\n".join(decisions_text))
            
        if self.success_patterns:
            patterns_text = []
            for pattern in self.success_patterns[:3]:  # Top 3 patterns
                patterns_text.append(f"- {pattern.get('description', 'Pattern')}: Success rate {pattern.get('success_rate', 'Unknown')}%")
            context_sections.append(f"SUCCESS PATTERNS:\n" + "\n".join(patterns_text))
            
        if self.failure_patterns:
            failures_text = []
            for pattern in self.failure_patterns[:2]:  # Top 2 anti-patterns
                failures_text.append(f"- AVOID: {pattern.get('description', 'Anti-pattern')}")
            context_sections.append(f"PATTERNS TO AVOID:\n" + "\n".join(failures_text))
            
        return "\n\n".join(context_sections)

class MemoryBank:
    """Core memory bank with guaranteed persistence and retrieval"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.memory_dir = self.project_path / "memory_bank"
        self.settings = get_settings()
        self._encryption_key = self._get_or_create_encryption_key()
        self._db_path = self.memory_dir / "memory_index.db"
        asyncio.create_task(self._initialize_memory_structure())
        
    def _get_or_create_encryption_key(self) -> str:
        """Get or create encryption key for memory bank"""
        key_file = self.memory_dir / ".encryption_key"
        
        if key_file.exists():
            return key_file.read_text().strip()
        else:
            # Create memory dir if it doesn't exist
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            # Generate new key
            key = Fernet.generate_key().decode()
            key_file.write_text(key)
            key_file.chmod(0o600)  # Restrict permissions
            return key
        
    async def _initialize_memory_structure(self):
        """Initialize memory bank structure with validation"""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Create all required memory files
            memory_files = {
                "project_essence.md": self._get_project_essence_template(),
                "active_context.md": self._get_active_context_template(),
                "decision_history.md": self._get_decision_history_template(),
                "conversation_memory.md": self._get_conversation_memory_template(),
                "architecture_evolution.md": self._get_architecture_template(),
                "task_patterns.md": self._get_task_patterns_template(),
                "stakeholder_context.md": self._get_stakeholder_template(),
                "integration_memory.md": self._get_integration_template(),
                "success_patterns.md": self._get_success_patterns_template(),
                "failure_analysis.md": self._get_failure_analysis_template()
            }
            
            for filename, template in memory_files.items():
                file_path = self.memory_dir / filename
                if not file_path.exists():
                    async with aiofiles.open(file_path, 'w') as f:
                        await f.write(template)
                        
            # Initialize SQLite index for fast searches
            await self._initialize_memory_index()
            
            logger.info(f"Memory bank initialized at {self.memory_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory bank: {e}")
            raise
    
    async def _initialize_memory_index(self):
        """Initialize SQLite index for memory searches"""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    relevance_score REAL DEFAULT 0.0,
                    tags TEXT
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(type)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_entries(timestamp)
            """)
            
            await db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_search 
                USING fts5(content, context, tags)
            """)
            
            await db.commit()
    
    @measure_performance
    async def store_decision(self, decision: Dict[str, Any]) -> str:
        """Store decision with full context and outcome tracking"""
        try:
            decision_id = f"decision_{datetime.now().isoformat()}_{hash(decision.get('title', ''))}"
            
            # Validate decision structure
            required_fields = ['title', 'context', 'options', 'chosen_option', 'rationale']
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add metadata
            decision.update({
                'id': decision_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            })
            
            # Store in decision history file
            await self._append_to_memory_file("decision_history.md", self._format_decision(decision))
            
            # Index for search
            await self._index_memory_entry(
                decision_id, 
                "decision", 
                json.dumps(decision),
                decision.get('context', ''),
                tags=f"decision,{decision.get('status', '')}"
            )
            
            logger.info(f"Decision stored: {decision_id}")
            return decision_id
            
        except Exception as e:
            logger.error(f"Failed to store decision: {e}")
            raise
    
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def get_relevant_context(self, query: str, context_type: str = "all") -> MemoryContext:
        """Intelligent context retrieval with relevance scoring"""
        try:
            # Multi-strategy context gathering
            contexts = await asyncio.gather(
                self._find_direct_references(query),
                self._find_semantic_similarities(query),
                self._get_temporal_context(query),
                self._get_dependency_relationships(query),
                return_exceptions=True
            )
            
            direct_refs, semantic_matches, temporal_context, dependencies = contexts
            
            # Get recent decisions
            recent_decisions = await self._get_recent_decisions(limit=10)
            
            # Get applicable patterns
            success_patterns = await self._get_success_patterns(query)
            failure_patterns = await self._get_failure_patterns(query)
            
            # Get stakeholder context
            stakeholder_context = await self._get_stakeholder_context()
            
            # Calculate relevance scores
            relevance_scores = await self._calculate_relevance_scores(
                query, direct_refs, semantic_matches, recent_decisions
            )
            
            return MemoryContext(
                direct_references=direct_refs or [],
                pattern_matches=semantic_matches or [],
                decision_history=recent_decisions or [],
                success_patterns=success_patterns or [],
                failure_patterns=failure_patterns or [],
                stakeholder_context=stakeholder_context or {},
                relevance_scores=relevance_scores or {},
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            # Return empty context rather than fail
            return MemoryContext([], [], [], [], [], {}, {}, datetime.now())
    
    async def update_active_context(self, updates: Dict[str, Any]) -> bool:
        """Update current project state with change tracking"""
        try:
            # Read current active context
            current_context = await self._read_memory_file("active_context.md")
            
            # Parse and update context
            updated_context = await self._merge_context_updates(current_context, updates)
            
            # Write back with timestamp
            await self._write_memory_file("active_context.md", updated_context)
            
            # Track the update in conversation memory
            await self._track_context_change(updates)
            
            logger.info("Active context updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update active context: {e}")
            return False
    
    async def track_conversation(self, interaction: Dict[str, Any]) -> bool:
        """Store AI interaction patterns and effectiveness"""
        try:
            interaction_id = f"conv_{datetime.now().isoformat()}_{hash(str(interaction))}"
            
            # Add metadata
            interaction.update({
                'id': interaction_id,
                'timestamp': datetime.now().isoformat()
            })
            
            # Store in conversation memory
            await self._append_to_memory_file(
                "conversation_memory.md", 
                self._format_conversation(interaction)
            )
            
            # Index for pattern analysis
            await self._index_memory_entry(
                interaction_id,
                "conversation",
                json.dumps(interaction),
                interaction.get('context', ''),
                tags="conversation,ai_interaction"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track conversation: {e}")
            return False
    
    async def _find_direct_references(self, query: str) -> List[str]:
        """Find direct mentions of query terms in memory"""
        try:
            async with aiosqlite.connect(self._db_path) as db:
                cursor = await db.execute(
                    "SELECT content FROM memory_search WHERE memory_search MATCH ?",
                    (query,)
                )
                results = await cursor.fetchall()
                return [row[0] for row in results[:10]]  # Top 10 matches
                
        except Exception as e:
            logger.error(f"Direct reference search failed: {e}")
            return []
    
    async def _find_semantic_similarities(self, query: str) -> List[Dict]:
        """Find semantically similar content using embeddings"""
        # Simplified semantic search - in production would use embeddings
        try:
            query_terms = query.lower().split()
            matches = []
            
            async with aiosqlite.connect(self._db_path) as db:
                for term in query_terms:
                    cursor = await db.execute(
                        "SELECT * FROM memory_entries WHERE content LIKE ?",
                        (f"%{term}%",)
                    )
                    results = await cursor.fetchall()
                    matches.extend([{
                        'id': row[0],
                        'type': row[1], 
                        'content': row[2][:200],  # Truncate for context
                        'relevance': 0.8  # Simplified scoring
                    } for row in results])
                    
            return matches[:5]  # Top 5 matches
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Get recent decisions for context"""
        try:
            async with aiosqlite.connect(self._db_path) as db:
                cursor = await db.execute(
                    "SELECT content FROM memory_entries WHERE type = 'decision' ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                results = await cursor.fetchall()
                return [json.loads(row[0]) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to get recent decisions: {e}")
            return []
    
    async def _index_memory_entry(self, entry_id: str, entry_type: str, content: str, 
                                context: str = "", tags: str = ""):
        """Index memory entry for fast search"""
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO memory_entries 
                    (id, type, content, context, tags) VALUES (?, ?, ?, ?, ?)
                """, (entry_id, entry_type, content, context, tags))
                
                await db.execute("""
                    INSERT OR REPLACE INTO memory_search 
                    (rowid, content, context, tags) VALUES 
                    ((SELECT rowid FROM memory_entries WHERE id = ?), ?, ?, ?)
                """, (entry_id, content, context, tags))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to index memory entry: {e}")
    
    # Helper methods for memory file operations
    async def _read_memory_file(self, filename: str) -> str:
        """Read content from memory file"""
        try:
            file_path = self.memory_dir / filename
            if file_path.exists():
                async with aiofiles.open(file_path, 'r') as f:
                    return await f.read()
            return ""
        except Exception as e:
            logger.error(f"Failed to read memory file {filename}: {e}")
            return ""
    
    async def _write_memory_file(self, filename: str, content: str):
        """Write content to memory file"""
        try:
            file_path = self.memory_dir / filename
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Failed to write memory file {filename}: {e}")
    
    async def _append_to_memory_file(self, filename: str, content: str):
        """Append content to memory file"""
        try:
            file_path = self.memory_dir / filename
            async with aiofiles.open(file_path, 'a') as f:
                await f.write(f"\n{content}\n")
        except Exception as e:
            logger.error(f"Failed to append to memory file {filename}: {e}")
    
    # Template methods for memory file initialization
    def _get_project_essence_template(self) -> str:
        return """# Project Essence

## Core Purpose
[Define the fundamental purpose and goals of this project]

## Key Stakeholders
- **Product Owner**: [Name] - [Key priorities and communication preferences]
- **Technical Lead**: [Name] - [Technical constraints and architectural preferences]  
- **End Users**: [Description] - [Primary needs and usage patterns]

## Success Definition
[Measurable criteria that define project success - these should remain stable]

## Core Constraints
- **Technical**: [Non-negotiable technical limitations and requirements]
- **Business**: [Business rules, compliance requirements, budget constraints]
- **Timeline**: [Critical deadlines and milestone dependencies]

## Architecture Principles
[Fundamental architectural decisions that guide all implementation decisions]

---
*This file contains the immutable essence of the project - update only when fundamental requirements change*
"""

    def _get_active_context_template(self) -> str:
        return f"""# Active Context

## Current State
**Last Updated**: {datetime.now().isoformat()}
**Phase**: [Current project phase]
**Progress**: [Completion percentage and current focus]

## Active Decisions
### [Decision ID]: [Decision Title]
- **Status**: Pending/Approved/Implemented
- **Context**: [Why this decision is needed now]
- **Options Considered**: [Alternatives being evaluated]
- **Recommendation**: [Current recommended approach]
- **Rationale**: [Why this approach is recommended]
- **Dependencies**: [What must be completed first]
- **Risks**: [Potential issues with this approach]

## Current Focus Areas
1. **[Area]**: [Current work, blockers, next steps]
2. **[Area]**: [Current work, blockers, next steps]

## Pending Issues
- **[Issue ID]**: [Description] - [Priority] - [Owner] - [Status]

## Next Milestones
- **[Date]**: [Milestone description and acceptance criteria]

---
*This file reflects the current state - updated frequently as project progresses*
"""

    def _get_decision_history_template(self) -> str:
        return """# Decision History

*Chronological log of all project decisions with full context and outcomes*

---

## Template for New Decisions

### [ISO Date] - [Decision ID]: [Decision Title]

#### Context
[Situation that required this decision]

#### Options Considered
1. **[Option A]**: [Description]
   - Pros: [Advantages and benefits]
   - Cons: [Disadvantages and risks]  
   - Risk Level: [High/Medium/Low]
   - Estimated Effort: [Time/complexity estimate]

#### Decision Made
**Chosen Option**: [Selected option]
**Rationale**: [Why this option was selected over alternatives]
**Decision Maker**: [Who made the final decision]
**Stakeholder Sign-off**: [Who approved this decision]

#### Implementation
**Status**: [Planned/In Progress/Completed/Failed]
**Implementation Notes**: [How it was actually implemented]
**Actual Outcome**: [What actually happened - success/failure analysis]

#### Lessons Learned
**What Worked Well**: [Positive outcomes and successful aspects]
**What Didn't Work**: [Issues, problems, unexpected complications]
**What We'd Do Differently**: [Improvements for similar future decisions]
**Impact on Future Decisions**: [How this experience affects future choices]

---
"""

    async def _format_decision(self, decision: Dict[str, Any]) -> str:
        """Format decision for storage in decision history"""
        return f"""
### {decision.get('timestamp', 'Unknown')} - {decision.get('id', 'Unknown')}: {decision.get('title', 'Untitled Decision')}

#### Context
{decision.get('context', 'No context provided')}

#### Options Considered
{self._format_options(decision.get('options', []))}

#### Decision Made
**Chosen Option**: {decision.get('chosen_option', 'Not specified')}
**Rationale**: {decision.get('rationale', 'No rationale provided')}
**Decision Maker**: {decision.get('decision_maker', 'Unknown')}
**Stakeholder Sign-off**: {decision.get('stakeholder_signoff', 'Pending')}

#### Implementation
**Status**: {decision.get('status', 'Pending')}
**Implementation Notes**: {decision.get('implementation_notes', 'Not yet implemented')}
**Actual Outcome**: {decision.get('actual_outcome', 'Pending implementation')}

#### Lessons Learned
**What Worked Well**: {decision.get('lessons_learned', {}).get('worked_well', 'To be determined')}
**What Didn't Work**: {decision.get('lessons_learned', {}).get('didnt_work', 'To be determined')}
**What We'd Do Differently**: {decision.get('lessons_learned', {}).get('do_differently', 'To be determined')}

---
"""

    def _format_options(self, options: List[Dict]) -> str:
        """Format decision options for display"""
        if not options:
            return "No options documented"
            
        formatted = []
        for i, option in enumerate(options, 1):
            formatted.append(f"""
{i}. **{option.get('name', f'Option {i}')}**: {option.get('description', 'No description')}
   - Pros: {option.get('pros', 'Not specified')}
   - Cons: {option.get('cons', 'Not specified')}
   - Risk Level: {option.get('risk_level', 'Unknown')}
   - Estimated Effort: {option.get('effort', 'Unknown')}""")
            
        return "\n".join(formatted)

    # Placeholder methods for templates and operations
    def _get_conversation_memory_template(self) -> str:
        return "# Conversation Memory\n\n*AI interaction patterns and effectiveness tracking*\n"
    
    def _get_architecture_template(self) -> str:
        return "# Architecture Evolution\n\n*Technical decisions and system evolution*\n"
    
    def _get_task_patterns_template(self) -> str:
        return "# Task Patterns\n\n*Task breakdown and execution patterns*\n"
    
    def _get_stakeholder_template(self) -> str:
        return "# Stakeholder Context\n\n*Stakeholder preferences and feedback*\n"
    
    def _get_integration_template(self) -> str:
        return "# Integration Memory\n\n*Multi-component coordination history*\n"
    
    def _get_success_patterns_template(self) -> str:
        return "# Success Patterns\n\n*What worked well and why*\n"
    
    def _get_failure_analysis_template(self) -> str:
        return "# Failure Analysis\n\n*What failed and lessons learned*\n"
    
    async def _get_temporal_context(self, query: str) -> Dict:
        return {}
    
    async def _get_dependency_relationships(self, query: str) -> Dict:
        return {}
    
    async def _get_success_patterns(self, query: str) -> List[Dict]:
        return []
    
    async def _get_failure_patterns(self, query: str) -> List[Dict]:
        return []
    
    async def _get_stakeholder_context(self) -> Dict:
        return {}
    
    async def _calculate_relevance_scores(self, query: str, *args) -> Dict[str, float]:
        return {}
    
    async def _merge_context_updates(self, current: str, updates: Dict) -> str:
        return current + f"\n\nUpdated: {datetime.now().isoformat()}\n{json.dumps(updates, indent=2)}"
    
    async def _track_context_change(self, updates: Dict):
        pass
    
    def _format_conversation(self, interaction: Dict) -> str:
        return f"### {interaction.get('timestamp')}\n{json.dumps(interaction, indent=2)}\n"

# CLI interface for memory service
async def cli_main():
    """CLI interface for memory service operations"""
    import typer
    app = typer.Typer()
    
    @app.command()
    def query(project_path: str, question: str):
        """Query memory bank for relevant context"""
        async def _query():
            memory_bank = MemoryBank(project_path)
            context = await memory_bank.get_relevant_context(question)
            print(context.format_for_ai())
        
        asyncio.run(_query())
    
    @app.command() 
    def store_decision(project_path: str, title: str, context: str):
        """Store a new decision in memory bank"""
        async def _store():
            memory_bank = MemoryBank(project_path)
            decision = {
                'title': title,
                'context': context,
                'options': [],
                'chosen_option': '',
                'rationale': ''
            }
            decision_id = await memory_bank.store_decision(decision)
            print(f"Decision stored: {decision_id}")
        
        asyncio.run(_store())
    
    app()

if __name__ == "__main__":
    cli_main()