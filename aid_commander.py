#!/usr/bin/env python3
"""
AID Commander v4.0 - AI-Facilitated Iterative Development with Memory Bank
Enhanced main CLI application with memory integration and quality gates
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rich_print

from memory_service import MemoryBank
from context_engine import ContextEngine
from quality_gates import QualityGatesEngine, ValidationResult
from conversation_manager import ConversationManager
from config.settings import get_settings, validate_configuration
from utils.performance import performance_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for enhanced output
console = Console()

# Main Typer app
app = typer.Typer(
    name="aid-commander",
    help="AID Commander v4.0 - AI-Facilitated Iterative Development with Memory Bank"
)

class AIDCommanderV4:
    """Enhanced AID Commander with memory and quality gates"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.settings = get_settings()
        self.project_path = Path(project_path) if project_path else Path.cwd()
        
        # Initialize core components
        self.memory_bank = MemoryBank(str(self.project_path))
        self.context_engine = ContextEngine(self.memory_bank)
        self.quality_gates = QualityGatesEngine(str(self.project_path))
        self.conversation_manager = ConversationManager(str(self.project_path))
        
        console.print(f"[green]AID Commander v4.0 initialized for project: {self.project_path}[/green]")
    
    async def start_project(self, project_name: str, approach: str = "single_prd", 
                          use_memory: bool = True) -> Dict[str, Any]:
        """Start new project with memory integration"""
        try:
            console.print(f"[bold blue]Starting new project: {project_name}[/bold blue]")
            
            project_dir = self.project_path / project_name
            project_dir.mkdir(exist_ok=True)
            
            # Initialize project with memory bank
            if use_memory:
                memory_bank = MemoryBank(str(project_dir))
                await memory_bank._initialize_memory_structure()
                
                # Store initial project decision
                await memory_bank.store_decision({
                    'title': f'Project Initialization: {project_name}',
                    'context': f'Starting new project with {approach} approach',
                    'options': [
                        {'name': 'single_prd', 'description': 'Single PRD approach'},
                        {'name': 'multi_component', 'description': 'Multi-component approach'}
                    ],
                    'chosen_option': approach,
                    'rationale': 'Project structure decision at initialization',
                    'decision_maker': 'User'
                })
                
                console.print("[green]✓ Memory bank initialized[/green]")
            
            # Create basic project structure
            dirs_to_create = ['src', 'tests', 'docs', 'config']
            for dir_name in dirs_to_create:
                (project_dir / dir_name).mkdir(exist_ok=True)
            
            console.print(f"[green]✓ Project {project_name} created successfully[/green]")
            
            return {
                'project_name': project_name,
                'project_path': str(project_dir),
                'approach': approach,
                'memory_enabled': use_memory,
                'status': 'initialized'
            }
            
        except Exception as e:
            logger.error(f"Failed to start project: {e}")
            console.print(f"[red]Error starting project: {e}[/red]")
            raise
    
    async def analyze_with_memory(self, query: str) -> Dict[str, Any]:
        """Analyze query using memory bank intelligence"""
        try:
            console.print(f"[blue]Analyzing: {query}[/blue]")
            
            # Get comprehensive context
            context = await self.context_engine.get_relevant_context(query)
            
            # Generate suggestions
            suggestions = await self.context_engine.suggest_tasks_from_memory(query)
            
            # Identify risks
            risks = await self.context_engine.predict_risk_factors({'query': query})
            
            # Format results
            results = {
                'query': query,
                'context_found': len(context.get('direct_references', [])) > 0,
                'suggestions_count': len(suggestions),
                'risk_factors': len(risks),
                'memory_insights': {
                    'direct_references': context.get('direct_references', [])[:3],
                    'recent_decisions': context.get('recent_decisions', [])[:3],
                    'success_patterns': context.get('success_patterns', [])[:2]
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Display results
            self._display_analysis_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            console.print(f"[red]Analysis error: {e}[/red]")
            return {'error': str(e)}
    
    async def validate_project_quality(self, component: str = "all") -> Dict[str, Any]:
        """Run quality gates validation"""
        try:
            console.print(f"[blue]Running quality validation: {component}[/blue]")
            
            results = {}
            
            if component in ["all", "prd"]:
                # Look for PRD files
                prd_files = list(self.project_path.glob("*_PRD.md"))
                if prd_files:
                    prd_content = prd_files[0].read_text()
                    prd_result = await self.quality_gates.validate_prd_completeness(prd_content)
                    results['prd'] = prd_result
                else:
                    console.print("[yellow]No PRD files found[/yellow]")
            
            if component in ["all", "tasks"]:
                # Look for task files
                task_files = list(self.project_path.glob("*_Tasks.md"))
                if task_files:
                    # Parse tasks (simplified)
                    tasks = [{'id': 'task1', 'title': 'Sample task'}]  # Would parse actual tasks
                    prd_content = prd_files[0].read_text() if prd_files else ""
                    task_result = await self.quality_gates.validate_task_breakdown(tasks, prd_content)
                    results['tasks'] = task_result
                else:
                    console.print("[yellow]No task files found[/yellow]")
            
            # Display validation results
            self._display_validation_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            console.print(f"[red]Validation error: {e}[/red]")
            return {'error': str(e)}
    
    async def chat_with_memory(self, message: str) -> Dict[str, Any]:
        """Process conversational request with full memory context"""
        try:
            console.print(f"[blue]Processing chat message with memory...[/blue]")
            
            # Process request through conversation manager
            claude_request = await self.conversation_manager.process_user_request(message)
            
            console.print("[green]✓ Memory context injected[/green]")
            console.print(f"[dim]Context size: {len(str(claude_request['project_context']))} characters[/dim]")
            
            # In a real implementation, this would send to Claude Code
            # For now, we'll simulate a response
            simulated_response = f"Based on the memory context, here's my analysis of: {message}"
            
            # Process the simulated response
            learning_result = await self.conversation_manager.process_ai_response(
                simulated_response, message, "simulated"
            )
            
            return {
                'user_message': message,
                'system_prompt_length': len(claude_request['system_prompt']),
                'memory_context_included': True,
                'learning_completed': learning_result.get('learning_complete', False),
                'decisions_extracted': learning_result.get('decisions_extracted', 0)
            }
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            console.print(f"[red]Chat error: {e}[/red]")
            return {'error': str(e)}
    
    async def get_project_status(self) -> Dict[str, Any]:
        """Get comprehensive project status with memory insights"""
        try:
            # Get memory context
            memory_context = await self.memory_bank.get_relevant_context("project status")
            
            # Get quality assessment
            project_state = {'phase': 'analysis'}  # Would be determined from project files
            success_probability = await self.quality_gates.calculate_success_probability(project_state)
            
            # Get conversation context
            conv_context = await self.conversation_manager.get_conversation_context()
            
            status = {
                'project_path': str(self.project_path),
                'memory_bank_initialized': (self.project_path / "memory_bank").exists(),
                'decisions_count': len(memory_context.decision_history),
                'success_probability': f"{success_probability:.1%}",
                'conversation_count': len(conv_context.get('recent_conversations', [])),
                'last_activity': datetime.now().isoformat(),
                'performance_metrics': self._get_performance_metrics()
            }
            
            self._display_project_status(status)
            
            return status
            
        except Exception as e:
            logger.error(f"Status retrieval failed: {e}")
            console.print(f"[red]Status error: {e}[/red]")
            return {'error': str(e)}
    
    def _display_analysis_results(self, results: Dict[str, Any]):
        """Display analysis results in formatted output"""
        table = Table(title="Memory Analysis Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Context Found", "Yes" if results['context_found'] else "No")
        table.add_row("Suggestions", str(results['suggestions_count']))
        table.add_row("Risk Factors", str(results['risk_factors']))
        
        console.print(table)
        
        if results['memory_insights']['direct_references']:
            console.print("\n[bold]Direct References:[/bold]")
            for ref in results['memory_insights']['direct_references']:
                console.print(f"  • {ref[:100]}...")
    
    def _display_validation_results(self, results: Dict[str, Any]):
        """Display quality validation results"""
        for component, result in results.items():
            if hasattr(result, 'result'):
                color = {
                    ValidationResult.PASS: "green",
                    ValidationResult.WARNING: "yellow", 
                    ValidationResult.FAIL: "red",
                    ValidationResult.BLOCKED: "bright_red"
                }.get(result.result, "white")
                
                panel = Panel(
                    f"Score: {result.score:.1f}/100\n"
                    f"Issues: {len(result.issues)}\n"
                    f"Suggestions: {len(result.suggestions)}",
                    title=f"{component.upper()} Validation - {result.result.value.upper()}",
                    border_style=color
                )
                console.print(panel)
    
    def _display_project_status(self, status: Dict[str, Any]):
        """Display project status"""
        table = Table(title="Project Status")
        table.add_column("Aspect", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("Memory Bank", "Initialized" if status['memory_bank_initialized'] else "Not Found")
        table.add_row("Decisions Stored", str(status['decisions_count']))
        table.add_row("Success Probability", status['success_probability'])
        table.add_row("Conversations", str(status['conversation_count']))
        
        console.print(table)
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            return {
                'memory_operations': performance_monitor.get_metric_stats('memory_service'),
                'context_operations': performance_monitor.get_metric_stats('context_engine'),
                'quality_operations': performance_monitor.get_metric_stats('quality_gates')
            }
        except Exception:
            return {}

# CLI Commands
@app.command()
def init(project_path: Optional[str] = None):
    """Initialize AID Commander v4.0 in current or specified directory"""
    try:
        validate_configuration()
        path = project_path or str(Path.cwd())
        
        # Create .aid_commander config directory
        config_dir = Path.home() / ".aid_commander"
        config_dir.mkdir(exist_ok=True)
        
        console.print(f"[green]✓ AID Commander v4.0 initialized in {path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Initialization failed: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def start(project_name: str, approach: str = "single_prd", memory: bool = True):
    """Start a new project with memory integration"""
    async def _start():
        aid = AIDCommanderV4()
        await aid.start_project(project_name, approach, memory)
    
    asyncio.run(_start())

@app.command()
def analyze(query: str, project_path: Optional[str] = None):
    """Analyze query using memory bank intelligence"""
    async def _analyze():
        aid = AIDCommanderV4(project_path)
        await aid.analyze_with_memory(query)
    
    asyncio.run(_analyze())

@app.command()
def validate(component: str = "all", project_path: Optional[str] = None):
    """Run quality gates validation"""
    async def _validate():
        aid = AIDCommanderV4(project_path)
        await aid.validate_project_quality(component)
    
    asyncio.run(_validate())

@app.command()
def chat(message: str, project_path: Optional[str] = None):
    """Chat with memory-enhanced AI"""
    async def _chat():
        aid = AIDCommanderV4(project_path)
        result = await aid.chat_with_memory(message)
        
        if 'error' not in result:
            console.print(f"[green]✓ Processed with memory context[/green]")
            console.print(f"[dim]System prompt: {result['system_prompt_length']} chars[/dim]")
        
    asyncio.run(_chat())

@app.command()
def status(project_path: Optional[str] = None):
    """Get comprehensive project status"""
    async def _status():
        aid = AIDCommanderV4(project_path)
        await aid.get_project_status()
    
    asyncio.run(_status())

@app.command()
def memory_query(query: str, project_path: Optional[str] = None):
    """Query memory bank directly"""
    async def _memory_query():
        aid = AIDCommanderV4(project_path)
        context = await aid.memory_bank.get_relevant_context(query)
        
        console.print(Panel(
            context.format_for_ai() or "No relevant context found",
            title=f"Memory Query: {query}"
        ))
    
    asyncio.run(_memory_query())

@app.command()
def store_decision(title: str, context: str, chosen_option: str, 
                  rationale: str, project_path: Optional[str] = None):
    """Store a decision in memory bank"""
    async def _store():
        aid = AIDCommanderV4(project_path)
        
        decision = {
            'title': title,
            'context': context,
            'options': [],
            'chosen_option': chosen_option,
            'rationale': rationale,
            'decision_maker': 'User'
        }
        
        decision_id = await aid.memory_bank.store_decision(decision)
        console.print(f"[green]✓ Decision stored: {decision_id}[/green]")
    
    asyncio.run(_store())

@app.command()
def version():
    """Show AID Commander version and system info"""
    settings = get_settings()
    
    info_table = Table(title="AID Commander v4.0")
    info_table.add_column("Component", style="cyan")
    info_table.add_column("Status", style="green")
    
    info_table.add_row("Version", settings['AID_COMMANDER_VERSION'])
    info_table.add_row("Mode", settings['AID_COMMANDER_MODE'])
    info_table.add_row("Memory Bank", "Enabled" if settings['MEMORY_BANK_ENABLED'] else "Disabled")
    info_table.add_row("Quality Gates", "Enabled" if settings['QUALITY_GATES_ENABLED'] else "Disabled")
    info_table.add_row("Performance Monitoring", "Enabled" if settings['PERFORMANCE_MONITORING'] else "Disabled")
    
    console.print(info_table)

def main():
    """Main entry point"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()