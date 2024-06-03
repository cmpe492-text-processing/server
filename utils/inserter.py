import os

from nlp.corpus_generator import GenerateCorpus, Platform
from utils.database import DatabaseManager


def local():
    database_manager = DatabaseManager()
    raw_data_dir = ""
    dir_name = raw_data_dir.split("/")[-1]
    files = os.listdir(raw_data_dir)
    files.sort()
    for file in files:
        print(f"\n\nProcessing {file}")
        subreddit_id = int(file.split("_")[1][:2])
        with open(os.path.join(raw_data_dir, file), "r") as f:
            corpus_list = []
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                corpus_generator = GenerateCorpus(Platform.WIKI, dir_name, subreddit_id, "", line)
                corpus = corpus_generator.generate_corpus()

                if corpus is not None:
                    corpus_list.append(corpus)
                    print("In line for insert: \"", line, end="\"\n")

            print(f"Inserting {len(lines)} corpuses into the database from {file}")
            database_manager.insert_corpuses(corpus_list)


if __name__ == "__main__":
    local()