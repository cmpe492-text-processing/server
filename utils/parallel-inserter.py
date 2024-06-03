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


def process_batch(batch, dir_name, subreddit_id, file, batch_number, total_batches):
    log_process_thread_info(f"Processing batch {batch_number} out of {total_batches} for file {file}")
    corpus_list = []
    for line in batch:
        line = line.strip()
        corpus_generator = GenerateCorpus(Platform.WIKI, dir_name, subreddit_id, "", line)
        corpus = corpus_generator.generate_corpus()
        if corpus is not None:
            corpus_list.append(corpus)
            logger.info(f"Generated corpus for line: {line} in batch {batch_number} for file {file}")
    return corpus_list


def process_file(file, raw_data_dir, dir_name):
    log_process_thread_info(f"Processing file {file}")
    subreddit_id = int(file.split("_")[1][:2])
    corpus_batches = []

    with open(os.path.join(raw_data_dir, file), "r") as f:
        lines = f.readlines()
        batches = [lines[i:i + BATCH_SIZE] for i in range(0, len(lines), BATCH_SIZE)]
        total_batches = len(batches)

        database_manager = DatabaseManager()

        with ThreadPoolExecutor() as executor:
            future_to_batch = {
                executor.submit(process_batch, batch, dir_name, subreddit_id, file, batch_num + 1, total_batches): batch
                for batch_num, batch in enumerate(batches)}
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                batch_number = batches.index(batch) + 1
                try:
                    batch_corpus_list = future.result()
                    if batch_corpus_list:
                        logger.info(
                            f"Inserting {len(batch_corpus_list)} corpuses into the database from batch {batch_number} of file {file}")
                        log_process_thread_info(f"Inserting batch {batch_number} of file {file}")
                        database_manager.insert_corpuses(batch_corpus_list)
                except Exception as exc:
                    logger.error(
                        f"Batch {batch_number} out of {total_batches} for file {file} generated an exception: {exc}")

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
                future.result()
            except Exception as exc:
                logger.error(f"{file} generated an exception: {exc}")


if __name__ == "__main__":
    local()
