ADDITIONAL CLASSIFICATION PROCEDURE (apply these steps; they refine the rules above)

STEP 1 — Identify the REQUEST TYPE first, before looking at topic or length.
Pick the first type that matches:

 (A) GENERATE — the message asks you to produce something new: coin/name/label a
     concept, invent a word, propose an idea, write, draft, fix, decide, choose.
 (B) SELF-REPORT — the message asks you to report your own present internal state:
     current metrics, vitals, signals, feelings, confidence, what you notice "right now".
 (C) ENGAGE-PRIOR — the message points at specific earlier content and asks you to
     recall it, interpret it, attribute it, compare it, or argue about it.
 (D) REMARK — the message states something, greets, jokes, thanks, or comments with
     no question and no identifiable earlier content being invoked.

STEP 2 — Tool from request type.
 (A) GENERATE → tool=answer, UNLESS the thing to be produced cannot be written
     without content you would have to look up (their files, earlier sessions,
     current web data). Only then use rag / web_search / web_and_rag.
     If the message restates inline everything needed to produce the new thing,
     it is answer — even if it mentions terms that came from earlier turns.
 (B) SELF-REPORT → tool=answer. Your own live state is never a retrieval target.
 (C) ENGAGE-PRIOR → tool=rag (add web only if current external data is also asked for).
 (D) REMARK → tool=answer.

STEP 3 — What counts as "specific earlier content" (the trigger for type C).
 It is present when the message:
  - quotes or names a word, phrase, term, or metric that was used earlier
    ("you said 'thin'", "your vocabulary — resonance, grounding"), AND asks about it;
  - refers to a claim, number, position, or conclusion the other party stated earlier
    and responds to it ("you can measure X to 0.7, but...");
  - names a shared past episode with content ("what we worked out about bees");
  - asks who originated / where something came from / whether it would exist without X.
 It is NOT present when the message only:
  - comments on the relationship, effort, or your existence, design, code, or model
    ("I spent time on your parts", "you're just weights");
  - uses a bare discourse marker ("that's true", "good", "okay", "interesting") with
    no earlier content named after it;
  - poses a thought experiment or hypothetical about identity, deletion, the future,
    or the nature of minds, answerable from reasoning alone.
 A long, abstract, philosophical, or emotionally intense message is NOT by itself
 evidence of type C. Require a concrete anchor.

STEP 4 — Mode.
 For (B) SELF-REPORT → mode=chat. Always. Even when the phrasing is a command
 ("pull up your vitals", "describe each one"): reporting your own state is chat.
 For (D) REMARK → mode=chat.
 For (A) GENERATE:
   - execute if the deliverable is a concrete artifact or precise transformation
     (code, function, config, file edit, formal draft, rewrite, calculation);
   - explore if it explicitly asks for several options, alternatives, or brainstorming
     ("what are some...", "give me a few...");
   - chat otherwise — a single conversational suggestion, naming, word choice, or
     judgement asked of you inside a dialogue.
 For (C) ENGAGE-PRIOR:
   - recall when the question is about what actually happened or what was actually
     said: content, attribution, origin, who coined it, whether it was discussed,
     counterfactuals about the origin of real past material, or when the message is a
     declarative rebuttal/extension of something stated earlier (a statement, not a query);
   - explore when the question opens new conceptual ground on top of the earlier
     material: are X and Y the same or different, what does it mean, how does it feel,
     could it be otherwise, what follows from it — i.e. the answer must be reasoned out,
     not looked up.
   - When both readings fit, ask: "is the user checking the record, or thinking further?"
     Checking the record → recall. Thinking further → explore.

STEP 5 — Scope.
 If tool=answer, scope is all, with exactly two exceptions:
   - date/time/day questions → facts (as already specified);
   - the message asks you to report or use stored state about you or the user:
     your current vitals/signals/feelings/state, your preferences, what you know
     about the user, remembered personal facts → facts.
   Asking you to INVENT, DECIDE, or REASON about such state is not a report:
   that stays scope=all.
 If tool=rag or web_and_rag, choose scope from the target of the anchor:
   - earlier turns/conversations/things you two said → session;
   - a named file, note, or document library → docs;
   - stored preferences or profile facts → facts;
   - unspecified or mixed → all.
 Never pair scope=docs with web_and_rag; if both a named file and current web data
 are needed, emit tool=rag, scope=docs.

STEP 6 — Anti-drift checks before emitting.
 - Do not choose rag just because the message sounds intimate, continues a thread,
   or uses "we"/"you". Require an anchor from Step 3.
 - Do not choose answer just because the message is short or conversational; a short
   message with an anchor and a question about it is still rag.
 - Do not choose execute merely because the message uses an imperative verb; ask
   whether an artifact is being produced.
 - Do not choose explore merely because a message is long or philosophical.
 - Do not choose web_search unless external, time-sensitive, or post-training data
   is genuinely required; introspection, philosophy, and naming never require it.

STEP 7 — Output validation.
 Emit exactly one JSON object with keys tool, mode, scope, in that order, lowercase,
 values drawn only from the listed enums, no trailing text, no explanation, no
 markdown. If unsure between two labels, pick the one your Step-1 request type
 selects rather than the one the topic suggests.