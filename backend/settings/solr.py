from .zenv import DEBUG, FOLDER_DEBUG_CONTAINER, PROJECT_DIR, config

USE_SOLR = config("USE_SOLR", default=True, cast=bool)
SOLR_URL = config("SOLR_URL", default="http://solr:solr@backendsolr:8983")
HAYSTACK_SIGNAL_PROCESSOR = "backend.haystack.CelerySignalProcessor"

if DEBUG:
    if FOLDER_DEBUG_CONTAINER != PROJECT_DIR:
        # HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
        SOLR_URL = "http://solr:solr@localhost:8983"
        REDIS_HOST = "localhost"

SOLR_COLLECTION = "backend_arq1"

SEARCH_BACKEND = "haystack.backends.solr_backend.SolrEngine"
SEARCH_URL = ("URL", "{}/solr/{}".format(SOLR_URL, SOLR_COLLECTION))
HAYSTACK_ROUTERS = ["backend.haystack.DefaultRouter"]
HAYSTACK_ITERATOR_LOAD_PER_QUERY = 100
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": SEARCH_BACKEND,
        SEARCH_URL[0]: SEARCH_URL[1],
        "BATCH_SIZE": 1000,
        "TIMEOUT": 600,
        "EXCLUDED_INDEXES": [
            # 'backend.arq.search_indexes.ArqDocIndex',
        ],
    },
    "backendarq": {
        "ENGINE": SEARCH_BACKEND,
        "URL": "{}/solr/{}".format(SOLR_URL, "backend_arq2"),
        "BATCH_SIZE": 1000,
        "TIMEOUT": 600,
        "EXCLUDED_INDEXES": [
            # 'backend.search.search_indexes....Index',
        ],
    },
}
