# 🔧 IDE Integration Guide - AID Commander v4.0

## Overview

This guide shows how to integrate AID Commander v4.0's Memory Bank System with popular IDEs and AI coding assistants for memory-enhanced development.

## 🎯 Core Integration Principle

**Every AI interaction should include project memory context for optimal results.**

## 🚀 Quick Integration

### **Universal IDE Integration Script**

Create this script in your project root as `aide_integration.sh`:

```bash
#!/bin/bash
# AID Commander v4.0 IDE Integration Script

# Function to get memory context for current task
get_memory_context() {
    local task="$1"
    if [ -z "$task" ]; then
        task="current development"
    fi
    
    echo "=== AID COMMANDER MEMORY CONTEXT ==="
    aid-commander memory-query "$task" 2>/dev/null || echo "No memory context available"
    echo "=== END MEMORY CONTEXT ==="
    echo ""
}

# Function to enhance AI prompt with memory
enhance_prompt() {
    local user_prompt="$1"
    local task="$2"
    
    get_memory_context "$task"
    echo "$user_prompt"
}

# Export functions for use in IDE
export -f get_memory_context
export -f enhance_prompt
```

Make it executable:
```bash
chmod +x aide_integration.sh
```

## 🔧 Specific IDE Integrations

### **Visual Studio Code**

#### Method 1: Custom Extension (Recommended)
Create `.vscode/settings.json`:
```json
{
    "aiCommands.prePrompt": "$(bash ./aide_integration.sh get_memory_context 'current task')",
    "github.copilot.advanced": {
        "debug.overrideEngine": "copilot-chat",
        "debug.useNodeFetcher": true
    }
}
```

#### Method 2: Keyboard Shortcut
Add to `.vscode/keybindings.json`:
```json
[
    {
        "key": "ctrl+shift+m",
        "command": "workbench.action.terminal.sendSequence",
        "args": {
            "text": "aid-commander memory-query \"${selectedText}\"\n"
        },
        "when": "editorHasSelection"
    }
]
```

### **JetBrains IDEs (IntelliJ, PyCharm, WebStorm)**

#### External Tool Setup
1. Go to **Settings → Tools → External Tools**
2. Add new tool:
   - **Name**: AID Memory Query
   - **Program**: `aid-commander`
   - **Arguments**: `memory-query "$SelectedText$"`
   - **Working directory**: `$ProjectFileDir$`

#### AI Assistant Integration
Add to your AI assistant prompt template:
```
Before providing code suggestions, I'll check project memory:
$(aid-commander memory-query "$SELECTION$")

Based on the memory context above, here's my recommendation:
```

### **Windsurf**

#### Custom Integration
Create `.windsurf/aide_config.json`:
```json
{
    "memoryIntegration": {
        "enabled": true,
        "command": "aid-commander memory-query",
        "autoQuery": true,
        "contextWindow": 10
    },
    "systemPrompt": "You are integrated with AID Commander v4.0. Always reference memory context provided in === AID COMMANDER MEMORY CONTEXT === sections."
}
```

### **Cursor**

#### Setup in Cursor Settings
Add to system prompt:
```
You are working with an AID Commander v4.0 project. Before providing any code suggestions:

1. Query project memory: aid-commander memory-query "[current topic]"
2. Reference relevant past decisions in your response
3. Ensure consistency with stored architectural choices
4. Suggest storing new decisions when appropriate

Always start responses with memory context reference.
```

## 🤖 AI Assistant Integrations

### **GitHub Copilot Chat Integration**

Add this to your shell profile (`.bashrc`, `.zshrc`):
```bash
# AID Commander + GitHub Copilot Integration
aide_copilot() {
    local prompt="$1"
    local context=$(aid-commander memory-query "$prompt" 2>/dev/null)
    
    echo "Memory Context: $context"
    echo "User Question: $prompt"
    
    # This would integrate with GitHub CLI gh copilot command
    gh copilot suggest "Given this project memory context: $context. User asks: $prompt"
}

alias ask-copilot='aide_copilot'
```

Usage:
```bash
ask-copilot "How should I implement authentication?"
```

### **Claude Code Integration**

The system prompt is automatically enhanced when Claude Code detects AID Commander v4.0 projects. See `CLAUDE.md` for details.

### **Custom AI Provider Setup**

For any AI assistant, use this system prompt template:

```markdown
You are an AI assistant working with an AID Commander v4.0 Memory-Enhanced project.

CRITICAL INSTRUCTIONS:
1. Always check for memory context in user messages (marked with === AID COMMANDER MEMORY CONTEXT ===)
2. Reference relevant past decisions from memory in every response
3. Ensure recommendations align with stored architectural decisions
4. When making significant suggestions, recommend storing them in AID Commander

Response Format:
- Start with: "Based on your project memory showing [specific decision]..."
- Provide technical guidance
- End with: "Store this decision: aid-commander store-decision..."

Integration Commands:
- aid-commander memory-query "[topic]" - Search memory
- aid-commander analyze "[task]" - Get analysis
- aid-commander store-decision - Store decisions
- aid-commander validate - Run quality gates
```

## ⚡ Advanced Integrations

### **Terminal Integration**

Add to your shell profile:
```bash
# AID Commander v4.0 Terminal Integration

# Smart memory query with context
amq() {
    local query="$*"
    if [ -z "$query" ]; then
        echo "Usage: amq <search terms>"
        return 1
    fi
    
    echo "🧠 Searching project memory for: $query"
    aid-commander memory-query "$query"
}

# Enhanced AI chat with automatic memory context
achat() {
    local question="$*"
    if [ -z "$question" ]; then
        echo "Usage: achat <your question>"
        return 1
    fi
    
    echo "🤖 Getting memory-enhanced AI response..."
    aid-commander chat "$question"
}

# Quick decision storage
astore() {
    echo "📝 Storing decision in project memory..."
    aid-commander store-decision "$@"
}

# Project status with memory insights
astatus() {
    echo "📊 Project status with memory insights:"
    aid-commander status
}

# Quality validation
avalidate() {
    echo "✅ Running quality gates validation:"
    aid-commander validate "${1:-all}"
}
```

### **Git Hooks Integration**

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# AID Commander v4.0 Git Integration

echo "🔍 Running AID Commander quality gates..."

# Validate current state before commit
if ! aid-commander validate all --quiet; then
    echo "❌ Quality gates failed. Commit blocked."
    echo "Run 'aid-commander validate all' for details."
    exit 1
fi

echo "✅ Quality gates passed. Proceeding with commit."

# Store commit as decision if significant
if [ -n "$AID_STORE_COMMITS" ]; then
    COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || echo "Current changes")
    aid-commander store-decision \
        "Code Commit" \
        "Committing code changes" \
        "$(echo "$COMMIT_MSG" | head -1)" \
        "Code changes ready for commit after quality validation" \
        --quiet
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## 📱 Mobile Development Integration

### **Xcode (iOS)**

Create custom script in Xcode:
1. **Product → Scheme → Edit Scheme**
2. **Build → Pre-actions**
3. Add script:
```bash
aid-commander memory-query "iOS development patterns" > /tmp/aide_context.txt
echo "Memory context saved to /tmp/aide_context.txt"
```

### **Android Studio**

Add Gradle task in `build.gradle`:
```gradle
task aideMemoryQuery {
    doLast {
        exec {
            commandLine 'aid-commander', 'memory-query', 'Android development'
        }
    }
}

// Run before build
preBuild.dependsOn aideMemoryQuery
```

## 🎯 Best Practices

### **1. Automatic Memory Querying**
Set up your IDE to automatically query memory when:
- Opening a new file
- Starting to type in certain contexts
- Before running AI assistants

### **2. Context-Aware Queries**
Query memory with specific context:
```bash
# Generic (less useful)
aid-commander memory-query "database"

# Specific (more useful)  
aid-commander memory-query "user authentication database design"
```

### **3. Store Important Decisions**
Configure your IDE to prompt for decision storage after:
- Architectural changes
- Technology choices
- Design pattern implementations

### **4. Quality Gate Integration**
Run quality gates:
- Before commits (git hooks)
- During CI/CD (automated)
- Before code reviews (manual)

## 🚀 Integration Validation

Test your integration with:

```bash
# 1. Test memory query
aid-commander memory-query "test integration"

# 2. Test enhanced AI chat
aid-commander chat "How should I structure my project based on memory?"

# 3. Test quality gates
aid-commander validate all

# 4. Test decision storage
aid-commander store-decision "Integration Test" "Testing IDE integration" "Setup complete" "Integration working properly"

# 5. Check project status
aid-commander status
```

## ✅ Integration Success Checklist

- [ ] Memory queries work from IDE
- [ ] AI assistants reference project memory
- [ ] Quality gates run automatically
- [ ] Decisions stored easily
- [ ] Project status visible
- [ ] Team patterns shared
- [ ] Success probability tracked

## 🎉 Benefits of Full Integration

With proper IDE integration, you get:

- **Memory-Enhanced Coding**: Every AI suggestion includes project history
- **Consistent Architecture**: Recommendations align with past decisions
- **Quality Assurance**: Automatic validation prevents issues
- **Team Learning**: Shared patterns across development team
- **Success Optimization**: 95%+ project success rates

**Your IDE becomes a memory-enhanced development partner! 🧠💻**