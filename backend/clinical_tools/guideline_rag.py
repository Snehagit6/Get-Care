from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class GuidelineRAG:
    """
    Local guideline retrieval engine.

    Initial implementation:
        SentenceTransformer + FAISS

    No LLM is used for retrieval itself.
    """

    def __init__(
        self,
        knowledge_dir: str = "data/rag",
        index_dir: str = "data/rag/index",
        embedding_model: str = (
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
    ) -> None:

        self.knowledge_dir = Path(
            knowledge_dir
        )

        self.index_dir = Path(
            index_dir
        )

        self.index_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.index_path = (
            self.index_dir / "guidelines.faiss"
        )

        self.metadata_path = (
            self.index_dir / "metadata.json"
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            encode_kwargs={
                "normalize_embeddings": True
            }
        )

        self.vectorstore: FAISS | None = None
        self.metadata: list[
            dict[str, Any]
        ] = []

    # ---------------------------------------------------------
    # Build index
    # ---------------------------------------------------------

    def build_index(self) -> None:

        documents = []

        for file_path in sorted(
            self.knowledge_dir.rglob("*.pdf")
        ):

            pages = PyPDFLoader(
                str(file_path)
            ).load()

            for page in pages:
                page.metadata.update(
                    {
                        "source": self._source_name(
                            file_path
                        ),
                        "document": file_path.name
                    }
                )

            documents.extend(pages)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = splitter.split_documents(
            documents
        )

        if not chunks:
            raise ValueError(
                f"No PDF guideline documents found "
                f"in {self.knowledge_dir}"
            )

        self.vectorstore = FAISS.from_documents(
            chunks,
            self.embeddings
        )

        self.vectorstore.save_local(
            str(self.index_dir)
        )

        self.metadata = [
            {
                **chunk.metadata,
                "text": chunk.page_content,
                "chunk_id": index
            }
            for index, chunk in enumerate(chunks)
        ]

        self.metadata_path.write_text(
            json.dumps(
                self.metadata,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

    # ---------------------------------------------------------
    # Load index
    # ---------------------------------------------------------

    def load_index(self) -> None:

        faiss_path = self.index_dir / "index.faiss"
        if not faiss_path.exists():
            raise FileNotFoundError(
                "FAISS index does not exist. "
                "Run build_index() first."
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                "Guideline metadata does not exist."
            )

        self.vectorstore = FAISS.load_local(
            str(self.index_dir),
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        self.metadata = json.loads(
            self.metadata_path.read_text(
                encoding="utf-8"
            )
        )

    # ---------------------------------------------------------
    # Retrieve
    # ---------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict[str, Any]]:

        if self.vectorstore is None:
            self.load_index()

        matches = self.vectorstore.similarity_search_with_score(
            query,
            k=top_k
        )

        results = []

        for document, distance in matches:

            metadata = document.metadata.copy()
            metadata["text"] = document.page_content

            metadata["similarity"] = round(
                1 / (1 + float(distance)),
                4
            )

            results.append(
                metadata
            )

        return results

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    @staticmethod
    def _source_name(file_path: Path) -> str:
        parts = {
            part.lower()
            for part in file_path.parts
        }

        for source in ("ada", "idf", "who"):
            if source in parts:
                return source.upper()

        return "UNKNOWN"