# File: app/models/creator.py (updated)
# Path: fanfix-api/app/models/creator.py

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid

# Creator Models
class CreatorBase(BaseModel):
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    active: bool = True

class CreatorCreate(CreatorBase):
    pass

class CreatorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    active: Optional[bool] = None

class CreatorRead(CreatorBase):
    id: uuid.UUID
    created_at: datetime
    style: Optional['CreatorStyleRead'] = None
    examples: Optional[List['StyleExampleRead']] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Creator Style Models
class CreatorStyleBase(BaseModel):
    approved_emojis: List[str] = Field(default_factory=list)
    case_style: Optional[str] = None
    text_replacements: Optional[Dict[str, str]] = None
    sentence_separators: List[str] = Field(default_factory=list)
    punctuation_rules: Optional[Dict[str, bool]] = None
    abbreviations: Optional[Dict[str, str]] = None
    message_length_preference: Optional[str] = None
    style_instructions: Optional[str] = None
    tone_range: Optional[str] = None

class CreatorStyleCreate(CreatorStyleBase):
    pass

class CreatorStyleUpdate(CreatorStyleBase):
    pass

class CreatorStyleRead(CreatorStyleBase):
    creator_id: uuid.UUID

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Style Example Models
class StyleExampleBase(BaseModel):
    fan_message: str
    creator_responses: List[str]

class StyleExampleCreate(StyleExampleBase):
    pass

class StyleExampleRead(StyleExampleBase):
    id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Circular reference resolution
CreatorRead.update_forward_refs()