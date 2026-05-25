from enum import Enum

from pydantic import BaseModel


class Category(str, Enum):
    FAQ = "faq"
    MEDICAL = "medical"
    BUSINESS = "business"
    ORDER = "order"
    SPAM = "spam"


class Priority(str, Enum):
    P1_URGENT = "P1"
    P2_BUSINESS = "P2"
    P3_SUPPORT = "P3"
    P4_FAQ = "P4"
    P5_SPAM = "P5"


class Language(str, Enum):
    HR = "hr"
    EN = "en"
    OTHER = "other"


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    language: Language
    summary: str
    requires_human: bool
    suggested_action: str
    auto_reply: str | None = None
