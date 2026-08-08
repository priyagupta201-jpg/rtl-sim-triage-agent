import streamlit as st
import os
from triage_lib import classify
from rag import retrieve, retrieve_semantic, triage_with_rag
from fix_agent import propose_fix

st.title("VCS Regression Triage")

logs = os.listdir("logs")              # 1. list the files in the logs/ folder
chosen = st.selectbox("Pick a log", logs)   # 2. dropdown; 'chosen' = the picked filename

with open("logs/" + chosen) as f:      # 3. open the picked file
    text = f.read()                    #    read all its text into 'text'

st.code(text)                          # 4. show that text on the page

if st.button("Triage this log"):
    # RETRIEVE: show which reference note RAG pulled in (semantic / embeddings)
    note = retrieve_semantic(text)
    with st.expander("Reference knowledge retrieved (RAG)"):
        st.markdown(note)

    # AGENT 1 — triage (grounded by RAG): WHAT broke?
    st.subheader("Agent 1 — Triage (what broke?)")
    finding = triage_with_rag(chosen, text)
    st.write(finding)

    # AGENT 2 — fix proposer: HOW to fix it?
    # ORCHESTRATION: agent 1's output (finding) becomes agent 2's input.
    st.subheader("Agent 2 — Fix proposal (how to fix?)")
    fix = propose_fix(finding, text)
    st.write(fix)


