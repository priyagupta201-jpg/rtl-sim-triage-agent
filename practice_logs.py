# practice_logs.py — Python practice on REAL log files from logs/
#
# Save with Cmd+S, then run:
#     .venv/bin/python practice_logs.py


# ---- Task 7a (YOUR TURN): read a file off disk ----
def read_log(path):
    """Open the file at `path`, read all its text, and return it as one string."""
    # The standard, safe way to read a whole file in Python:
    #     with open(path) as fh:      # opens the file, auto-closes it after
    #         return fh.read()        # read() gives back the entire contents as a string
    pass   # <-- write the 2 lines above, then delete this


# ---- Task 7b (YOUR TURN): classify the text by keywords ----
def classify_log(text):
    """Return a category string by looking for keywords in the log text.

    Rules (check in this order — first match wins):
        - "Error-[" or "compilation"   -> "COMPILE"
        - "Assertion"                  -> "ASSERTION"
        - "scoreboard" or "mismatch"   -> "SCOREBOARD"
        - "timeout" or "$finish"       -> "TIMEOUT"
        - otherwise                    -> "OTHER"
    """
    # New idea: `if "word" in text:` is True when that word appears anywhere
    # in the string. Chain choices with if / elif / else:
    #
    #     if "Error-[" in text or "compilation" in text:
    #         return "COMPILE"
    #     elif "Assertion" in text:
    #         return "ASSERTION"
    #     elif "scoreboard" in text or "mismatch" in text:
    #         return "SCOREBOARD"
    #     elif "timeout" in text or "$finish" in text:
    #         return "TIMEOUT"
    #     else:
    #         return "OTHER"
    pass   # <-- write the if/elif/else chain above, then delete this


if __name__ == "__main__":
    text = read_log("logs/tc_fifo_overflow.log")
    print("Category:", classify_log(text))   # expect: ASSERTION
