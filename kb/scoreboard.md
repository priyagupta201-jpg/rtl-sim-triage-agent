# SCOREBOARD / data-mismatch failures

## Symptoms in the log
- UVM_ERROR [MISMATCH], "exp= ... got= ..."
- compare/predictor mismatch reported from the scoreboard
- often a UVM_FATAL [TOO_MANY_ERR] once max_quit_count is hit

## Common root causes
- RTL computes the wrong result (a real design bug)
- reference model / predictor is wrong (a testbench bug)
- timing/sampling off — comparing at the wrong cycle

## Typical first things to check
- is the expected value (predictor) actually correct?
- which operands produced the mismatch — pattern or one-off?
