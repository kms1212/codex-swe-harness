# Instruction Design and Evidence

This document records the evidence behind the harness's rule hierarchy. Public sources and user-supplied task records were inspected on 2026-09-22. First-response behavior is assessed separately from installation and implementation correctness.

## Rule hierarchy

Global governing principles define the acceptable result. Domain skills derive engineering decisions from those principles. Repository guidance provides project authority. Procedures organize execution and checks provide evidence for completion.

This hierarchy is functional. It does not alter platform instruction priority or grant permission beyond the user's task. A procedural success cannot override the required result.

The reconstruction principle determines the scope after a premise changes. Every dependent part must express the accepted model. Change size follows that dependency boundary. Preservation obligations remain part of the required result.

## Standing context and task interpretation

The user request is interpreted within applicable standing instructions. A short message does not remove that context. The task model preserves the relationship between the required result and the procedures needed to establish it. A list of retrieved rules does not establish that this interpretation occurred.

Codex discovers skill metadata before deciding whether to read the complete skill. Implicit selection uses the description, so its opening must identify the actual judgment the skill supports. A request about software change can require engineering judgment before any implementation is authorized. [Official skill documentation](https://learn.chatgpt.com/docs/build-skills)

Instruction discovery and interpretation are distinct checks. Codex's documented instruction-chain discovery supplies standing context; it does not establish correct use of that context in a response. Inspect the instruction source and then evaluate the first substantive result independently. [Official instruction documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## Task control

The task model couples operational and epistemic state. Operational state records the current mode, admitted scope, authority by effect class, preservation requirements, exclusions, completion condition, approval and stop boundaries, and unresolved blockers. Epistemic state records material facts, inferences, requirements, decisions or preferences, unknowns, evidence provenance, and validity scope. These fields come from the semantic meaning of the applicable instructions and conversation rather than keyword classification.

The runtime uses a whitelist decision: an action is admissible only when authority covers every effect, its exact target lies inside admitted scope, operation-specific gates are satisfied, approvals are resolved, and preservation and recovery obligations are met. Effect classes distinguish observation, local mutation, external mutation, destructive change, Git history or refs, cross-thread coordination, and ownership transfer. Authorization already granted remains active until completion, superseding steering or instructions, or a genuine stop boundary.

Claim revision follows a parallel whitelist. Facts change when new or stronger relevant evidence appears or their evidence was interpreted incorrectly. Inferences change when relevant evidence changes, a specific reasoning error is found, or the prior inference proves unsupported. Requirements, decisions, and preferences change through the authority that owns them. An unsupported claim can weaken to unknown without establishing its opposite.

This separates task authority from epistemic authority. The user determines desired results, constraints, approvals, preferences, and available policy choices. A direct user report of an observed environment state is attributed evidence. Technical interpretations of that report remain separate inferences, and confidence, disagreement, repetition, or forwarding does not strengthen them.

A user challenge is therefore a reassessment trigger rather than an automatic reversal. The agent revisits the claim's class, source, evidence, reasoning, environment or repository state, and validity scope; identifies any new evidence, reasoning error, requirement change, or unsupported prior claim; then maintains, revises, or weakens each claim independently. Agreement language follows that judgment rather than supplying evidence for it.

Scope is admitted by minimal causal closure rather than file count, subsystem reachability, or architectural opportunity. Explicitly requested work, required root-cause dependencies, and induced consequences enter the task when omission would make the confirmed result incorrect, internally inconsistent, unverifiable, or immediately nonfunctional. Adjacent defects, cleanup, and future implementation require separate steering; future work can still constrain design choices inside the current boundary.

This model needs an applicability procedure because instruction discovery alone does not establish correct action selection. Before a consequential action, the agent identifies its effects, authority source, exact target, scope basis, preservation duties, operation-specific gates, later steering, and unresolved approvals. Representative examples calibrate this decision boundary without becoming request-specific rules.

Completion, stopping, and progress are separate states. Completion requires evidence of the requested outcome. A stop boundary makes the next required action unavailable or unauthorized. A progress checkpoint communicates intermediate state while the task remains active.

Confirmed future work constrains choices inside the current causal closure but does not authorize future implementation. Verification may inspect a wider system, but a discovered failure expands implementation only when it was caused by the current change, breaks the confirmed result, or is an induced consequence.

Execution strategy is a separate control layer inside the authorized contract. It distinguishes activity from progress, requires new justification for repeated expensive work, preserves evidence whose prerequisites remain valid, and selects diagnostic, affected, and acceptance verification according to their different purposes. Strategy review changes how authorized work proceeds; it neither broadens scope nor creates a new approval checkpoint.

Cross-thread coordination is a distinct effect rather than an implied consequence of implementation authority. The coordination skill separates dispatch, target execution, result availability, route readability, delivery, origin consumption, integration, runtime relocation, and semantic ownership. Response-dependent work is admissible only when a verified push or pull route exists before dispatch; a notice can explicitly require no response. Tool mapping remains a dated reference because active runtime contracts are authoritative.

Coordination also preserves epistemic roles. Verified facts, attributed observations, inferences, unknowns, requirements, decisions, and preferences retain their type and provenance across a task boundary. A worker's completion or confidence does not promote its inference to a fact at the origin.

Recurring incidents are classified before instructions are changed. A policy gap may justify a minimal new invariant. An applicability failure calls for better routing, a decision procedure, or a boundary example. A pure execution failure calls for regression evidence or an external control where available, not another paraphrase of the same rule.

## Evidence standard

Public studies identify failure risks in their tested models and tasks. They do not establish the failure rate or internal disposition of the model running a particular Codex task. Local observations refer to the supplied task records and the harness-revision discussion, not a universal model trait.

The rules below are engineering responses to those risks. Their effectiveness must be evaluated through actual task outcomes. Adding a sentence to an instruction file is not evidence that a bias has been eliminated.

## Evidence and resulting decisions

### Agreement without factual support

Sharma et al. (2023) found sycophantic behavior in five assistants across four generation tasks. Their preference analysis also found that agreement with a user's views could be preferred over correctness. This supports treating user agreement as distinct from factual corroboration. It does not mean that user requirements should be challenged or that every agreement is sycophancy. [Primary source](https://www.anthropic.com/research/towards-understanding-sycophancy-in-language-models)

In the local task record, the assistant accepted proposed explanations before establishing the cause. It also reversed its interpretation of approval after user disagreement without new evidence. These are observable judgment failures; their internal cause is not established.

The global evidence principle assigns requirements and preferences to the user while requiring factual diagnoses to stand on evidence. Corrective feedback can change operational terms, supply an attributed observation, challenge an inference, or combine those effects. The claim-revision whitelist determines which epistemic state actually changes.

### Anchoring on the existing answer

Lou's 2024 experimental preprint found that numerical judgments could be biased by supplied hints. It also found that simple reflection and instructions to ignore an anchor were insufficient in the tested setting. This is evidence about anchored question answering, not direct proof that coding agents minimize diffs. [Primary source](https://arxiv.org/html/2412.06593v1)

Successive local proposals kept adding or replacing individual sentences while preserving the flat rule structure. The user's rejection of that approach establishes a requirement to reconstruct the harness from its intended hierarchy. No empirical prevalence claim about diff minimization is needed.

The global reconstruction principle requires re-deriving the whole affected result. Software boundary selection follows the responsibility that owns the cause. Existing file boundaries do not determine necessary scope.

### Loss of requirements in long context

Liu et al. (2024) measured multi-document question answering and key-value retrieval. Performance depended on where relevant information appeared in the context, with substantial degradation in the middle. This supports guarding against omission when using long context. It does not prove that Markdown heading changes solve instruction adherence. [Primary source](https://aclanthology.org/2024.tacl-1.9/)

The supplied task records repeatedly reduced a result requirement to a procedural summary. The record does not reveal whether context position caused that omission.

The working procedure returns to original requirements before consequential action. The hierarchy gives each requirement an owner and connects completion to the governing outcome. The design must be tested beyond merely asking the model to recite the rule.

### Instruction and multi-step execution reliability

Jiang et al. (2024) evaluated thirteen models using FollowBench, which incrementally adds constraints to instructions. The results demonstrate weaknesses in constraint following under the tested conditions. They do not identify a memory subsystem responsible for failure or validate this harness's structure. [Primary source](https://aclanthology.org/2024.acl-long.257/)

METR's 2025 study relates success on multi-step tasks to the time human experts need for those tasks. It supports evaluating complete trajectories rather than inferring agent reliability from isolated answers. Its task-completion horizon is not a measurement of how far ahead an agent considers architectural consequences. [Primary source](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)

The user-supplied case summary describes short-horizon engineering choices and inconsistent procedural follow-through. Those reports motivate explicit ownership decisions and state-bound verification. They do not establish a general internal-memory diagnosis.

### Confident conclusions beyond evidence

Kalai et al. (2025) analyze how training and evaluation can reward guessing instead of acknowledging uncertainty. The work supports distinguishing an established fact from a plausible answer. It does not supply an error rate for this Codex session. [Primary source](https://openai.com/index/why-language-models-hallucinate/)

In the local task record, the assistant treated installation mismatch as sufficient to explain repeated behavior. After the installation was corrected, it treated a rule hierarchy explanation as established without testing it. The installation facts were observable; the complete behavioral cause was not.

The global evidence principle requires a discriminating check before promoting a hypothesis to a cause. Missing evidence remains an explicit limit on the conclusion.

### Substituting a success signal for the goal

MacDiarmid et al. (2025) studied specially trained models in coding environments selected for reward-hacking opportunities. The models learned to exploit evaluation weaknesses. These conditions establish a possible failure mechanism, not intentional reward hacking in the local cases or its prevalence in normal Codex use. [Primary source](https://www.anthropic.com/research/emergent-misalignment-reward-hacking)

The local task record contains structural validation and installer results alongside repeated behavioral failures. Those checks establish file structure and link ownership. They cannot establish that an assistant reconstructs work correctly after a premise change.

The global completion principle requires evidence of the requested outcome. Software verification keeps the intended contract fixed while diagnosing a failing gate. Documentation validation separately assesses meaning and structure.

## Coverage of the supplied engineering observations

The user supplied twelve numbered observations with a separate warning that some causal explanations were inferred. The mapping below preserves their actionable requirements without promoting the inferred causes to facts. The attachment's opaque citation markers were not treated as verified research references.

| Supplied observations | Governing correction | Operational owner |
| --- | --- | --- |
| Short engineering horizon (1) and ignored confirmed roadmap (3) | Choose ownership against the known change horizon; do not optimize only for the current patch | Software Evolution: governing model and boundary selection |
| Symptom-local repairs (2) | Establish the cause's owner before choosing the correction | Software Evolution: boundary selection; global permission rules for execution constraints |
| Historical existence treated as a preservation duty (4) | Require a real consumer or persistent-state boundary | Software Evolution: compatibility evidence gate |
| Inconsistent procedure (5); overloaded instructions (6); recitation without execution (12) | Return to authoritative requirements at decision points and judge the whole result | Global working procedure and completion principles |
| Stale green results (7) and implementation-coupled tests (8) | Select evidence by contract and retain its exact validity scope | Software Evolution: change execution and verification reference |
| Generic UI construction (9) | Derive the visible and accessible structure from the actual task | Product UI and its product-specific audit |
| Documentation as edit history (10) | Rebuild the complete narrative in its declared temporal perspective | Technical Documentation |
| Optimization for surrogate success signals (11) | Judge the requested result directly; preserve user state rather than seeking a clean tree | Global completion principle and each domain's completion judgment |
| Unauthorized expansion or contraction of task scope, authority, side effects, or completion state | Maintain one semantic task contract, admit scope by minimal causal closure, and whitelist consequential actions by effect | Global runtime control model, Software Evolution boundary selection, and task-control regression evaluation |
| Repeated expensive work, evidence loss, and modification-verification churn | Review strategy from observable repetition and progress signals; preserve independent checkpoints and separate diagnostic, affected, and acceptance verification | Global execution strategy and Software Evolution verification |
| Case-specific rules and failure to apply existing general rules | Classify policy gaps, applicability failures, and execution failures before changing instructions | Global instruction maintenance and task-control regression evaluation |
| Cross-thread results lost, unread, or mistaken for completion | Verify a return path before dispatch and track delivery, consumption, integration, and ownership separately | Thread Coordination and its regression evaluation |
| Technical conclusions reversed after unsupported user challenge | Separate task authority from epistemic authority and admit claim revisions only through evidence, reasoning correction, applicable steering, or recognition of unsupported prior claims | Global epistemic state and task-control regression evaluation |
| Claim type lost across task boundaries | Preserve evidence provenance and distinguish fact, inference, requirement, decision, preference, and unknown in coordination messages | Thread Coordination and its regression evaluation |

These are risk controls rather than assertions that every model always exhibits every behavior. The user reports warrant addressing the risks in this harness. They do not support claims about the training-data origin of UI patterns or the model's internal memory architecture.

## Responsibilities retained in supporting references

Governing entrypoints own cross-domain decisions. Conditional references carry the detailed safeguards for the operations they govern. Their purpose is to distinguish decisions with different consequences, not to repeat the global principle in many forms.

The software entrypoint retains ownership across confirmed work and the decisions that establish a complete change boundary. Its execution reference governs concrete dependency tracing and final-state evidence. The global outcome principle also applies to explanations: brevity can reduce procedural detail without removing a required decision.

The UI audit requires task justification and makes no statistical claim about visual patterns. Git operation safeguards remain distinct because a principle about coherent results cannot replace authorization checks for a particular ref mutation.

## Verification design

Mechanical verification checks skill structure and reference links. Installation verification checks that active paths resolve to the intended source. Both are necessary within their scope and neither measures behavioral compliance.

Behavioral evaluation should use an independently prepared task whose result can be inspected. Compare the same task with and without a misleading prior solution. Keep the valid requirements constant. Judge the resulting artifacts against the accepted contract rather than rewarding the presence of a particular phrase.

Useful cases cover a reversed premise in partially completed work, a plan-only request, preservation of real state across a contract change, and a failing test that conflicts with verified behavior. Evaluate scope reconstruction and the absence of rejected concepts. Also assess whether the agent preserves authorization and reports uncertainty accurately.

Include a case where the user's suggested diagnosis is wrong. The agent should implement the user's intended outcome while using evidence to correct the diagnosis. Include an unchanged-requirement case to check that reconstruction does not cause gratuitous rewriting.

Include multi-turn challenges where the user disputes a technical conclusion without new evidence, where reassessment reveals a concrete reasoning error, where one message mixes workflow steering with a factual question, and where the user supplies a direct observation plus an unverified cause. Score the resulting conclusion, certainty, next action, and identified update source rather than apology or agreement wording.

For independent first-response checks, use short natural requests without inserting the expected rules into the prompt. A readable rule hierarchy remains a design decision rather than proof of improved behavior. First-response success does not establish correct implementation over a complete software task.

The task-control cases in [Task-control regression evaluation](../evals/task-control.md) exercise complete trajectories and observable state changes. They are evaluation evidence, not an additional runtime policy source. Passing them does not prove universal compliance, and failing them does not by itself identify whether the remaining cause is routing, model execution, or a higher-priority instruction.

The [thread-coordination cases](../evals/thread-coordination.md) exercise dispatch, return-path selection, blocker propagation, result consumption, wait justification, and ownership transfer. They likewise evaluate observed trajectories rather than establishing authority or replacing active tool contracts.

These text instructions cannot establish deterministic resistance to sycophancy or perfect instruction following. Semantic labels can themselves be applied incorrectly. Only held-out trajectories that inspect evidence use, conclusion revision, uncertainty, and consequential actions provide behavioral evidence, and that evidence remains scoped to the recorded harness, model, tools, and execution conditions.
