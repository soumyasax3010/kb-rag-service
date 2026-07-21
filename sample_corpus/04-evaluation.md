# Evaluating RAG Systems

A RAG system has two things that can go wrong independently, so evaluation
measures both. **Retrieval quality** asks whether the right chunks were found at
all. **Generation quality** asks whether the answer is correct and faithful to
those chunks.

Retrieval is typically measured with recall@k: given a gold passage that should
be retrieved for a question, recall@k is one if that passage appears in the top k
results and zero otherwise, averaged over a set of questions. A high recall@5
means the relevant context almost always reaches the generator.

Generation faithfulness is whether every claim in the answer is supported by the
retrieved context. A common way to score this is an LLM-as-judge: a separate
model is given the answer and the context and asked whether each claim is
entailed. Faithfulness is the fraction of claims that are supported. Answer
correctness, by contrast, compares the answer to a gold reference and may use a
mix of semantic similarity and human or LLM judgment.

A good evaluation harness holds out a labeled set of question-and-answer pairs,
runs the full pipeline, and reports recall and faithfulness as numbers that can
be tracked as the system changes. Without such numbers it is impossible to tell
whether a change to chunking or retrieval actually helped.
