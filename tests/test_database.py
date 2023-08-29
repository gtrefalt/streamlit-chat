import pytest
from sqlmodel import create_engine, Session, Field, SQLModel, func
import datetime
from loguru import logger

# Model definitions (from the refactored code)


class Conversation(SQLModel, table=True):
    id: str = Field(primary_key=True)
    conversation_name: str
    model: str
    messages: dict
    system_msg: str
    total_tokens: dict
    total_price: float
    user_name: str
    datetime_utc: datetime.datetime = Field(default=datetime.datetime.utcnow)
    datetime_updated: datetime.datetime


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_name: str
    user_email: str
    credit_used: float = Field(default=0.0)
    total_credit: float


# Testing setup using :memory:
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="function", autouse=True)
def create_test_tables():
    SQLModel.metadata.create_all(test_engine)


@pytest.fixture
def session():
    with Session(test_engine) as session:
        yield session
        session.rollback()


# Test functions


def test_create_new_user(session):
    user_name = "testuser"
    user_email = "testuser@example.com"
    total_credit = 100.0

    create_new_user(user_name, user_email, total_credit)

    user = session.query(User).filter_by(user_email=user_email).first()
    assert user is not None
    assert user.user_name == user_name
    assert user.total_credit == total_credit


def test_create_new_conversation(session):
    conversation_id = "test123"
    conversation_name = "test conversation"
    model_name = "test model"
    messages = {"message": "hello"}
    system_msg = "system message"
    total_tokens = {"tokens": 5}
    total_price = 5.0
    user_name = "testuser"

    create_new_conversation(
        conversation_id,
        conversation_name,
        model_name,
        messages,
        system_msg,
        total_tokens,
        total_price,
        user_name,
    )

    conversation = session.query(Conversation).get(conversation_id)
    assert conversation is not None
    assert conversation.conversation_name == conversation_name
    assert conversation.model == model_name


def test_update_conversation(session):
    conversation_id = "test123"
    messages = {"message": "updated hello"}
    total_tokens = {"tokens": 10}
    total_price = 10.0

    update_conversation(conversation_id, messages, total_tokens, total_price)

    conversation = session.query(Conversation).get(conversation_id)
    assert conversation.messages == messages
    assert conversation.total_tokens == total_tokens
    assert conversation.total_price == total_price


def test_get_user_credit_used(session):
    user_name = "testuser"
    credit_used = get_user_credit_used(user_name)

    # Assuming the user was created in a previous test and has a conversation
    # Therefore, total credit used should be 10.0 (from the previous test)
    assert credit_used == 10.0
