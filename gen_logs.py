"""
gen_logs.py — Generate synthetic (but realistic) VCS regression logs.

These mimic the kind of output Synopsys VCS produces during compile,
elaboration, and simulation. They are FAKE — no real design, no real
license needed — but the failure signatures are the real ones you'd
triage in a regression. The triage agent reads these exactly as it
would read your real overnight regression dir.

Run:  python gen_logs.py
"""

import os

LOGS = {
    # 1. Clean compile + elaboration, but a UVM_FATAL at runtime.
    "tc_alu_smoke.log": """\
Chronologic VCS simulator copyright 1991-2024
Contains Synopsys proprietary information.
Compiler version V-2024.03; Runtime version V-2024.03;  May 29 02:14 2026

UVM_INFO @ 0: reporter [RNTST] Running test alu_smoke_test...
UVM_INFO testbench/env/alu_scoreboard.sv(142) @ 100: uvm_test_top.env.sb [SB] Comparing txn id=0
UVM_INFO testbench/env/alu_scoreboard.sv(142) @ 220: uvm_test_top.env.sb [SB] Comparing txn id=1
UVM_ERROR testbench/env/alu_scoreboard.sv(151) @ 340: uvm_test_top.env.sb [MISMATCH] ADD result mismatch: exp=0x0000_00ff got=0x0000_00fe operands a=0x80 b=0x7f
UVM_FATAL testbench/env/alu_scoreboard.sv(160) @ 340: uvm_test_top.env.sb [TOO_MANY_ERR] Stopping: error count reached max_quit_count=1

--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :   58
UVM_WARNING : 0
UVM_ERROR :   1
UVM_FATAL :   1
$finish called from file "uvm_root.svh", line 512.
$finish at simulation time              340
""",

    # 2. SystemVerilog Assertion (SVA) failure.
    "tc_fifo_overflow.log": """\
Chronologic VCS simulator copyright 1991-2024
Compiler version V-2024.03; Runtime version V-2024.03;  May 29 02:18 2026

UVM_INFO @ 0: reporter [RNTST] Running test fifo_stress_test...
"Assertion no_overflow_when_full" failed at time 1450
    File: rtl/sync_fifo.sv  Line: 88
    rd_en && wr_en asserted while fifo_full==1, depth=16
"Error: assert failed in scope top.dut.u_fifo at time 1450"
UVM_ERROR @ 1450: uvm_test_top [SVA] Assertion failure propagated to scoreboard
$finish at simulation time             1450
** Report counts by severity
UVM_ERROR :   1
UVM_FATAL :   0
""",

    # 3. Compile error — never reaches simulation.
    "tc_axi_burst.log": """\
Chronologic VCS simulator copyright 1991-2024
Parsing design file 'rtl/axi_master.sv'

Error-[SE] Syntax error
  Following verilog source has syntax error :
  "rtl/axi_master.sv", 214: token is ';'
      assign awvalid = (state == ADDR_PHASE) ? 1'b1 : 1'b0
                                                          ^
  Expected ';' before 'endmodule'

Error-[SE] Syntax error
  "rtl/axi_master.sv", 217: token is 'endmodule'

1 error
make: *** [compile] Error 1
""",

    # 4. Timeout / hang — simulation never reaches $finish.
    "tc_handshake.log": """\
Chronologic VCS simulator copyright 1991-2024
Compiler version V-2024.03; Runtime version V-2024.03;  May 29 02:31 2026

UVM_INFO @ 0: reporter [RNTST] Running test req_ack_handshake_test...
UVM_INFO testbench/seq/handshake_seq.sv(40) @ 50: uvm_test_top.env.agt.seqr [SEQ] Driving req=1, waiting for ack
UVM_WARNING testbench/seq/handshake_seq.sv(48) @ 100050: uvm_test_top.env.agt.seqr [STALL] No ack after 100000 ns, still waiting
UVM_FATAL @ 5000000: reporter [TIMEOUT] Global timeout reached (set_global_timeout=5ms). Test did not complete. Likely deadlock: req asserted, ack never returned.
$finish at simulation time         5000000
** Report counts by severity
UVM_FATAL :   1
""",

    # 5. X-propagation / unknown value issue.
    "tc_reset_release.log": """\
Chronologic VCS simulator copyright 1991-2024
Compiler version V-2024.03; Runtime version V-2024.03;  May 29 02:40 2026

UVM_INFO @ 0: reporter [RNTST] Running test reset_release_test...
Warning-[STASKW_CO] $display/$write encountered 'x'
RTL_X_CHECK rtl/ctrl_fsm.sv(73) @ 15: signal 'next_state' is X after reset deasserted at time 12
UVM_ERROR testbench/env/ctrl_monitor.sv(95) @ 20: uvm_test_top.env.mon [X_PROP] state register propagated X to output 'grant', sampled grant=x
UVM_ERROR testbench/env/ctrl_monitor.sv(95) @ 60: uvm_test_top.env.mon [X_PROP] grant still X, downstream comparison invalid
$finish at simulation time              200
** Report counts by severity
UVM_ERROR :   2
UVM_FATAL :   0
""",

    # 6. A genuinely PASSING test — the agent must NOT flag this.
    "tc_decoder_basic.log": """\
Chronologic VCS simulator copyright 1991-2024
Compiler version V-2024.03; Runtime version V-2024.03;  May 29 02:44 2026

UVM_INFO @ 0: reporter [RNTST] Running test decoder_basic_test...
UVM_INFO testbench/env/dec_scoreboard.sv(120) @ 900: uvm_test_top.env.sb [SB] All 64 transactions matched
UVM_INFO @ 905: reporter [TEST_DONE] *** TEST PASSED ***
** Report counts by severity
UVM_INFO :   71
UVM_WARNING : 0
UVM_ERROR :   0
UVM_FATAL :   0
$finish at simulation time              905
""",
}


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(out_dir, exist_ok=True)
    for name, text in LOGS.items():
        path = os.path.join(out_dir, name)
        with open(path, "w") as f:
            f.write(text)
        print(f"wrote {path} ({len(text)} bytes)")
    print(f"\n{len(LOGS)} synthetic VCS logs written to {out_dir}/")


if __name__ == "__main__":
    main()
