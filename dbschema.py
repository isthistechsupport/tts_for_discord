from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, BLOB
from sqlalchemy.sql.schema import MetaData


metadata = MetaData()


files_table = Table(
    "attachments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("server", String),
    Column("server_id", Integer),
    Column("channel", String),
    Column("channel_id", Integer),
    Column("username", String),
    Column("username_id", Integer),
    Column("datetime_received", DateTime),
    Column("name", String),
    Column("file", BLOB)
)


link_history = Table(
    "links",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("server", String),
    Column("server_id", Integer),
    Column("channel", String),
    Column("channel_id", Integer),
    Column("username", String),
    Column("username_id", Integer),
    Column("datetime_sent", DateTime),
    Column("subreddit", String),
    Column("link", String),
    Column("reddit_id", String)
)


command_history = Table(
    "history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("server", String),
    Column("server_id", Integer),
    Column("channel", String),
    Column("channel_id", Integer),
    Column("username", String),
    Column("username_id", Integer),
    Column("datetime_sent", DateTime),
    Column("command_text", String)
)


def connect_db(filename: str):
    engine = create_engine(f"sqlite+pysqlite:///{filename}", echo=True, future=True)
    metadata.create_all(engine)
    return engine