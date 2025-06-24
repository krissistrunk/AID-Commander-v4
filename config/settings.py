#!/usr/bin/env python3
"""
Configuration Management for AID Commander v4.0
Centralized settings with environment variable support and validation
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_settings() -> Dict[str, Any]:
    """Get all configuration settings with environment variable overrides"""
    return {
        # Core Settings
        'AID_COMMANDER_VERSION': os.getenv('AID_COMMANDER_VERSION', '4.0.0'),
        'AID_COMMANDER_MODE': os.getenv('AID_COMMANDER_MODE', 'hybrid'),
        'AID_LOG_LEVEL': os.getenv('AID_LOG_LEVEL', 'INFO'),
        'AID_DATA_DIR': Path(os.getenv('AID_DATA_DIR', '~/.aid_commander')).expanduser(),
        
        # Memory Bank Settings
        'MEMORY_BANK_ENABLED': os.getenv('MEMORY_BANK_ENABLED', 'true').lower() == 'true',
        'MEMORY_BANK_MAX_SIZE_MB': int(os.getenv('MEMORY_BANK_MAX_SIZE_MB', '1000')),
        'MEMORY_BANK_ENCRYPTION': os.getenv('MEMORY_BANK_ENCRYPTION', 'true').lower() == 'true',
        'MEMORY_SEARCH_ENGINE': os.getenv('MEMORY_SEARCH_ENGINE', 'sqlite_fts'),
        'MEMORY_CACHE_TTL': int(os.getenv('MEMORY_CACHE_TTL', '3600')),
        
        # AI Provider Settings
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'AZURE_COGNITIVE_KEY': os.getenv('AZURE_COGNITIVE_KEY'),
        'AI_DEFAULT_PROVIDER': os.getenv('AI_DEFAULT_PROVIDER', 'openai'),
        'AI_CONFIDENCE_THRESHOLD': int(os.getenv('AI_CONFIDENCE_THRESHOLD', '85')),
        'AI_CONTEXT_MAX_TOKENS': int(os.getenv('AI_CONTEXT_MAX_TOKENS', '8000')),
        
        # Quality Gates Settings
        'QUALITY_GATES_ENABLED': os.getenv('QUALITY_GATES_ENABLED', 'true').lower() == 'true',
        'QUALITY_GATES_STRICT_MODE': os.getenv('QUALITY_GATES_STRICT_MODE', 'false').lower() == 'true',
        'QUALITY_GATES_AUTO_FIX': os.getenv('QUALITY_GATES_AUTO_FIX', 'true').lower() == 'true',
        'QUALITY_SUCCESS_THRESHOLD': int(os.getenv('QUALITY_SUCCESS_THRESHOLD', '95')),
        
        # Performance Settings
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'ELASTICSEARCH_URL': os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///~/.aid_commander/aid_commander.db'),
        
        # Security Settings
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'ENCRYPT_MEMORY_BANK': os.getenv('ENCRYPT_MEMORY_BANK', 'true').lower() == 'true',
        'API_RATE_LIMIT': int(os.getenv('API_RATE_LIMIT', '100')),
        
        # Development Settings
        'DEBUG_MODE': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
        'PERFORMANCE_MONITORING': os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true',
        'TELEMETRY_ENABLED': os.getenv('TELEMETRY_ENABLED', 'true').lower() == 'true',
    }

def validate_configuration() -> bool:
    """Validate required configuration is present"""
    settings = get_settings()
    required_settings = ['SECRET_KEY']
    
    missing = [key for key in required_settings if not settings.get(key)]
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")
    
    return True

def get_ai_provider_config(provider: str) -> Dict[str, Any]:
    """Get configuration for specific AI provider"""
    settings = get_settings()
    
    configs = {
        'openai': {
            'api_key': settings['OPENAI_API_KEY'],
            'model': 'gpt-4',
            'max_tokens': settings['AI_CONTEXT_MAX_TOKENS'],
            'temperature': 0.7
        },
        'anthropic': {
            'api_key': settings['ANTHROPIC_API_KEY'],
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': settings['AI_CONTEXT_MAX_TOKENS'],
            'temperature': 0.7
        },
        'azure': {
            'api_key': settings['AZURE_COGNITIVE_KEY'],
            'endpoint': os.getenv('AZURE_COGNITIVE_ENDPOINT'),
            'deployment_name': os.getenv('AZURE_DEPLOYMENT_NAME')
        }
    }
    
    return configs.get(provider, {})