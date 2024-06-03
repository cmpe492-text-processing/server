import os
import logging
import multiprocessing
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from nlp.corpus_generator import GenerateCorpus, Platform
from utils.database import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def log_process_thread_info(message):
    process_id = multiprocessing.current_process().pid
    thread_id = threading.current_thread().ident
    logger.info(f"{message} (Process ID: {process_id}, Thread ID: {thread_id})")


def process_batch(batch, dir_name, subreddit_id):
    log_process_thread_info("Processing batch")
    corpus_list = []
    for line in batch:
        line = line.strip()
        corpus_generator = GenerateCorpus(Platform.WIKI, dir_name, subreddit_id, "", line)
        corpus = corpus_generator.generate_corpus()
        if corpus is not None:
            corpus_list.append(corpus)
            logger.info(f"Generated corpus for line: {line}")
    return corpus_list


def process_file(file, raw_data_dir, dir_name):
    log_process_thread_info(f"Processing file {file}")
    subreddit_id = int(file.split("_")[1][:2])
    corpus_batches = []

    with open(os.path.join(raw_data_dir, file), "r") as f:
        lines = f.readlines()
        batches = [lines[i:i + BATCH_SIZE] for i in range(0, len(lines), BATCH_SIZE)]

        database_manager = DatabaseManager()

        with ThreadPoolExecutor() as executor:
            future_to_batch = {executor.submit(process_batch, batch, dir_name, subreddit_id): batch for batch in
                               batches}
            for future in as_completed(future_to_batch):
                try:
                    batch_corpus_list = future.result()
                    if batch_corpus_list:
                        logger.info(f"Inserting {len(batch_corpus_list)} corpuses into the database from {file}")
                        log_process_thread_info(f"Inserting batch from file {file}")
                        database_manager.insert_corpuses(batch_corpus_list)
                except Exception as exc:
                    logger.error(f"Batch generated an exception: {exc}")

    logger.info(f"Processed {len(lines)} lines from {file}")


def local():
    raw_data_dir = ""
    dir_name = raw_data_dir.split("/")[-1]
    files = sorted(os.listdir(raw_data_dir))

    with ProcessPoolExecutor() as executor:
        future_to_file = {executor.submit(process_file, file, raw_data_dir, dir_name): file for file in files}
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                future.result()  # This will re-raise any exceptions caught during processing
            except Exception as exc:
                logger.error(f"{file} generated an exception: {exc}")


if __name__ == "__main__":
    local()
