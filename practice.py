# practice.py — Python fluency practice
#
# Save with Cmd+S, then run in the terminal:
#     .venv/bin/python practice.py
# (after the first run, just press Up arrow + Enter to re-run)


# ---- Task 1 (DONE) — kept here as a reference you can look back at ----
def count_by_category(findings):
    """Return a dict mapping each category -> how many times it appears."""
    count = {}                                # an empty dictionary, made once
    for f in findings:                        # walk through every finding
        cat = f["category"]                   # e.g. "TIMEOUT"
        count[cat] = count.get(cat, 0) + 1    # add 1 to that category's tally
    return count                              # hand back the finished dict



# ---- Task 3 (YOUR TURN) ----
def failing_messages(findings):
    """Return a list of the 'message' text for findings that are NOT 'PASS'.

    Example: for the test data below it should return
        ["timed out after 60s", "compile error in foo.v"]
    """
    # 1. start with an empty list:        result = []
    # 2. loop over each finding:          for f in findings:
    # 3. if its category is not "PASS":        if f["category"] != "PASS":
    # 4. add its message to the list:              result.append(f["message"])
    # 5. return the list:                 return result
    result = []
    for f in findings:
        if f["category"] != "PASS":
            result.append(f["message"])
    return result
    
        


# ---- Task 4 (YOUR TURN) ----
def summarize(findings):
    """Return a sentence like '4 findings, 2 failures'.

    'failures' means findings whose category is NOT 'PASS'.
    """
    # 1. total number of findings:        total = len(findings)
    # 2. count the failures (the counter pattern you already know):
    #        failures = 0
    #        for f in findings:
    #            if f["category"] != "PASS":
    #                failures += 1
    # 3. build and return the sentence with an f-string:
    #        return f"{total} findings, {failures} failures"
    total = 0;
    failures = 0;
    for f in findings:
        total += 1
        if f["category"] != "PASS":
            failures += 1

    return f"{total} findings, {failures} failures"


# ---- Task 5 (YOUR TURN) ----
def top_category(findings):
    """Return the category that appears most often.

    For the test data below that is "TIMEOUT" (it appears twice).
    """
    # 1. REUSE the function you already wrote to get the counts dict:
    #        counts = count_by_category(findings)
    #    (counts looks like {"TIMEOUT": 2, "PASS": 1, "COMPILE": 1})
    #
    # 2. find the key with the biggest value. Two ways — pick one:
    #    (a) the loop way (clearest while learning):
    #            best_cat = None
    #            best_n = -1
    #            for cat in counts:                 # cat is each key
    #                if counts[cat] > best_n:
    #                    best_n = counts[cat]
    #                    best_cat = cat
    #            return best_cat
    #    (b) the one-line Python way (try this once you've done (a)):
    #            return max(counts, key=counts.get)
    counts = count_by_category(findings)
    best_cat = None
    best_n = -1
    for cat in counts:
        if counts[cat] > best_n:
            best_n = counts[cat]
            best_cat = cat
    return best_cat


# ---- Task 6 (CAPSTONE — YOUR TURN) ----
def print_report(findings):
    """Print a full triage report by REUSING the functions above.

    Expected output for the test data:
        === Triage Report ===
        4 findings, 2 failures
        Most common category: TIMEOUT
        Breakdown: {'TIMEOUT': 2, 'PASS': 1, 'COMPILE': 1}
        Failures:
          - timed out after 60s
          - compile error in foo.v
    """
    # This function PRINTS (it doesn't return). Call your own functions:
    # 1. print a title line:               print("=== Triage Report ===")
    # 2. print the summary:                print(summarize(findings))
    # 3. print the top category:           print("Most common category:", top_category(findings))
    # 4. print the breakdown dict:         print("Breakdown:", count_by_category(findings))
    # 5. print "Failures:" then loop over failing_messages(findings)
    #    and print each one indented:
    #        print("Failures:")
    #        for m in failing_messages(findings):
    #            print("  -", m)
    print("=== Triage Report ===")
    print(summarize(findings))
    print("Most common category:", top_category(findings))
    print("Breakdown:", count_by_category(findings))
    print("Failures:")
    for m in failing_messages(findings):
        print("  -", m) 
    
    
if __name__ == "__main__":
    findings = [
        {"category": "TIMEOUT",  "message": "timed out after 60s"},
        {"category": "PASS",     "message": "ok"},
        {"category": "COMPILE",  "message": "compile error in foo.v"},
        {"category": "TIMEOUT",  "message": "timed out again"},
    ]
    print_report(findings)
