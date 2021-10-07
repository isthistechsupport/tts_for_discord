from datetime import datetime
from sqlalchemy.sql.expression import insert
from dbschema import link_history
from sqlalchemy import select
import praw


def init_reddit(setup):
    return praw.Reddit(user_agent='tts_for_discord', client_id=setup['reddit']['id'], client_secret=setup['reddit']['secret'])


def get_subreddit(subreddit: str, setup):
    return init_reddit(setup).subreddit(subreddit)


def check_duplicate(id: str, server_id: int, dupes_allowed: bool, engine):
    with engine.begin() as conn:
        result = conn.execute(
            select(link_history).filter_by(reddit_id = id, server_id = server_id)
        ).all()
        if not dupes_allowed:
            return len(result) > 0
        else:
            return False


def get_post(subreddit: str, server: str, server_id: int, channel: str, channel_id: int, username: str, username_id: int, dupe: bool, engine, setup):
    for submission in get_subreddit(subreddit, setup).hot(limit=25):
        if not check_duplicate(submission.id, server, dupe, engine):
            with engine.begin() as conn:
                conn.execute(
                    insert(link_history).values(server=server, server_id=server_id, channel=channel, channel_id=channel_id, username=username, username_id=username_id, datetime_sent=datetime.now(), subreddit=subreddit, link=submission.url, reddit_id=submission.id)
                )
            return submission 

