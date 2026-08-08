# TIMEOUT failures

## Symptoms in the log
- [TIMEOUT] / "Global timeout reached" messages
- simulation never hits a natural $finish
- a UVM_WARNING about stalling / "still waiting" before the timeout

## Common root causes
- a handshake where req is asserted but ack never returns (deadlock)
- a missing or wrong reset, leaving an FSM stuck
- waiting on an event/semaphore that's never triggered

## Typical first things to check
- is the ack/grant path actually driven?
- is the FSM reaching the state that should respond?

