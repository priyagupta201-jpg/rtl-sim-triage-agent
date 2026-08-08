# Python Cheat Sheet — the subset you actually use

Keep this open while you write. Looking things up IS how you learn — not cheating.

---

## Variables (no type declarations — Python figures it out)
```python
name = "tc_handshake.log"      # string
count = 6                       # int (number)
done = True                     # boolean (True / False)
```

## Lists (ordered collection — like an array)
```python
logs = ["a.log", "b.log", "c.log"]
logs[0]            # first item -> "a.log"   (indexing starts at 0)
logs[-1]           # last item  -> "c.log"
len(logs)          # how many   -> 3
logs.append("d.log")   # add to the end
for log in logs:       # loop over every item
    print(log)
```

## Dicts (key -> value lookup table)
```python
finding = {"category": "TIMEOUT", "confidence": "high"}
finding["category"]          # look up a value -> "TIMEOUT"
finding["category"] = "PASS" # set/change a value
"category" in finding        # is the key present? -> True
for key in finding:          # loop over keys
    print(key, finding[key])
for key, value in finding.items():   # loop over key+value together
    print(key, value)
```

## if / else (note the colon and the indentation)
```python
if finding["category"] == "PASS":     # == means "is equal to"
    print("test passed")
elif finding["confidence"] == "low":  # "else if"
    print("needs a human")
else:
    print("a real failure")
```
Comparisons: `==` equal, `!=` not equal, `>` `<` `>=` `<=`,
combine with `and` / `or` / `not`.

## Functions (def, arguments, return)
```python
def triage(filename, model="qwen2.5:7b"):   # model has a default value
    result = filename.upper()
    return result            # hands a value back to the caller

x = triage("a.log")          # call it; x now holds the returned value
```

## Strings
```python
s = "tc_handshake.log"
s.upper()                    # "TC_HANDSHAKE.LOG"
s.lower()                    # "tc_handshake.log"
s.endswith(".log")           # True
s.split("_")                 # ["tc", "handshake.log"]  (split into a list)
"a" + "b"                    # "ab"  (glue strings with +)
f"category is {finding['category']}"   # f-string: insert a value into text
```

## Loops
```python
for item in mylist:          # over a list
    ...
for i in range(5):           # 0,1,2,3,4
    ...
total = 0
for x in [1, 2, 3]:
    total = total + x        # total becomes 6
```

## List comprehension (a loop that builds a list, in one line)
```python
nums = [1, 2, 3, 4]
doubled = [n * 2 for n in nums]            # [2, 4, 6, 8]
bigs    = [n for n in nums if n > 2]       # [3, 4]  (with a filter)
```

## Files
```python
with open("logs/a.log") as f:    # open for reading; auto-closes after
    text = f.read()              # whole file into one string

with open("out.txt", "w") as f:  # "w" = write (overwrites)
    f.write("hello")
```

## JSON (text <-> dict)
```python
import json
d = json.loads('{"category": "TIMEOUT"}')   # text  -> dict
s = json.dumps({"category": "TIMEOUT"})      # dict  -> text
# read a json file:
with open("golden.json") as f:
    golden = json.load(f)        # note: load (file) vs loads (string)
```

## os (files/folders)
```python
import os
os.listdir("logs")               # list of filenames in the folder
os.path.join("logs", "a.log")    # "logs/a.log"  (safe path building)
```

## try / except (handle an error instead of crashing)
```python
try:
    x = risky_thing()
except ValueError as e:          # catch a specific error type
    print("it failed:", e)
```

## The two things that trip up C++ people
1. **No semicolons, no braces.** Blocks are defined by **indentation** (4 spaces).
   The `:` starts a block; everything indented under it is "inside."
2. **No type declarations.** You write `x = 5`, not `int x = 5`.
```python
def f(items):
    for it in items:      # indented = inside the loop
        if it > 0:        # indented more = inside the if
            print(it)     # wrong indentation = error
```
