#!/usr/bin/env python3
"""
embedder.py — Shared embedding module for code-graph-index.

Embedding strategies (auto-selected, best first):
  1. ONNX: all-MiniLM-L6-v2 INT8-quantized (384-dim, ~22 MB model)
     Requires: onnxruntime + numpy (pip install onnxruntime)
     Model is bundled as gzip in the skill — extracted on first use.
  2. Hash: deterministic token-hashing (384-dim, zero external deps)
     Fallback when onnxruntime is not installed.

Both produce L2-normalised 384-dim float32 vectors suitable for FAISS IndexFlatIP.

Model source (priority order):
  1. Bundled:  .agent/skills/code-graph-index/model/*.gz  (shipped with GravityKit)
  2. CDN:     cdn.jsdelivr.net npm packages (fallback if bundled files missing)
  3. Hash:    no model needed (lowest quality, always available)
"""
from __future__ import annotations

import gzip
import logging
import os
import re
import shutil
import unicodedata
import urllib.request
import urllib.error
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_DIM = 384
MAX_SEQ_LEN = 128  # MiniLM default

# Bundled model location (relative to this script)
_BUNDLED_MODEL_DIR = Path(__file__).resolve().parent.parent / "model"

# CDN fallback URLs — used only if bundled .gz files are missing.
_CDN_FILES = {
    "model.onnx": (
        "https://cdn.jsdelivr.net/npm/@ngao/search-core@1.0.1"
        "/models/Xenova/all-MiniLM-L6-v2/onnx/model_quantized.onnx"
    ),
    "vocab.txt": (
        "https://cdn.jsdelivr.net/npm/@alvix/all-minilm-l6-v2@1.0.1"
        "/dist/Xenova/all-MiniLM-L6-v2/vocab.txt"
    ),
}

# Well-known special tokens for all-MiniLM-L6-v2 (BERT-based)
_CLS_ID = 101
_SEP_ID = 102
_PAD_ID = 0
_UNK_ID = 100


# ---------------------------------------------------------------------------
# Model provisioning: bundled .gz first, CDN fallback
# ---------------------------------------------------------------------------

def ensure_model(model_dir: str | Path | None = None) -> Path:
    """Ensure model files are ready in model_dir.

    Strategy:
      1. If model_dir already has model.onnx + vocab.txt → done.
      2. Try extracting from bundled .gz files shipped with the skill.
      3. Fall back to downloading from jsdelivr CDN.

    Returns the model directory path.
    """
    if model_dir is None:
        model_dir = Path(".code-graph-index") / "model"
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    needed = {"model.onnx", "vocab.txt"}

    for name in list(needed):
        dest = model_dir / name
        if dest.exists() and dest.stat().st_size > 0:
            needed.discard(name)

    if not needed:
        logger.info("Model files already present in %s", model_dir)
        return model_dir

    # --- Strategy 1: Extract from bundled gzip ---
    extracted = set()
    for name in list(needed):
        gz_path = _BUNDLED_MODEL_DIR / (name + ".gz")
        if gz_path.exists():
            dest = model_dir / name
            logger.info("Extracting bundled %s -> %s", gz_path, dest)
            print(f"   📦 Extracting bundled {name} ...")
            try:
                _extract_gz(gz_path, dest)
                size_mb = dest.stat().st_size / (1024 * 1024)
                print(f"   ✅ {name} ({size_mb:.1f} MB)")
                extracted.add(name)
            except Exception as exc:
                print(f"   ⚠️  Extract failed for {name}: {exc}")
                logger.warning("Extract failed for %s: %s", gz_path, exc)
                dest.unlink(missing_ok=True)

    needed -= extracted

    if not needed:
        return model_dir

    # --- Strategy 2: Download from CDN ---
    cdn_urls = _resolve_cdn_urls()
    for name in list(needed):
        url = cdn_urls.get(name)
        if not url:
            continue
        dest = model_dir / name
        logger.info("Downloading %s -> %s", url, dest)
        print(f"   ⬇ Downloading {name} from jsdelivr CDN ...")
        try:
            _download(url, dest)
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"   ✅ {name} ({size_mb:.1f} MB)")
            needed.discard(name)
        except Exception as exc:
            print(f"   ⚠️  Download failed for {name}: {exc}")
            logger.warning("Download failed for %s: %s", url, exc)
            dest.unlink(missing_ok=True)

    if needed:
        raise RuntimeError(
            f"Could not provision model files: {needed}. "
            f"Check bundled .gz files in {_BUNDLED_MODEL_DIR} or network access."
        )

    return model_dir


def _extract_gz(src: Path, dest: Path) -> None:
    """Extract a gzip file to dest."""
    with gzip.open(str(src), "rb") as f_in:
        with open(dest, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


def _resolve_cdn_urls() -> dict[str, str]:
    """Return {local_name: url} mapping for CDN fallback."""
    custom = os.environ.get("GKT_MODEL_CDN")
    if custom:
        base = custom.rstrip("/")
        return {
            "model.onnx": f"{base}/model_quantized.onnx",
            "vocab.txt": f"{base}/vocab.txt",
        }
    return dict(_CDN_FILES)


def _download(url: str, dest: Path) -> None:
    """Download a file from URL with progress indicator."""
    req = urllib.request.Request(url, headers={"User-Agent": "gkt-code-graph-index/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        dest.parent.mkdir(parents=True, exist_ok=True)
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    print(f"\r     {downloaded // 1024:,d} / {total // 1024:,d} KB ({pct}%)",
                          end="", flush=True)
        if total > 0:
            print()


# ---------------------------------------------------------------------------
# Pure-Python WordPiece Tokenizer (no external dependencies)
# ---------------------------------------------------------------------------

class WordPieceTokenizer:
    """Minimal BERT WordPiece tokenizer — pure stdlib Python.

    Compatible with all-MiniLM-L6-v2 vocab.txt format.
    """

    def __init__(self, vocab_path: str | Path):
        self.vocab: dict[str, int] = {}
        self.ids_to_tokens: dict[int, str] = {}
        with open(vocab_path, encoding="utf-8") as f:
            for idx, line in enumerate(f):
                token = line.rstrip("\n")
                self.vocab[token] = idx
                self.ids_to_tokens[idx] = token
        self.unk_id = self.vocab.get("[UNK]", _UNK_ID)

    def tokenize(self, text: str, max_length: int = MAX_SEQ_LEN) -> dict:
        """Tokenize text and return input_ids + attention_mask."""
        # Step 1: Normalize — lowercase + strip accents (BERT uncased)
        text = text.lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

        # Step 2: Basic tokenization — split on whitespace + punctuation
        tokens = self._basic_tokenize(text)

        # Step 3: WordPiece subword tokenization
        wp_ids: list[int] = [_CLS_ID]
        for token in tokens:
            wp_ids.extend(self._wordpiece(token))
            if len(wp_ids) >= max_length - 1:
                break
        wp_ids = wp_ids[:max_length - 1]
        wp_ids.append(_SEP_ID)

        # Step 4: Pad to max_length
        attn_mask = [1] * len(wp_ids)
        pad_len = max_length - len(wp_ids)
        wp_ids.extend([_PAD_ID] * pad_len)
        attn_mask.extend([0] * pad_len)

        return {"input_ids": wp_ids, "attention_mask": attn_mask}

    def _basic_tokenize(self, text: str) -> list[str]:
        """Split on whitespace and punctuation."""
        # Insert spaces around punctuation
        output: list[str] = []
        for ch in text:
            if self._is_punctuation(ch):
                output.append(f" {ch} ")
            elif ch.isspace():
                output.append(" ")
            else:
                output.append(ch)
        return "".join(output).split()

    @staticmethod
    def _is_punctuation(ch: str) -> bool:
        cp = ord(ch)
        if (33 <= cp <= 47) or (58 <= cp <= 64) or (91 <= cp <= 96) or (123 <= cp <= 126):
            return True
        cat = unicodedata.category(ch)
        return cat.startswith("P")

    def _wordpiece(self, token: str) -> list[int]:
        """WordPiece tokenization for a single word."""
        if token in self.vocab:
            return [self.vocab[token]]

        ids: list[int] = []
        start = 0
        while start < len(token):
            end = len(token)
            found = False
            while start < end:
                substr = token[start:end]
                if start > 0:
                    substr = "##" + substr
                if substr in self.vocab:
                    ids.append(self.vocab[substr])
                    found = True
                    break
                end -= 1
            if not found:
                ids.append(self.unk_id)
                start += 1
            else:
                start = end
        return ids


# ---------------------------------------------------------------------------
# ONNX Embedder
# ---------------------------------------------------------------------------

class OnnxEmbedder:
    """Sentence embedding using ONNX Runtime + WordPiece tokenizer.

    Loads all-MiniLM-L6-v2 quantized model and produces 384-dim vectors.
    """

    def __init__(self, model_dir: str | Path):
        import numpy as np  # noqa: F811
        try:
            import onnxruntime as ort
        except ImportError:
            raise RuntimeError(
                "onnxruntime is required for ONNX embeddings. "
                "Install with: pip install onnxruntime"
            )

        model_dir = Path(model_dir)
        model_path = model_dir / "model.onnx"
        vocab_path = model_dir / "vocab.txt"

        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        if not vocab_path.exists():
            raise FileNotFoundError(f"Vocab file not found: {vocab_path}")

        self.np = np
        self.tokenizer = WordPieceTokenizer(vocab_path)
        # Suppress ONNX Runtime verbose logging
        opts = ort.SessionOptions()
        opts.log_severity_level = 3
        self.session = ort.InferenceSession(str(model_path), opts)
        self._dim = MODEL_DIM
        logger.info("ONNX embedder loaded from %s", model_dir)

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> "numpy.ndarray":
        """Produce a single 384-dim normalised embedding vector."""
        np = self.np
        tok = self.tokenizer.tokenize(text, max_length=MAX_SEQ_LEN)

        input_ids = np.array([tok["input_ids"]], dtype=np.int64)
        attention_mask = np.array([tok["attention_mask"]], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

        outputs = self.session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        # outputs[0] shape: (1, seq_len, hidden_dim) — token embeddings
        token_embeddings = outputs[0]  # (1, seq_len, 384)

        # Mean pooling — average only non-padding tokens
        mask_expanded = attention_mask[:, :, None].astype(np.float32)
        sum_embeddings = (token_embeddings * mask_expanded).sum(axis=1)
        sum_mask = mask_expanded.sum(axis=1).clip(min=1e-9)
        sentence_embedding = (sum_embeddings / sum_mask)[0]  # (384,)

        # L2 normalise
        norm = float(np.linalg.norm(sentence_embedding))
        if norm > 0:
            sentence_embedding /= norm

        return sentence_embedding.astype(np.float32)

    def embed_batch(self, texts: list[str]) -> "numpy.ndarray":
        """Embed multiple texts. Returns (N, 384) array."""
        np = self.np
        vecs = np.empty((len(texts), self._dim), dtype=np.float32)
        for i, text in enumerate(texts):
            vecs[i] = self.embed(text)
        return vecs


# ---------------------------------------------------------------------------
# Hash Embedder (fallback — zero deps beyond numpy)
# ---------------------------------------------------------------------------

class HashEmbedder:
    """Deterministic token-hashing embedder. No model files needed."""

    def __init__(self, dim: int = MODEL_DIM):
        self._dim = dim
        try:
            import numpy as np
            self.np = np
        except ImportError:
            raise RuntimeError("numpy is required. Install with: pip install numpy")

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, text: str) -> "numpy.ndarray":
        np = self.np
        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text.lower())
        for token in tokens:
            idx = hash(token) % self._dim
            vec[idx] += 1.0
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    def embed_batch(self, texts: list[str]) -> "numpy.ndarray":
        np = self.np
        vecs = np.empty((len(texts), self._dim), dtype=np.float32)
        for i, text in enumerate(texts):
            vecs[i] = self.embed(text)
        return vecs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_EMBEDDER = None


def get_embedder(
    model_dir: str | Path | None = None,
    auto_download: bool = False,
) -> OnnxEmbedder | HashEmbedder:
    """Return the best available embedder.

    Priority: ONNX (if model present + onnxruntime installed) > Hash fallback.

    Args:
        model_dir: Path to directory containing model.onnx + vocab.txt.
                   Default: .code-graph-index/model/
        auto_download: If True and model not present, download from jsdelivr CDN.
    """
    global _EMBEDDER
    if _EMBEDDER is not None:
        return _EMBEDDER

    if model_dir is None:
        model_dir = Path(".code-graph-index") / "model"
    model_dir = Path(model_dir)

    # Try ONNX first
    try:
        import onnxruntime  # noqa: F401

        if auto_download:
            try:
                ensure_model(model_dir)
            except Exception as exc:
                logger.warning("Model download failed, falling back to hash: %s", exc)
                _EMBEDDER = HashEmbedder()
                return _EMBEDDER

        if (model_dir / "model.onnx").exists() and (model_dir / "vocab.txt").exists():
            _EMBEDDER = OnnxEmbedder(model_dir)
            return _EMBEDDER
        else:
            logger.info("ONNX model files not found in %s, using hash embedder", model_dir)
    except ImportError:
        logger.info("onnxruntime not installed, using hash embedder")

    _EMBEDDER = HashEmbedder()
    return _EMBEDDER


def embed(text: str, dim: int = MODEL_DIM) -> "numpy.ndarray":
    """Convenience function: embed text using the best available strategy."""
    emb = get_embedder()
    return emb.embed(text)
