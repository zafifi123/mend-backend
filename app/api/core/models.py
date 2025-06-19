from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, DECIMAL, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Watchlist(Base):
    __tablename__ = 'watchlist'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol = Column(String(10), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol = Column(String(10), nullable=False)
    action = Column(String(10), nullable=False)
    price = Column(DECIMAL(18, 4), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    executed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Recommendation(Base):
    __tablename__ = 'recommendations'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    recommendation = Column(String(10), nullable=False)
    confidence = Column(Integer, nullable=False)
    price = Column(String(20), nullable=False)
    change = Column(String(20), nullable=False)
    reasoning = Column(Text)
    risk = Column(String(20))
    timeframe = Column(String(50))
    sector = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MarketInsight(Base):
    __tablename__ = 'market_insights'
    id = Column(Integer, primary_key=True, index=True)
    sentiment = Column(String(20), nullable=False)
    top_sectors = Column(ARRAY(String(50)), nullable=False)
    volatility_alert = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrendingStock(Base):
    __tablename__ = 'trending_stocks'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TopMover(Base):
    __tablename__ = 'top_movers'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    change = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = Column(Text, nullable=False)
    is_user = Column(Boolean, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) 