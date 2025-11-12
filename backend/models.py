# models.py
import uuid
from sqlalchemy import (
    Column, String, Integer, Date, DECIMAL, Text, Enum, CHAR, TIMESTAMP, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

def gen_uuid():
    return str(uuid.uuid4())

import uuid
from sqlalchemy import (
    Column, String, Integer, Date, DECIMAL, Text, Enum, CHAR, TIMESTAMP, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

def gen_uuid():
    return str(uuid.uuid4())

class Customer(Base):
    __tablename__ = "customers"
    id = Column(CHAR(36), primary_key=True, default=gen_uuid)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone_number = Column(String(30))
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    customer_identification = Column(String(100))
    total_spending = Column(DECIMAL(13,2), default=0.00)
    rough_monthly_income = Column(DECIMAL(13,2))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="customer", cascade="all,delete")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

    transactions = relationship("Transaction", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(CHAR(36), nullable=False)
    date_of_purchase = Column(Date, nullable=False)
    item_description = Column(String(500))
    category_id = Column(Integer)
    amount = Column(DECIMAL(13,2), nullable=False)
    currency = Column(String(3), default="USD")
    source = Column(String(100))
    parsed_raw = Column(Text)
    category_source = Column(Enum('rule','ai','manual', name='category_src_enum'), default='rule')
    ai_confidence = Column(DECIMAL(4,3))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # relationships
    customer = relationship("Customer", back_populates="transactions", foreign_keys=[customer_id])
    category = relationship("Category", back_populates="transactions", foreign_keys=[category_id])
