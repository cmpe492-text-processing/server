# Project X - Server

## Overview

The backend is responsible for processing online conversation data, performing named entity linking, sentiment analysis, and constructing context windows to reveal relationships between entities. The processed data is stored in a SQL database. 

## Key Features

- **Named Entity Linking**: Uses TagMe to link entities to Wikidata, enriching the data with relevant information.
- **Sentiment Analysis**: Processes individual context windows to determine sentiment polarity using NLTK's VADER lexicon.
- **Context Window Construction**: Employs SpaCy’s dependency parsing to create fine-grained co-occurrence windows, enhancing relationship detection between entities.
- **Efficient Data Handling**: Parallel processing and caching ensure that data is handled quickly and graphs are updated in real time.
- **RESTful API**: Provides endpoints to fetch processed data and serve it to the frontend for visualization.

## Tools & Technologies Used

- **Python 3.11**: Core language for backend logic and data processing.
- **Flask**: MVC framework for the backend, managing API endpoints and data flow.
- **PostgreSQL**: Database for storing processed entities, relationships, and sentiment data.
- **TagMe**: Named entity linking tool for connecting text entities to Wikidata.
- **SpaCy**: Used to create syntactic dependency graphs for context window generation.
- **NLTK (VADER)**: Performs sentiment analysis on context windows.
