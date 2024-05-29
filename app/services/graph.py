

def get_graph(wiki_id: int):
    """
    Get the graph for the given entity.

    :param wiki_id:     Wikidata ID
    :return:            {
                            nodes: [
                                {
                                    id: int,
                                    name: str,
                                    type: str
                                }
                            ],
                            links: [
                                {
                                    source: int,
                                    target: int,
                                    type: str
                                }
                            ]
                        }
    """




