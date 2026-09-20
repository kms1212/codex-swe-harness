# Korean Technical Writing

Use this reference for Korean technical documentation after document semantics and general prose have been audited.

The goal is accurate, direct, natural Korean. Do not translate an English surface structure sentence by sentence. Reconstruct the meaning according to Korean syntax, discourse, and the project's established terminology.

The patterns below are review signals, not grammatical prohibitions. Do not rewrite a correct technical expression merely to satisfy a stylistic preference.

## Prefer direct predicates

When meaning remains accurate, prefer a direct verb over an abstract noun combined with a generic verb.

Examples:

- `검증을 수행합니다` → `검증합니다`
- `요청에 대한 처리를 진행합니다` → `요청을 처리합니다`
- `데이터의 저장을 수행합니다` → `데이터를 저장합니다`

Keep nominal technical terms when they name a real domain concept or when rewriting would reduce precision.

## Use voice deliberately

Prefer active voice when the actor is known and ownership matters.

Use passive voice when:

- the actor is irrelevant;
- the resulting state is the subject;
- a contract is more accurate in passive form;
- naming an actor would require speculation.

Do not invent a subject merely to eliminate passive voice. Do not hide a responsible component behind passive wording when the actor is material to the contract.

## Limit habitual possibility expressions

Use `수 있습니다` and equivalent constructions when capability, permission, or possibility is the actual claim.

When describing deterministic behavior, state the behavior directly. Remove possibility expressions that only soften an otherwise factual sentence.

## Replace vague abstractions

Review generic nouns such as:

- 부분;
- 측면;
- 관점;
- 경우;
- 형태;
- 방식;
- 구조;
- 단계;
- 요소;
- 기능;
- 처리;
- 관리;
- 지원;
- 활용.

Keep them when they name the intended concept. Replace them when a specific component, action, condition, or result would be clearer.

## Remove unsupported evaluation

Do not use adjectives equivalent to efficient, flexible, powerful, intuitive, smooth, enhanced, optimized, convenient, smart, or stable without a concrete basis.

Describe the observable property instead: fewer steps, bounded latency, a preserved invariant, supported input, automatic recovery, or another verifiable characteristic.

## Control connective expressions

Do not use `또한`, `특히`, `따라서`, `이를 통해`, `이에 따라`, `한편`, `즉`, `결과적으로`, `이러한`, or similar expressions as automatic paragraph glue.

Keep them when they clarify a real relationship between claims. Otherwise place the claims in a direct sequence or restructure the paragraph.

## Shape Korean sentences

Split a sentence when independent claims, conditions, exceptions, and results have accumulated through repeated `-하며`, `-하고`, `-하여`, `-하면서`, commas, or equivalent connectors.

Do not enforce uniformly short sentences. Keep information together when the relationship is easier to understand in one sentence.

Review long modifier chains. Make clear:

- who acts;
- what changes;
- which condition applies;
- which noun a modifier describes.

Repeat a subject when ownership or contract would otherwise become ambiguous. Omit it when context is clear and repetition makes the Korean unnatural.

## Preserve terminology

Use one established term for one technical concept. Do not alternate between Korean synonyms or Korean and English terms merely for stylistic variety.

Follow repository terminology before inventing a translation. Keep a standard English technical term when translating it would conflict with domain usage. Use natural Korean when it preserves the same meaning.

Avoid unnecessary mixed constructions such as English nouns embedded in Korean when the project already has a stable Korean or English term.

## Avoid translation-shaped prose

Review:

- English-style noun chains;
- unnecessary possessive constructions;
- modifiers kept in English order;
- repeated pronouns or subjects copied from the source;
- long prepositional structures converted mechanically;
- bureaucratic expressions that obscure the actor or action.

Translate the intended meaning and paragraph function, not each source-language token.

## Korean audit

Read the completed Korean prose aloud or at natural reading speed and ask:

1. Does the sentence sound written in Korean rather than converted into Korean?
2. Is the actor explicit where ownership matters?
3. Can a direct verb replace a nominalized construction?
4. Does passive voice serve the meaning?
5. Is possibility the real claim?
6. Can a vague noun be replaced with the actual object or action?
7. Does each connective express a real relationship?
8. Is the modifier scope unambiguous?
9. Does each term refer to one stable technical concept?
10. Does every evaluative expression have evidence?

Preserve correctness over stylistic smoothness when the two appear to conflict.
