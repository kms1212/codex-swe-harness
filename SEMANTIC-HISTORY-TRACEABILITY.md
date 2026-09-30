# Semantic history traceability, v0 selection reconstruction

The baseline is the semantic-history audit supplied for this change: `6217170` removed the earlier global SWE guidance and the software-evolution and verification references. Later work strengthened completion and delegation, while selection and economy remained weaker or local. This record tracks the resulting current owners. “Installed” means the row is carried by the managed `common.md` fragment or installed runtime; the final installation revision and fresh-session observations must be checked separately.

| Audited requirement | Audit status | Final owner and scope | Modality | Enforcement mechanism and source | Installed |
| --- | --- | --- | --- | --- | --- |
| Necessary change completeness | Preserved | Global SWE instruction | Required | Parent obligation and integration gate; `runtime/instructions/common.md`, `completion.py` | Yes |
| Exclude unrelated change | Weakened | Global SWE instruction | Stop | Request and scope judgment; `runtime/instructions/common.md` | Yes |
| Activity versus progress | Weakened | Global SWE instruction and runtime selector | Stop | Current-value selection and completion; `common.md`, `optimization.py` | Yes |
| Work and evidence reuse | Weakened | Global SWE instruction and runtime selector | Stop | Identity-matched PASS reuse; `common.md`, `optimization.py` | Yes |
| Affected-scope verification | Weakened | Global SWE instruction and runtime selector | Conditional | Required scope identity comparison; `common.md`, `optimization.py`, `completion.py` | Yes |
| Expensive action repetition | Weakened | Global SWE instruction and runtime selector | Stop | `select --proposed` reuses identical PASS; `common.md`, `cli.py`, `optimization.py` | Yes |
| Review routing | Modality changed | Global SWE instruction and Stop routing | Conditional | Current candidate path/risk routing; `common.md`, `always_on.py`, `review.py` | Yes |
| Test selection restraint | Moved to wrong scope | Global SWE instruction | Conditional | Stable contract and protection gap judgment; `common.md` | Yes |
| Existing protection reuse | Dropped/weak | Global SWE instruction | Stop | Existing test/type/schema/constraint check selection; `common.md` | Yes |
| Stable-contract test philosophy | Moved to wrong scope | Global SWE instruction | Conditional | New durable test only for uncovered material risk; `common.md` | Yes |
| Root cause | Preserved, weak globally | Global SWE instruction | Required | Owning-layer repair; `common.md` | Yes |
| Workaround policy | Dropped | Global SWE instruction | Conditional | External/uncontrollable or evidenced unavailable direct repair; `common.md` | Yes |
| Semantic ownership | Moved to wrong scope | Global SWE instruction | Required | Recomposition and instruction-state gate; `common.md`, `instructions.py` | Yes |
| Information lifetime | Moved to wrong scope | Global SWE instruction | Required | Temporary ledger versus durable contract owner; `common.md` | Yes |
| Request fidelity | Weakened globally | Global SWE instruction and ledger | Required | Actor/object/source/scope/operation/authority preservation; `common.md`, `core.py` | Yes |
| Completion evidence | Preserved/strengthened | Runtime completion gate | Required | Scope PASS and obligation refs; `completion.py` | Yes |
| Delegated-result consumption | Preserved/strengthened | Runtime lifecycle and completion gate | Required | Return, integration, consumption; `always_on.py`, `completion.py` | Yes |
| Consumer verification | Preserved/strengthened | Runtime completion gate | Required | Consumer-point PASS; `completion.py`, `instructions.py` | Yes |

The repository root `AGENTS.md` now owns only harness development facts. The managed `common.md` owns general SWE behavior. OS fragments own OS-specific execution rules. The ledger’s completion state holds declared required evidence, authority holds permitted capabilities, and `action_selection` records conditional and stop/economy choices. Selection can reduce work but cannot waive a declared completion obligation.
