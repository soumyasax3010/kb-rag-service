# Chunking Strategies

Chunking is the process of splitting a document into smaller passages before
embedding. The chunk size controls a tradeoff between precision and context.
Very large chunks contain many topics, so a single embedding blurs them and
retrieval matches become less precise. Very small chunks lose surrounding
context, so the retrieved passage may not be enough to answer the question.

A common default is **token-based chunking** with a window of about 512 tokens
and an overlap of about 64 tokens. The overlap means every token after the first
window appears in at least two chunks, which prevents context from being cut at
a boundary. Tokens are used instead of characters because models measure context
in tokens, so token-based sizes stay within the model's context budget.

Two alternatives are sentence-aware chunking, which splits on sentence
boundaries to avoid cutting mid-sentence, and semantic chunking, which groups
sentences by embedding similarity so each chunk covers one topic. Semantic
chunking is more expensive because it requires extra embedding passes, but it
tends to produce more coherent chunks for mixed-topic documents.
