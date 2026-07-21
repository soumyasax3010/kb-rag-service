# Vector Search and Embeddings

An embedding model maps a piece of text to a fixed-length vector of floating
point numbers. Texts that are semantically similar produce vectors that are
close together in the vector space. The most common similarity measure is cosine
similarity, which compares the angle between two vectors and ignores their
length. Cosine distance is simply one minus cosine similarity, so lower
distances mean more similar texts.

To search a large corpus quickly, the vectors are stored in an index that
supports approximate nearest neighbor lookup. Two popular index types are
**ivfflat**, which partitions vectors into clusters and searches only the
nearest clusters, and **hnsw**, which builds a layered graph that is traversed
during search. HNSW usually gives better recall at similar latency and needs no
separate training step, while ivfflat can be faster for very large datasets once
tuned.

pgvector is a PostgreSQL extension that adds a vector column type and these
index types, so a single Postgres database can serve as both the relational
store and the vector store. This avoids running a separate vector database and
keeps document metadata and embeddings in the same transactional store.
