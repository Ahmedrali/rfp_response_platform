"""
Base model class with common fields and functionality
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, func, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields for all tables"""
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name"""
        return cls.__name__.lower() + 's'

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of the model"""
        return f"<{self.__class__.__name__}(id={self.id})>"
