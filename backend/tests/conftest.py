import os
import tempfile

# Point the vector store and glossary at throwaway locations before any
# `app.*` module is imported, so running the test suite never touches real
# data on disk.
os.environ.setdefault("CHROMA_PERSIST_DIR", tempfile.mkdtemp(prefix="ai-translator-test-chroma-"))
os.environ.setdefault(
    "GLOSSARY_PATH", os.path.join(tempfile.mkdtemp(prefix="ai-translator-test-glossary-"), "glossary.json")
)
