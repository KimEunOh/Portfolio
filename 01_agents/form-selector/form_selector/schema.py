from pydantic import BaseModel
from typing import List, Dict, Optional


class UserInput(BaseModel):
    input: str


class FormSelectorOutput(BaseModel):
    form_type: str
    keywords: List[str]
    slots: Optional[Dict[str, str]] = None
