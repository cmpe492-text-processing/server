from nlp.corpus_extractor import CorpusExtractor
from nlp.corpus_generator import GenerateCorpus, Platform
from reddit import Reddit, RedditPost
from database import DatabaseManager
import random


def main():
    reddit = Reddit()
    database_manager = DatabaseManager()
    politics_subreddits = ["trump", "politics", "elections", "democrats", "republican", "PoliticalDiscussion"]
    football_subreddits = ['galatasaray', 'soccer', 'superlig', 'FenerbahceSK']
    python_subreddits = ['Python', 'PythonProjects2', 'PythonLearning', 'learnpython']
    c_subreddits = ['C_Programming', 'cpp', 'csharp', 'Cplusplus']
    programming_subreddits = ['learnprogramming', 'AskProgramming', 'programming']
    other_subreddits = ['AskReddit', 'todayilearned', 'news', 'nottheonion', 'IAmA', 'worldnews', 'science',
                        'changemyview', 'The_Donald', 'askscience', 'copypasta', 'Turkey', 'Yatirim', 'ankara',
                        'kopyamakarna', 'ArsivUnutmaz', 'trpolitics', 'tibukandtoker']
    all_subreddits = (other_subreddits + politics_subreddits + football_subreddits + python_subreddits
                      + c_subreddits + programming_subreddits)
    random.shuffle(all_subreddits)

    for subreddit in all_subreddits:
        post_list: list[RedditPost] = reddit.get_new_posts(subreddit, limit=10)

        corpus_list: list = []
        for post in post_list:
            corpus_generator = GenerateCorpus(Platform.REDDIT, subreddit, post.id, post.title, post.selftext)
            corpus = corpus_generator.generate_corpus()
            if corpus is not None:
                corpus_list.append(corpus)
            else:
                print("Empty text, skipped this post for creating corpus")

        print(
            f"Inserting {len(post_list)} posts and {len(corpus_list)} "
            f"corpuses into the database related to {subreddit}.")

        database_manager.insert_posts(post_list)
        database_manager.insert_corpuses(corpus_list)


if __name__ == "__main__":
    main()
