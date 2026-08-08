# ASSERTION (SVA) failures

## Symptoms in the log
- "Assertion ... failed" / "assert failed"
- "Error: assert failed in scope ... at time ..."
- a named property firing (e.g. no_overflow_when_full)

## Common root causes
- RTL genuinely violated the property (a real design bug)
- the assertion itself is wrong / too strict (a checker bug)
- a protocol/timing corner the design wasn't built for

## Typical first things to check
- read the property: what condition did it assert must hold?
- the time + scope of the failure — what was driving those signals then?
