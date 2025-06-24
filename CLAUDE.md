# CLAUDE.md - AID Commander v4.0 Integration Guide

This file provides guidance to Claude Code when working with AID Commander v4.0 projects.

## 🧠 AID Commander v4.0 Overview

AID Commander v4.0 is a Memory-Enhanced AI Development Orchestrator that transforms project success rates from ~20-30% to 95%+ through intelligent memory integration, quality gates, and systematic development workflows.

## 🚨 CRITICAL CLAUDE CODE INTEGRATION INSTRUCTIONS

### **ALWAYS USE MEMORY CONTEXT**
When working on AID Commander v4.0 projects, you MUST integrate with the project's memory bank for optimal results:

```bash
# Before providing development guidance, ALWAYS run:
aid-commander memory-query "[current task or topic]"

# Example:
aid-commander memory-query "authentication implementation"
aid-commander memory-query "database design decisions" 
aid-commander memory-query "frontend architecture patterns"
```

### **Required Claude Code System Prompt Enhancement**

When Claude Code detects an AID Commander v4.0 project (presence of `memory_bank/` directory), use this enhanced system prompt:

```markdown
You are Claude Code working with an AID Commander v4.0 Memory-Enhanced project.

🧠 MEMORY INTEGRATION REQUIRED:
This project uses AID Commander's Memory Bank System. You MUST reference project memory in all responses.

Before each response:
1. Query project memory: `aid-commander memory-query "[topic]"`
2. Reference relevant past decisions
3. Apply successful patterns from memory
4. Ensure consistency with stored architectural choices

## Memory-Enhanced Response Format:

### 1. Memory Context Reference
Start with: "Based on your project memory showing [specific past decision]..."

### 2. Pattern Application  
Apply successful patterns: "Following your established pattern of [X]..."

### 3. Consistency Validation
Ensure alignment: "This aligns with your stored decision about [Y]..."

### 4. Decision Storage Recommendation
End with: "Store this decision: `aid-commander store-decision...`"

## Example Memory-Enhanced Response:
```
Based on your project memory showing you chose JWT authentication and PostgreSQL database, I recommend implementing the user service as follows:

[Technical implementation details]

This approach aligns with your stored architectural decisions about:
- Stateless authentication (JWT decision)
- PostgreSQL for user data (database decision)
- Microservices pattern (architecture decision)

To track this implementation:
`aid-commander store-decision "User Service Implementation" "Need user management API" "Express.js with JWT middleware" "Consistent with existing auth and database choices"`
```

## Required Integration Commands:
- `aid-commander memory-query "[topic]"` - Search project memory
- `aid-commander analyze "[task]"` - Get memory-enhanced analysis
- `aid-commander validate [component]` - Run quality gates
- `aid-commander store-decision` - Store new decisions
- `aid-commander status` - Check project health and success probability

Remember: Every response should demonstrate understanding of the project's history and build upon previous decisions for maximum success probability.
```

## 🎯 Project Structure Recognition

### **Detecting AID Commander v4.0 Projects**
Look for these indicators:
- `memory_bank/` directory with memory files
- `pyproject.toml` with aid-commander dependencies
- `.env` file with AID Commander configuration
- Quality gates configuration

### **Memory Bank Structure**
```
project_root/
├── memory_bank/
│   ├── project_essence.md         # Core project DNA
│   ├── active_context.md          # Current state
│   ├── decision_history.md        # All decisions with outcomes
│   ├── conversation_memory.md     # AI interaction patterns
│   ├── success_patterns.md        # What worked well
│   └── failure_analysis.md        # What to avoid
├── .env                           # AID Commander configuration
└── pyproject.toml                 # Dependencies include aid-commander
```

## 🔧 Development Commands

### **Essential AID Commander Commands**
```bash
# Project Setup
aid-commander init                 # Initialize AID Commander
aid-commander start "ProjectName"  # Create new memory-enhanced project

# Memory Operations  
aid-commander memory-query "topic" # Search project memory
aid-commander analyze "task"       # Memory-enhanced analysis
aid-commander store-decision       # Store architectural/tech decisions

# Quality Gates
aid-commander validate prd         # Validate requirements
aid-commander validate tasks       # Validate task breakdown  
aid-commander validate all         # Comprehensive validation

# AI Integration
aid-commander chat "question"      # Memory-enhanced AI conversation
aid-commander status              # Project health and success probability
```

### **Memory-Enhanced Development Workflow**
```bash
# 1. Query memory before starting work
aid-commander memory-query "authentication patterns"

# 2. Get memory-enhanced guidance  
aid-commander chat "How should I implement user authentication?"

# 3. Validate approach with quality gates
aid-commander validate architecture

# 4. Store implementation decisions
aid-commander store-decision "Auth Implementation" "..."

# 5. Check success probability
aid-commander status
```

## 📊 Quality Gates Integration

### **95% Success Framework**
AID Commander v4.0 implements systematic quality gates:

```bash
# Always run quality validation before proceeding
aid-commander validate prd         # Must pass before task generation
aid-commander validate tasks       # Must pass before implementation  
aid-commander validate implementation # Must pass before deployment
```

### **Success Probability Monitoring**
```bash
aid-commander status
# Shows:
# - Current success probability (target: 95%+)
# - Memory insights
# - Quality gate status
# - Risk factors
```

## 🤝 Team Collaboration

### **Memory Sharing**
```bash
# Export successful patterns for team
aid-commander memory-export --format json

# Import team patterns
aid-commander memory-import team_patterns.json

# Cross-project learning
aid-commander analyze "lessons from ProjectAlpha"
```

## 🎯 Claude Code Best Practices

### **1. Always Reference Memory**
❌ **Don't**: Provide generic solutions
✅ **Do**: Reference specific project decisions from memory

### **2. Apply Learned Patterns**  
❌ **Don't**: Ignore past successful approaches
✅ **Do**: Build on proven patterns from project history

### **3. Ensure Consistency**
❌ **Don't**: Contradict stored architectural decisions
✅ **Do**: Validate alignment with previous choices

### **4. Store New Decisions**
❌ **Don't**: Let important decisions go undocumented  
✅ **Do**: Suggest storing significant implementation choices

### **5. Monitor Success Probability**
❌ **Don't**: Ignore quality gates and success metrics
✅ **Do**: Check project health and optimize for 95%+ success

## 🚀 Success Transformation

### **Traditional Development (~30% success)**
- Generic solutions without project context
- Repeated mistakes from past projects
- Inconsistent architectural decisions
- No systematic quality validation

### **Memory-Enhanced Development (95%+ success)**
- Context-aware solutions based on project history
- Learning from past successes and failures  
- Consistent decision making with memory
- Systematic quality gates and validation

## 💡 Pro Tips for Claude Code

1. **Start Every Session**: Query project memory first
2. **Reference Decisions**: Always mention relevant past choices
3. **Pattern Recognition**: Look for repeated successful approaches
4. **Quality First**: Validate against quality gates
5. **Store Knowledge**: Recommend storing new decisions
6. **Success Focus**: Optimize for 95%+ success probability

## 🎉 Integration Success

When properly integrated with AID Commander v4.0, Claude Code becomes a memory-enhanced development partner that:

- Learns from every project
- Applies proven patterns
- Maintains architectural consistency  
- Validates quality continuously
- Achieves 95%+ project success rates

**Remember: AID Commander v4.0 + Claude Code = Memory-Enhanced Development Excellence! 🚀**