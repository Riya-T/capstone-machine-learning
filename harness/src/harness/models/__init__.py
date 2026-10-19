"""Model calls: backends that send prompts to a model (or a mock), and the
parser that turns a model's answer into program files.

Usage:
    from harness.models.backends import CachedBackend, make_backend
    from harness.models.parser import parse_program
"""
