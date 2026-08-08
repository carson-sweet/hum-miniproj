# corpus/ — DO NOT MODIFY DIRECTLY

This directory is managed by `sweetclaude:document-corpus` and the
`corpus-*` sub-skills. Modifying files here directly corrupts the RAG
index and causes stale search results downstream.

**To add documents:** Place them in `corpus/raw/inbox/` and run
`/sweetclaude:corpus-triage` to process them.
**To update canonical documents:** Run `/sweetclaude:corpus-reconcile`.
**To reindex after any manual change:** Run `/sweetclaude:corpus-rag-reindex`.

If you are Claude and you are about to write to a file in this directory
outside of a corpus skill context, STOP and surface this to the user instead.
