from metax.frameworks_and_drivers.opensearch.indices.index_metadata_format import IndexMetadata

INDEX_NAME = "discounted_product_read_model_v1"

ALIAS_NAME = "discounted_products_read_model"


INDEX_BODY = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s",
            "codec": "best_compression",
        },
        "analysis": {
            "filter": {
                "discounted_product_edge_ngram": {"type": "edge_ngram", "min_gram": 2, "max_gram": 20},
                "am_stemmer": {"type": "stemmer", "language": "armenian"},
                "en_stemmer": {"type": "stemmer", "language": "english"},
                "ru_stemmer": {"type": "stemmer", "language": "russian"},
            },
            "analyzer": {
                "armenian_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "am_stemmer", "discounted_product_edge_ngram"],
                },
                "english_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "en_stemmer", "discounted_product_edge_ngram"],
                },
                "russian_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ru_stemmer", "discounted_product_edge_ngram"],
                },
            },
        },
    },
    "mappings": {  # https://docs.opensearch.org/latest/mappings/#mapping-structure-and-example
        "properties": {
            "name": {
                "type": "text",
                "fields": {
                    "arm": {"type": "text", "analyzer": "armenian_analyzer", "search_analyzer": "standard"},
                    "eng": {"type": "text", "analyzer": "english_analyzer", "search_analyzer": "standard"},
                    "rus": {"type": "text", "analyzer": "russian_analyzer", "search_analyzer": "standard"},
                },
            },
            "real_price": {"type": "scaled_float", "scaling_factor": 100},
            "discounted_price": {"type": "scaled_float", "scaling_factor": 100},
            "category_uuid": {
                "type": "keyword",
            },
            "category_name": {
                "type": "keyword",
            },
            "retailer_uuid": {"type": "keyword"},
            "retailer_name": {"type": "keyword"},
            "url": {"type": "keyword"},
            "created_at": {
                "type": "date",
            },
        }
    },
}

DISCOUNTED_PRODUCT_READ_MODEL_METADATA: IndexMetadata = {
    "index_name": INDEX_NAME,
    "alias_name": ALIAS_NAME,
    "index_body": INDEX_BODY,
}
