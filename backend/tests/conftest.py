import os
import tempfile

# Point the vector store at a throwaway directory before any `app.*` module
# is imported, so running the test suite never touches a real translation
# memory on disk.
os.environ.setdefault("CHROMA_PERSIST_DIR", tempfile.mkdtemp(prefix="ai-translator-test-chroma-"))
