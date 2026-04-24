# Import models here so SQLAlchemy's Base can discover them before creating tables.
# This is crucial for Base.metadata.create_all() to work properly.

from app.models.user import User
from app.models.policy import Policy
from app.models.chat import ChatSession

# Export all models for clean imports elsewhere in the project
__all__ = ["User", "Policy", "ChatSession"]