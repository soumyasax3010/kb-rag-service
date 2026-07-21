# Retrieval-Augmented Generation: Overview

Retrieval-Augmented Generation (RAG) is a pattern that combines a retriever with
a text-generating language model so the model can ground its answers in external
documents instead of relying only on its parametric memory.

A RAG system has three core stages. First, **ingestion**: documents are parsed,
split into chunks, and each chunk is embedded into a vector and stored in a
vector index. Second, **retrieval**: a user question is embedded with the same
encoder and the index is searched for the most similar chunks. Third,
**generation**: the retrieved chunks are inserted into the prompt as context and
the language model produces an answer that cites them.

The main benefit of RAG over a fine-tuned model is that the knowledge base can be
updated without retraining. Adding, removing, or correcting a document only
requires re-indexing it, which is cheap. RAG also reduces hallucinations
because the model is instructed to answer only from the provided context, and it
makes provenance possible: each claim can be traced back to a source chunk.
