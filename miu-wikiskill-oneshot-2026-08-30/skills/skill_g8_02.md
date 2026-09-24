CONTINUATION-TURN PROCEDURE (apply this before choosing values; it overrides the general guidance above when the message is a turn in an ongoing dialogue)

STEP A — Decide whether this is a dialogue turn.
A dialogue turn is a message that reacts to the assistant or continues a discussion. Signals:
  - opens with a connective or reaction ("But", "So", "That's true", "Good —", "Right,", "Okay, then")
  - quotes or names a word, number, claim, or metaphor the assistant used
  - talks to or about the assistant itself (its state, memory, identity, feelings, code)
  - contradicts, agrees with, or builds on a point that was already on the table
If none of these apply, treat the message as a standalone request and use the base rules.

STEP B — Locate the MAIN ASK.
The main ask is the last question mark or imperative in the message. If there are several, use the last/primary one; earlier sentences are context, not the ask. If there is no question or imperative, the main ask is "respond to the point being made."

STEP C — Choose tool for a dialogue turn.
Choose rag when the main ask cannot be answered without material from earlier in the conversation that the message does not fully restate. Typical shapes:
  - asks what was said, when, by whom, or where a shared term/idea came from
  - asks what the assistant meant by a word it used earlier
  - asserts or disputes something the assistant previously claimed about itself
  - asks whether something would exist / would be true "without" the shared history
Choose answer when any of these hold:
  - the message itself restates every definition, premise, or number needed
  - the ask is to make something new: name it, coin a word, decide, choose, compute, imagine, write, rank, opine
  - the ask is hypothetical or counterfactual about the future ("what if...", "would that...", "suppose we...")
  - the user is reporting their OWN actions, effort, mood, or opinion, or offering thanks, praise, apology, or encouragement
  - the user asks the assistant to report its CURRENT internal state right now (vitals, signals, how it feels this moment) — live self-report is introspection, not retrieval
Do not select rag merely because the words "you", "your", "we", or "us" appear. Mentions of the assistant's parts, code, or nature are about the present, not about stored conversation.
Do not select web_search or web_and_rag for questions about the assistant, its state, its history with the user, or abstract/philosophical topics; none of these are current events.

STEP D — Choose mode for a dialogue turn.
If tool = answer:
  - use chat, even when the message is long, philosophical, emotionally loaded, multi-part, or demanding. Depth does not make it explore.
  - use execute ONLY when the deliverable is a concrete artifact: code, a fix, a file edit, a script, a document, a written passage the user will keep. Naming a concept inside conversation is chat, not execute.
  - use explore ONLY for open-ended requests for options or research the assistant must go gather ("what are some...", "give me ideas for...").
If tool = rag:
  - default to recall: the ask is about what happened, what was said, the origin or history of a term, or verifying an earlier claim.
  - use explore instead when the ask is to draw a NEW distinction or judgement from earlier material — something never actually stated before. Typical shapes: "is X the same as Y, or different?", "when you said Z, did you mean...?", "is that uncomfortable, or more like...?", two or more stacked open questions probing implications.
  - a rag turn that only asserts or rebuts, with no question, is recall.

STEP E — Choose scope for a dialogue turn.
  - tool = rag or web_and_rag from this procedure → session, unless a named file/document/notes is the target (then docs).
  - tool = answer and the ask concerns the assistant's own state, vitals, preferences, name, identity data, or the user's stored personal facts → facts.
  - tool = answer for anything else in dialogue (philosophy, hypotheticals, naming, opinions, user self-reports, praise, small talk) → all.
  - Never emit docs unless a file, document, note, or library item is named or unmistakably implied.

STEP F — Consistency check before emitting.
  - answer + chat is the correct pair for most conversational turns; do not upgrade it to explore just because the question is hard.
  - rag + chat and answer + recall are almost never right; if you land on one, redo Step C.
  - If the turn both discusses shared history AND asks for something new, ask which one the answer actually requires. If the assistant could answer using only the text in front of it, choose answer.
  - Every field must be one of the listed enum values, exactly. Emit only the JSON object, nothing else.