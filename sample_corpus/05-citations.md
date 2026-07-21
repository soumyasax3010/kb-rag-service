# Citations and Grounded Answers

Citations are what separate a grounded knowledge-base answer from a generic
chatbot reply. In a RAG system, each retrieved chunk carries metadata that
identifies its source document and its position within that document. When the
generator produces an answer, it is instructed to cite the passage number for
each claim, and the system maps those passage numbers back to the concrete
chunks.

A practical prompt gives the model numbered context passages and tells it to
answer only from them, marking each claim with a bracketed passage number such
as [1]. The system then resolves those numbers to citations that include the
source filename and a short snippet of the supporting text. If the answer cites
no passages, or cites passages that were not retrieved, that is a signal that
the answer may not be grounded.

Groundedness is the property that every claim in the answer is supported by a
cited passage. It is closely related to faithfulness but emphasizes the citation
link explicitly. A grounded answer lets a user click through to the source
passage and verify the claim, which is essential for knowledge bases used in
domains where accuracy matters, such as internal documentation or support.
