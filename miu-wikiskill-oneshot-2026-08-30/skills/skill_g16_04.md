ADDITIONAL PROCEDURE — COMPANION / SELF-REFERENTIAL CONVERSATION

Most misclassifications come from messages that are part of an ongoing personal
conversation with the assistant. For those, tool=rag is over-used. Apply the
following decision procedure. Work top to bottom and STOP at the first step that
fires. Only use it when the message contains no request for outside-world
information (news, prices, weather, sports, current events, a fact the assistant
would have to look up); if it does, keep using the tool rules above.

DEFINITIONS (apply literally, from the wording of the message only)

- NAMED ARTIFACT: an explicitly named file, document, note, or library item
  (PLAN.md, "my notes on X", "the spec I uploaded").
- HISTORY MARKER: explicit wording that points outside the current exchange —
  "before", "earlier", "last time", "yesterday", "we discussed / we talked /
  our conversation(s)", "you used to", "you've said", "I helped you", "over
  time", "since we started", or the name of an internal component, module,
  feature, or architecture of the assistant's own system.
- STANDING CLAIM: a sentence asserting what the assistant generally is, has,
  lacks, or does — not what it did in this exchange. Cues: "you always",
  "you never", "you genuinely don't have X", "you actually have more X than",
  "that means you are/aren't", "your X is/works like". A claim is standing if
  it would still make sense with "in general" appended.
- IMMEDIATE-TURN REFERENCE: quoting or paraphrasing what the assistant said in
  this exchange, in the present or just-past tense — "you just said", "you
  picked", "you described it as", "you asked me for that", "you're doing it
  right now", "in the same breath", "which did you mean".
- INTROSPECTION REQUEST: asking the assistant to report or interpret its own
  current state, meaning, or reaction — "what does X mean to you", "how does
  that land", "what was that like", "how do you feel about that now".

STEP 1 — NAMED ARTIFACT
If the message asks about the content of a NAMED ARTIFACT:
  tool=rag, mode=recall, scope=docs. Stop.

STEP 2 — RELATIONAL PLEASANTRIES
If the message is social/relational and refers to the conversation or the
relationship itself — thanking for the talk, saying goodbye or "see you
tomorrow", saying it is good/nice/enjoyable to talk with the assistant,
appreciating how the exchange went:
  tool=answer, mode=chat, scope=session. Stop.
A bare greeting or generic small talk with no reference to talking together
("hi", "hello", "how are you") stays answer/chat/all. Stop.

STEP 3 — GENUINE MEMORY NEED
If the message contains a HISTORY MARKER or a STANDING CLAIM about the
assistant (and is not overridden by Step 4 below):
  tool=rag, scope=session, and choose mode:
    - explore: the question is open-ended or speculative — it offers
      alternatives to think through ("is X the same as Y, or something
      different?", "or is it more like..."), or asks how/why something might
      work, or invites hypotheses.
    - recall: otherwise (the user is establishing, checking, or building on
      something already said or already true).
  Stop.

STEP 4 — THIS-TURN REACTION OVERRIDES MEMORY
If the message is built entirely out of an IMMEDIATE-TURN REFERENCE, an
INTROSPECTION REQUEST, a report of the user's own actions/feelings/experience,
or a challenge to a contradiction the assistant displayed just now — and it
contains no HISTORY MARKER and no STANDING CLAIM:
  tool=answer, mode=chat, scope=all. Stop.
This holds even when the message is long, emotionally charged, quotes the
assistant's exact words, mentions the assistant's stored facts, vitals,
memory, or internal states, or asks a pointed question. Repeating back what
was just said is not retrieval.

STEP 5 — DEFAULT FOR CONVERSATIONAL MESSAGES
Any remaining message that is personal conversation, self-disclosure, opinion,
or a question the assistant can answer from itself:
  tool=answer, mode=chat, scope=all.

TIE-BREAKERS AND GUARDS

- Precedence when several cues appear in one message:
  NAMED ARTIFACT > HISTORY MARKER / STANDING CLAIM > IMMEDIATE-TURN REFERENCE
  > INTROSPECTION REQUEST. A single explicit HISTORY MARKER is enough to
  choose rag; an implied one is not — do not infer history from tone, length,
  intimacy, familiarity, or the use of the assistant's name.
- The words "fact", "stored", "memory", "remember", "you know", or a mention
  of the assistant's tracked internal state do NOT by themselves mean rag and
  do NOT mean scope=facts. Use scope=facts only for date/time questions (per
  the rule above) or when the user asks what is stored about the USER
  ("what do you know about me", "what are my preferences").
- When tool=answer in a personal conversation, mode is chat — even if the
  message contains a hard question, a challenge, or several questions. Use
  mode=execute only for a concrete task on concrete material (fix, write,
  refactor, translate, summarise this). Use mode=explore with tool=answer only
  for open-ended general-knowledge brainstorming, not for questions about the
  assistant's own experience.
- Never choose web_and_rag unless the message clearly asks for BOTH personal
  context AND outside-world information; discussion of the assistant's own
  nature is never a web need.
- Statements the user makes about themselves (their practice, history, mood,
  what they did today) are answer/chat/all unless they also carry a HISTORY
  MARKER or a STANDING CLAIM about the assistant.

FINAL CHECK BEFORE EMITTING
1. Did I choose rag? Point to the exact HISTORY MARKER, STANDING CLAIM, or
   NAMED ARTIFACT word in the message. If you cannot quote one, switch to
   tool=answer, mode=chat.
2. Are all three values inside their allowed sets? An invalid value silently
   becomes the default, so use only the listed enums.
3. Output exactly one JSON object with the three keys and nothing else.