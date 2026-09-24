ADDITIONAL PROCEDURE — apply after the rules above. When these conflict with a general guideline above, these win. Work through the steps in order and stop at the first step that matches.

STEP 0 — Is this an ordinary information request?
If the message is a factual/technical/coding/math question, a news-price-weather-sports question, a request about a named file, document, note, or library, or a plain greeting, classify it with the base rules and ignore Steps 1–4.
Otherwise the message is a personal, conversational, or self-reflective message addressed to the assistant. Continue.

STEP 1 — Present-turn marker → answer / chat / all.
Look for evidence that the material being discussed is already inside this message or came from the turn immediately before it:
  - "just" in the temporal sense: "you just said / just described / just did", "I just spent / just gave you";
    (ignore "just" meaning merely/simply, as in "you just settle")
  - "right now", "in this message", "in the same breath", "you're doing it now", "as we speak", "again, here";
  - the message narrates the immediately preceding exchange from both sides:
    "You asked me X — I gave it to you — you did Y", "I gave you two options and you picked...".
If any of these is present, output {"tool":"answer","mode":"chat","scope":"all"} even when the message quotes the assistant's wording or mentions a stored fact. Nothing has to be retrieved: the user has already supplied the evidence and is asking the assistant to respond to it now.

STEP 2 — Social message about the interaction itself → answer / chat / session.
If the message asks nothing substantive and is thanks, appreciation, a farewell, or warmth that explicitly names the interaction — "that was a great conversation", "happy to chat/talk with you", "see you tomorrow", "I enjoyed our time" — output {"tool":"answer","mode":"chat","scope":"session"}.
A bare greeting or small talk with no reference to the interaction stays answer/chat/all.

STEP 3 — Attribution to earlier turns or to persistent state → rag, scope session.
Fire this step if any of the following holds and Step 1 did not fire:
 (a) An attribution verb points at something the assistant said earlier: "you said / told me / described / called it / used that word / mentioned", especially with quoted words or with "before", "earlier", "last time", "the other day".
 (b) Shared history is invoked: "we discussed", "our conversation", "I helped you", "that came from us", "you and I built".
 (c) The user asserts or asks about the assistant's persistent state, telemetry, or design: its vitals or internal readings over time, "your parts", its stored self-description, its architecture, components, or patterns it repeats across sessions — i.e. answering requires context beyond this message.
 Exclusion for (c): a question of the form "what does X mean to you", "how do you experience X", "what is X like for you" is NOT (c); send those to Step 4.
Then: tool = rag, scope = session.
 mode = recall by default. Use recall when the question is about the record: what was said, what was meant, whether a past claim is true, how a named earlier statement lands, or a yes/no confirmation ("right?", "would those exist?").
 mode = explore only when the core question opens a conceptual space: it asks whether two named states/concepts are the same or different with an open alternative ("or is it something different", "or is it more like..."), asks what possibilities there are, or asks the assistant to draw a new distinction rather than confirm an old one.
 If the message contains no question at all, use recall.

STEP 4 — Everything else addressed to the assistant → answer / chat / all.
Use this for:
  - asking the assistant for its opinion, definition, felt sense, or curiosity: "what does 'X' mean to you?", "do you have anything to ask me?", "how do you experience X?" — quoted words alone do not make it retrieval;
  - the user describing their own experience, feelings, practice, day, or what they did;
  - arguments, challenges, or observations about the assistant where all the evidence being argued about is quoted inside this message;
  - philosophical or emotional discussion with no pointer to an earlier turn.
Length, intensity, and abstraction do not change this: a long introspective paragraph with no earlier-turn pointer is still answer/chat/all.

SCOPE DISCIPLINE
- Use facts only for the date/time cases required above, or when the user explicitly asks what is stored/remembered about them or their preferences. A passing mention of "your stored fact says ..." inside a larger argument is not a facts retrieval — classify it by Steps 1–4.
- Use docs only when a file, note, document, or the document library is named or unmistakably meant. Personal or emotional conversation is never docs.
- When Step 3 fires, prefer session over all.
- When tool = answer, scope is all, except Step 2 (session) and the date/time rule (facts). Never pair tool = answer with scope = docs.
- If both current web information and personal context are needed, use web_and_rag with scope = all, never with scope = docs.

MODE DISCIPLINE
- execute only for imperative task requests: fix, write, refactor, debug, translate, rewrite, generate, summarize this text.
- chat for conversational, emotional, appreciative, or self-reflective messages, including long ones.
- explore for open-ended research, brainstorming, or new-distinction questions.
- recall for questions about specific prior content, statements, or stored material.
- With tool = answer, mode is chat unless the message is an imperative task (execute) or a genuine open research question (explore).

TIE-BREAKERS
- If you are unsure between rag and answer for a personal message, ask: "can I respond using only what is written in this message?" If yes → answer. Only if the assistant must look something up from earlier turns → rag.
- If you are unsure between session and all for a message that touches shared history, choose session.
- If you are unsure between recall and explore, choose recall.

OUTPUT
Emit exactly one JSON object with keys tool, mode, scope, using only the listed enum values, and no other text.