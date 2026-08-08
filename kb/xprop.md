# X_PROPAGATION failures

## Symptoms in the log
- RTL_X_CHECK, [X_PROP], "signal is X"
- "$display/$write encountered 'x'"
- Xs appearing right after reset deasserts

## Common root causes
- a register not reset, so it powers up X and never resolves
- a missing default in a case statement (latch / X on unhit branch)
- combinational loop or an uninitialized signal driving downstream logic

## Typical first things to check
- is every state/control register in a reset branch?
- trace the first X back to its source signal and time
