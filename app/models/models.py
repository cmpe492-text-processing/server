from app.main import db


class Corpus(db.Model):
    __tablename__ = 'corpuses'

    platform = db.Column(db.String(), primary_key=True)
    entry_id = db.Column(db.String(), primary_key=True)
    data = db.Column(db.JSON)

    def __init__(self, platform, entry_id, data):
        self.platform = platform
        self.entry_id = entry_id
        self.data = data

    @staticmethod
    def insert_corpuses(corpuses: list):
        try:
            for corpus in corpuses:
                new_corpus = Corpus(platform=corpus['platform'], entry_id=corpus['id'], data=corpus)
                db.session.add(new_corpus)
            db.session.commit()
        except Exception as e:
            print(f"Error inserting corpuses: {e.__str__()}")


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.String(), primary_key=True)
    author_id = db.Column(db.String())
    created_utc = db.Column(db.DateTime)
    name = db.Column(db.String())
    permalink = db.Column(db.String())
    score = db.Column(db.Integer)
    selftext = db.Column(db.String())
    subreddit = db.Column(db.String())
    title = db.Column(db.String())
    upvote_ratio = db.Column(db.Float)

    def __init__(self, id, author_id, created_utc, name, permalink, score, selftext, subreddit, title, upvote_ratio):
        self.id = id
        self.author_id = author_id
        self.created_utc = created_utc
        self.name = name
        self.permalink = permalink
        self.score = score
        self.selftext = selftext
        self.subreddit = subreddit
        self.title = title
        self.upvote_ratio = upvote_ratio

    @staticmethod
    def insert_posts(posts: list):
        try:
            for post in posts:
                new_post = Post(id=post.id, author_id=post.author_id, created_utc=post.created_utc,
                                name=post.name, permalink=post.permalink, score=post.score,
                                selftext=post.selftext, subreddit=post.subreddit,
                                title=post.title, upvote_ratio=post.upvote_ratio)
                db.session.add(new_post)
            db.session.commit()
        except Exception as e:
            print(f"Error inserting posts: {e.__str__()}")
