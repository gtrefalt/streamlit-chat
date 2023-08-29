from loguru import logger
from sqlmodel import SQLModel, Field, Session, create_engine
from typing import Optional
from sqlalchemy import func, Column, JSON
import datetime
import streamlit as st
import yaml
from yaml.loader import SafeLoader


# Models
class Conversation(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: str = Field(primary_key=True)
    conversation_name: str
    model: str
    messages: dict = Field(default={}, sa_column=Column(JSON))
    system_msg: Optional[str]
    total_tokens: dict = Field(default={}, sa_column=Column(JSON))
    total_price: float
    user_name: str
    datetime_utc: datetime.datetime = Field(default=datetime.datetime.utcnow())
    datetime_updated: datetime.datetime


class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int = Field(primary_key=True)
    user_name: str
    user_email: str
    credit_used: float = Field(default=0.0)
    total_credit: float = Field(default=0.0)


# Engine and Session setup
# create user table in db
# load config
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

database_file = config["database"]["database_file"]


@st.cache_resource
def init_database(database_file):
    engine = create_engine(f"sqlite:///{database_file}")
    SQLModel.metadata.create_all(engine)
    return engine


engine = init_database(database_file)


def create_new_user(
    user_name: str,
    user_email: str,
    total_credit: float = None,
):
    with Session(engine) as session:
        existing_user = session.get(User, user_email)
        if existing_user is not None:
            logger.warning(f"A user with the email {user_email} already exists.")
            return

        new_user = User(
            user_name=user_name,
            user_email=user_email,
            total_credit=total_credit,
        )

        session.add(new_user)
        session.commit()


def create_new_conversation(
    conversation_id: str,
    conversation_name: str,
    model_name: str,
    messages: dict,
    system_msg: str,
    total_tokens: dict,
    total_price: float,
    user_name: str,
):
    with Session(engine) as session:
        new_conversation = Conversation(
            id=conversation_id,
            conversation_name=conversation_name,
            model=model_name,
            messages=messages,
            system_msg=system_msg,
            total_tokens=total_tokens,
            total_price=total_price,
            user_name=user_name,
            datetime_updated=datetime.datetime.utcnow(),
        )

        session.add(new_conversation)
        session.commit()


def update_conversation(
    conversation_id: str, messages: dict, total_tokens: dict, total_price: float
):
    with Session(engine) as session:
        conversation: Conversation = session.get(Conversation, conversation_id)
        if conversation:
            conversation.messages = messages
            conversation.total_tokens = total_tokens
            conversation.total_price = total_price
            conversation.datetime_updated = datetime.datetime.utcnow()
            session.commit()
        else:
            logger.error(f"No conversation found with this id: {conversation_id}")


def update_credit_used(user_name: str):
    with Session(engine) as session:
        total_price = (
            session.query(func.sum(Conversation.total_price))
            .filter(Conversation.user_name == user_name)
            .scalar()
        )
        if total_price is None:
            total_price = 0.0

        session.query(User).filter_by(user_name=user_name).update(
            {User.credit_used: total_price}
        )
        session.commit()


def get_user_credit_used(user_name: str) -> float:
    with Session(engine) as session:
        user = session.query(User).filter_by(user_name=user_name).first()
        if user is not None:
            return user.credit_used
        else:
            logger.error(f"No user found with the username: {user_name}")
            return 0.0


def get_user_conversations(user_name: str, limit: int = 10) -> list:
    with Session(engine) as session:
        conversations = (
            session.query(Conversation)
            .filter(Conversation.user_name == user_name)
            .order_by(Conversation.datetime_updated.desc())
            .limit(limit)
            .all()
        )
        return conversations


def get_conversation(conversation_id: str) -> Conversation:
    with Session(engine) as session:
        conversation = session.query(Conversation).get(conversation_id)
        if not conversation:
            logger.error(f"No conversation found with this id: {conversation_id}")
        return conversation
