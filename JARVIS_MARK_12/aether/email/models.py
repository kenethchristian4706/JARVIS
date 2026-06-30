from pydantic import BaseModel
from typing import List, Optional

class ConnectRequest(BaseModel):
    email: str
    password: str

class EmailSummary(BaseModel):
    id: str
    sender: str
    subject: str
    date: str
    unread: bool
    has_attachments: bool

class EmailDetails(BaseModel):
    id: str
    sender: str
    recipients: List[str]
    subject: str
    date: str
    body: str
    attachments: List[str]
