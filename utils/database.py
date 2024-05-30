import psycopg2
from psycopg2 import OperationalError
import os
from dotenv import load_dotenv
import json


class DatabaseManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print("basedir", base_dir)
        env_path = os.path.join(base_dir, ".env")
        load_dotenv(env_path)
        self.connection = None
        self.create_connection()

    def create_connection(self):
        try:
            # Connect to the database using DATABASE_URL environment variable
            connection = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
            self.connection = connection
            print("Connection to PostgreSQL DB successful")
        except OperationalError as e:
            print(f"The error '{e}' occurred")

    def execute_query(self, query):
        if self.connection is not None:
            self.connection.autocommit = True
            cursor = self.connection.cursor()
            try:
                cursor.execute(query)
                print("Query executed successfully")
            except OperationalError as e:
                print(f"The error '{e}' occurred")
            finally:
                cursor.close()

    def insert_corpuses(self, corpuses):
        if self.connection is not None:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO corpuses (platform, entry_id, data)
            VALUES (%s, %s, %s::jsonb)
            ON CONFLICT (platform, entry_id) DO NOTHING;
            """

            for corpus in corpuses:
                json_data = json.dumps(corpus, indent=0)
                values = (corpus["platform"], corpus["id"], json_data)
                try:
                    cursor.execute(query, values)
                    print("Query executed successfully")
                except OperationalError as e:
                    print(f"The error '{e}' occurred")

            self.connection.commit()
            cursor.close()

    def insert_posts(self, posts):
        if self.connection is not None:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO posts (id, author_id, created_utc, name, permalink, score, selftext, subreddit, title, upvote_ratio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
            """

            for post in posts:
                values = (
                    post.id,
                    post.author_id,
                    post.created_utc,
                    post.name,
                    post.permalink,
                    post.score,
                    post.selftext,
                    post.subreddit,
                    post.title,
                    post.upvote_ratio,
                )
                try:
                    cursor.execute(query, values)
                    print("Query executed successfully")
                except OperationalError as e:
                    print(f"The error '{e}' occurred")

            self.connection.commit()
            cursor.close()

    def close_connection(self, debug=True):
        if self.connection is not None:
            self.connection.close()
            if debug:
                print("Database connection closed.")

    def get_corpuses(self):
        if self.connection is not None:
            cursor = self.connection.cursor()
            query = "SELECT * FROM corpuses"
            try:
                cursor.execute(query)
                corpuses = cursor.fetchall()
                return corpuses
            except OperationalError as e:
                print(f"The error '{e}' occurred")
        return None

    def get_relatedness(self, entity_1, entity_2):
        if self.connection is not None:
            cursor = self.connection.cursor()
            query = f"SELECT relatedness FROM entity_relatedness WHERE entity_1 = {entity_1} AND entity_2 = {entity_2}"
            try:
                cursor.execute(query)
                corpuses = cursor.fetchall()
                cursor.close()
                return corpuses
            except OperationalError as e:
                print(f"The error '{e}' occurred")
            finally:
                cursor.close()
        return None

    def upsert_relatedness(self, entity_1, entity_2, relatedness):
        if self.connection is not None:
            cursor = self.connection.cursor()
            query = f"""
            INSERT INTO entity_relatedness (entity_1, entity_2, relatedness)
            VALUES ({entity_1}, {entity_2}, {relatedness})
            ON CONFLICT (entity_1, entity_2) DO UPDATE SET relatedness = {relatedness};
            """
            try:
                cursor.execute(query)
            except OperationalError as e:
                print(f"The error '{e}' occurred")

            self.connection.commit()
            cursor.close()
        return None
