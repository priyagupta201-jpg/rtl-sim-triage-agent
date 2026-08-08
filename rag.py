import os
import json
import ollama
from triage_lib import SYSTEM_PROMPT, TRIAGE_SCHEMA, MODEL

def retrieve(log_text):
    """Return the KB note most relevant to this log (keyword overlap)."""
    best_note = ""
    best_score = -1
    for name in os.listdir("kb"):
        with open("kb/" + name) as f:
            note = f.read()

        score = 0
        for word in note.split():
            if word.lower() in log_text.lower():
                score += 1

        if score > best_score:
            best_score = score
            best_note = note

    return best_note


# ===========================================================================
# SEMANTIC retrieval (RAG Stage 2) — match by MEANING, not exact words.
# ===========================================================================
EMBED_MODEL = "nomic-embed-text"


def embed(text):
    """Turn text into a vector (list of 768 numbers) representing its meaning."""
    return ollama.embeddings(model=EMBED_MODEL, prompt=text)["embedding"]


def cosine(a, b):
    """Cosine similarity between two vectors: ~1 = very similar meaning, ~0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))          # how aligned they are
    norm_a = sum(x * x for x in a) ** 0.5           # length of vector a
    norm_b = sum(y * y for y in b) ** 0.5           # length of vector b
    return dot / (norm_a * norm_b)


def retrieve_semantic(log_text):
    """Return the KB note closest in MEANING to this log (embeddings + cosine)."""
    log_vec = embed(log_text)                       # embed the query (the log)
    best_note, best_sim = "", -1
    for name in os.listdir("kb"):
        with open("kb/" + name) as f:
            note = f.read()
        sim = cosine(log_vec, embed(note))          # compare meanings
        if sim > best_sim:
            best_sim = sim
            best_note = note
    return best_note

def triage_with_rag(filename, log_text, model=MODEL):
    """Triage one log, grounded in retrieved KB knowledge. Returns a finding dict."""

    # --- RETRIEVE: find the relevant reference note (semantic / embeddings) ---
    note = retrieve_semantic(log_text)

    # --- AUGMENT: put that note INTO the prompt, next to the log --------
    user_msg = (
        "Reference knowledge for this type of failure:\n" + note +
        "\n\nNow triage this log:\n===== " + filename + " =====\n" + log_text +
        "\n\nReturn one finding for this log."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    # --- GENERATE: the model answers, now grounded in the note ---------
    resp = ollama.chat(model=model, messages=messages,
                       format=TRIAGE_SCHEMA, options={"temperature": 0})
    obj = json.loads(resp["message"]["content"])
    return obj["findings"][0]      # one log in -> one finding out


if __name__ == "__main__":
    with open("logs/tc_handshake.log") as f:
        log = f.read()
    print(triage_with_rag("tc_handshake.log", log))

