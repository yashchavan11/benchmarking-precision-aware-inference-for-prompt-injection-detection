"""Shared tokenizer policy and input checks for the unpadded development pilot."""

import hashlib

from . import tokenizer_audit

CAP = 1024
PREPROCESSING_OPTIONS = {
    "tokenizer_class": "Qwen2TokenizerFast", "use_fast": True,
    "add_special_tokens": True, "split_special_tokens": False,
    "padding": False, "truncation": True, "max_length": CAP,
    "truncation_side": "right", "padding_side": "left",
    "chat_template": False, "manual_eos": False,
    "model_pad_token_id": None, "model_pooling": "original_unpadded_batch_one",
}


class PreprocessingError(ValueError):
    """Fixed diagnostics that do not expose source text."""


def validate_vectors(ids, mask):
    if not (isinstance(ids, list) and 1 <= len(ids) <= CAP
            and isinstance(mask, list) and len(mask) == len(ids)
            and all(type(value) is int and 0 <= value < tokenizer_audit.VOCAB_LIMIT for value in ids)
            and all(type(value) is int and value == 1 for value in mask)):
        raise PreprocessingError(
            "Inference requires a nonempty unpadded token vector and all-one attention mask"
        )


def encode_prompt(tokenizer, prompt, expected_sha256):
    """Return checked capped IDs, attention mask, and original token length."""
    if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != expected_sha256:
        raise PreprocessingError("Original prompt changed before tokenization")

    original, _ = tokenizer_audit.encode(tokenizer, [prompt])
    capped, masks = tokenizer_audit.encode(tokenizer, [prompt], cap=CAP)
    ids, mask = capped[0], masks[0]
    validate_vectors(ids, mask)
    if ids != original[0][:CAP]:
        raise PreprocessingError("Tokenization disagrees with the uncapped right prefix")
    return ids, mask, len(original[0])
