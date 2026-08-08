"""
gen_lint.py — generate synthetic lint warning files for testing.

Each file = one source file's lint output, like you'd get from running
clang-tidy or a VCS compile with -Wall on a C++/RTL codebase.

Run once:  python gen_lint.py
Produces:  lint_warnings/*.lint
"""

import os

OUTDIR = "lint_warnings"
os.makedirs(OUTDIR, exist_ok=True)

# Each entry: (filename, list of warning lines)
# Patterns are realistic C++/EDA lint output shapes.
FILES = {

    # -----------------------------------------------------------------------
    # BUG — uninitialized variable read before write
    # -----------------------------------------------------------------------
    "sim_scheduler.cpp.lint": """\
sim_scheduler.cpp:42:12: warning: variable 'timeout_cycles' is used uninitialized [-Wuninitialized]
    if (timeout_cycles > MAX_CYCLES) return false;
            ^~~~~~~~~~~~~~
sim_scheduler.cpp:38:9: note: 'timeout_cycles' declared here
    int timeout_cycles;
        ^~~~~~~~~~~~~~
""",

    # -----------------------------------------------------------------------
    # BUG — missing return value in non-void function
    # -----------------------------------------------------------------------
    "event_queue.cpp.lint": """\
event_queue.cpp:87:1: warning: control reaches end of non-void function [-Wreturn-type]
}
^
event_queue.cpp:65:5: note: in function 'int EventQueue::pop()'
    int EventQueue::pop() {
    ^
""",

    # -----------------------------------------------------------------------
    # BUG — undeclared function prototype used
    # -----------------------------------------------------------------------
    "dbs_engine.cpp.lint": """\
dbs_engine.cpp:114:18: warning: implicit declaration of function 'compute_wakeup_mask' [-Wimplicit-function-declaration]
    int mask = compute_wakeup_mask(proc_id, sensitivity_list);
               ^~~~~~~~~~~~~~~~~~~~
dbs_engine.cpp:114:18: note: did you mean 'compute_wakeup_map'?
""",

    # -----------------------------------------------------------------------
    # REVIEW — unused variable (could be bug or intentional placeholder)
    # -----------------------------------------------------------------------
    "vsp_pass.cpp.lint": """\
vsp_pass.cpp:203:9: warning: unused variable 'alias_count' [-Wunused-variable]
    int alias_count = 0;
        ^~~~~~~~~~~
vsp_pass.cpp:231:9: warning: unused variable 'debug_mode' [-Wunused-variable]
    bool debug_mode = false;
         ^~~~~~~~~~
""",

    # -----------------------------------------------------------------------
    # STYLE — naming convention violation
    # -----------------------------------------------------------------------
    "memory_pool.cpp.lint": """\
memory_pool.cpp:17:8: warning: variable 'MemPool_Size' does not follow naming convention (use snake_case) [readability-identifier-naming]
    int MemPool_Size = 4096;
        ^~~~~~~~~~~~
memory_pool.cpp:55:6: warning: function 'AllocateBlock' does not follow naming convention (use snake_case) [readability-identifier-naming]
    int AllocateBlock(size_t sz) {
        ^~~~~~~~~~~~~
""",

    # -----------------------------------------------------------------------
    # IGNORE — long line / formatting suggestion
    # -----------------------------------------------------------------------
    "netlist_parser.cpp.lint": """\
netlist_parser.cpp:301:121: warning: line exceeds 120 characters [whitespace/line_length]
    auto result = netlist_db.find_module(module_name)->get_port_list()->filter_by_direction(PORT_INPUT)->to_vector();
                                                                                                                        ^
netlist_parser.cpp:418:1: warning: consider breaking this function into smaller units, function exceeds 80 lines [function/length]
    void NetlistParser::elaborate_hierarchy() {
    ^
""",

}

for fname, content in FILES.items():
    path = os.path.join(OUTDIR, fname)
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote {path}")

print(f"\n{len(FILES)} lint warning files generated in {OUTDIR}/")
