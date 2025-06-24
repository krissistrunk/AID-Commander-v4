#!/usr/bin/env python3
"""
Data validation utilities for AID Commander v4.0
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryEntryModel(BaseModel):
    """Pydantic model for memory entry validation"""
    id: str
    type: str
    content: str
    context: Optional[str] = None
    timestamp: datetime
    relevance_score: float = 0.0
    tags: Optional[str] = None
    
    @validator('relevance_score')
    def validate_relevance_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Relevance score must be between 0.0 and 1.0')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['decision', 'conversation', 'pattern', 'context', 'task']
        if v not in valid_types:
            raise ValueError(f'Type must be one of {valid_types}')
        return v

class DecisionModel(BaseModel):
    """Pydantic model for decision validation"""
    title: str
    context: str
    options: List[Dict[str, Any]]
    chosen_option: str
    rationale: str
    decision_maker: Optional[str] = None
    stakeholder_signoff: Optional[str] = 'Pending'
    status: str = 'pending'
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'approved', 'implemented', 'failed']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v

def validate_memory_data(data: Dict[str, Any], data_type: str) -> bool:
    """Validate memory data using appropriate Pydantic model"""
    try:
        if data_type == 'memory_entry':
            MemoryEntryModel(**data)
        elif data_type == 'decision':
            DecisionModel(**data)
        else:
            logger.warning(f"Unknown data type for validation: {data_type}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Validation failed for {data_type}: {e}")
        return False

def validate_json_structure(json_data: str, required_fields: List[str]) -> bool:
    """Validate JSON structure has required fields"""
    try:
        data = json.loads(json_data)
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return False

def sanitize_input(input_data: str, max_length: int = 10000) -> str:
    """Sanitize input data for security"""
    # Remove potentially dangerous characters
    dangerous_chars = ['<script>', '</script>', 'javascript:', 'data:']
    
    sanitized = input_data
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    return sanitized.strip()