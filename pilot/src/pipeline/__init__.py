"""pipeline: the data-collection pipeline for training a code writer on the
outcomes of later edits (see docs/Project_Proposal_473_v2.docx.pdf).

Modules: config (settings), registry (tasks and writer prompts), backends
(model calls), parser (model answers to files), store (results), runner
(Docker sandbox), evaluator (test categories), scorer (preferences).

Usage:
    uv run pytest                                  # from pilot/
    from pipeline.config import load_config
"""
