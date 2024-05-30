import enum

import praw
import os
from dotenv import load_dotenv
from dataclasses import dataclass


@dataclass
class RedditPost:
    id: str
    author_id: str
    created_utc: int
    name: str
    permalink: str
    score: int
    selftext: str
    subreddit: str
    title: str
    upvote_ratio: float
    cleaned_selftext: str = None
    cleaned_title: str = None


class TimeFilter(enum.Enum):
    ALL = "all"
    DAY = "day"
    HOUR = "hour"
    MONTH = "month"
    WEEK = "week"
    YEAR = "year"


class Reddit:
    def __init__(self):
        load_dotenv(".env")
        self.reddit: praw.Reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            password=os.getenv("PASSWORD"),
            user_agent="Comment Extraction (by u/" + os.getenv("USERNAME") + ")",
            username=os.getenv("USERNAME"),
        )

    def get_hot_posts(self, subreddit, limit=10) -> list[RedditPost]:
        posts: list[RedditPost] = []
        for submission in self.reddit.subreddit(subreddit).hot(limit=limit):
            try:
                post = RedditPost(
                    id=submission.id,
                    author_id=submission.author.id,
                    created_utc=submission.created_utc,
                    name=submission.name,
                    permalink=submission.permalink,
                    score=submission.score,
                    selftext=submission.selftext,
                    subreddit=submission.subreddit.display_name,
                    title=submission.title,
                    upvote_ratio=submission.upvote_ratio
                )
                posts.append(post)
            except Exception as e:
                print(e)

        return posts

    def get_top_posts(self, subreddit, time_filter: TimeFilter = TimeFilter.ALL, limit=10) -> list[RedditPost]:
        posts: list[RedditPost] = []
        for submission in self.reddit.subreddit(subreddit).top(time_filter=time_filter.value, limit=limit):
            try:
                post = RedditPost(
                    id=submission.id,
                    author_id=submission.author.id,
                    created_utc=submission.created_utc,
                    name=submission.name,
                    permalink=submission.permalink,
                    score=submission.score,
                    selftext=submission.selftext,
                    subreddit=submission.subreddit.display_name,
                    title=submission.title,
                    upvote_ratio=submission.upvote_ratio
                )
                posts.append(post)
            except Exception as e:
                print(e)

        return posts

    def get_new_posts(self, subreddit, limit=10) -> list[RedditPost]:
        posts: list[RedditPost] = []
        for submission in self.reddit.subreddit(subreddit).new(limit=limit):
            try:
                post = RedditPost(
                    id=submission.id,
                    author_id=submission.author.id,
                    created_utc=submission.created_utc,
                    name=submission.name,
                    permalink=submission.permalink,
                    score=submission.score,
                    selftext=submission.selftext,
                    subreddit=submission.subreddit.display_name,
                    title=submission.title,
                    upvote_ratio=submission.upvote_ratio
                )
                posts.append(post)
            except Exception as e:
                print(e)

        return posts
