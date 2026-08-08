# COMPILE / elaboration failures

## Symptoms in the log
- Error-[SE] syntax error, "token is ';'"
- "make: *** [compile] Error 1"
- simulation never starts (no UVM_INFO RNTST "Running test" line)

## Common root causes
- missing semicolon, unmatched begin/end, bad port connection
- a typo in a signal, module, or package name
- a file not added to the compile list / wrong order

## Typical first things to check
- the exact file and line in the Error-[SE] message
- whether the module even elaborated, or died during parse
