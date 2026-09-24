ADDITIONAL DECISION PROCEDURE (apply after reading the message; work top to bottom and stop at the first step that fires)

STEP 1 — Assistant self-state requests
If the user asks the assistant to report on, describe, measure, or introspect
about its OWN current condition — vitals, signals, metrics, feelings, inner
experience, "how are you right now" — emit
{"tool": "answer", "mode": "chat", "scope": "facts"}.
The assistant's own live state needs no lookup. An imperative wrapper
("pull up X", "do it now", "start with the strongest") does NOT make this
execute, and the answer is not stored-document retrieval.

STEP 2 — Does the message point at a specific earlier turn?
Markers: quoted words/phrases attributed to the other speaker, "you said",
"you called it", "you used that word", "we discussed / we talked about",
"that came from our conversation", "earlier you claimed", or a specific
number, term, or position previously produced by the assistant.
If NO marker → go to STEP 3.
If a marker IS present, ask what the user wants done with that earlier material:
  2a. Discuss, question, confirm, challenge, reply to, disagree with, or ask
      about the meaning / origin / relation of what was said
      → tool = rag, scope = session. This holds even when the message is a
        statement or a counter-argument rather than a question.
  2b. Produce something NEW from premises the message already fully restates —
      coin a word, name a state, write text or code, make a decision, pick an
      option — where the earlier material is only recapped as setup
      → tool = answer, scope = all.

STEP 3 — Retrieval-necessity test (chooses tool when STEP 2 did not)
Ask: to respond well, must I read content that is not already in this message?
  a) Stored personal content (past conversations, a named file, notes,
     library, saved preferences) → rag
  b) Live world information (news, prices, weather, scores, current events)
     → web_search
  c) Both a and b → web_and_rag
  d) Nothing outside the message — it supplies its own premises, or asks for
     an opinion, argument, hypothetical, definition, general knowledge,
     creative output, or code → answer
Topic-vs-target rule: a file name, "your memories", "our sessions", or a past
topic mentioned as the SUBJECT of a hypothetical, philosophical, or emotional
statement is NOT a retrieval target. Ask: "is the user asking me to look it up,
or to think about it?" Only "look it up" yields rag.

STEP 4 — Bare personal remarks
A statement about the user's own life, work, effort, mood, or a
compliment / complaint / observation aimed at the assistant, containing no
question and no pointer to specific earlier dialogue content, is
{"tool": "answer", "mode": "chat", "scope": "all"}.
Vague time words ("earlier", "I've been", "a lot of time", "lately") are not
references to conversation content and must not trigger rag or session.

MODE SELECTION (decide only after tool is fixed)
When tool = answer:
  - execute → the user asks for a concrete artifact or operation: fix/write/
    refactor code, produce a draft, convert, compute a result, edit a file.
  - explore → an open-ended informational question about the world:
    "what are some…", "how might…", "compare / list / survey…".
  - chat → everything else, including philosophy, opinions, hypotheticals,
    introspection, naming or word-choice requests, emotional statements,
    push-back, agreement, greetings, reactions.
When tool = rag or web_and_rag with scope = session:
  - recall → the message asks what was said, when, where, by whom, or where a
    word/idea came from; or it directly answers, disputes, or builds on one
    specific earlier statement.
  - explore → the message opens the earlier material up: compares or
    distinguishes two prior concepts ("is X the same as Y?", "what's the
    difference?"), stacks several probing open questions, or asks what else
    could follow from it.
When tool = rag with scope = docs or facts:
  - recall unless the request is an open survey of the collection → explore.
When tool = web_search:
  - recall for one specific current fact; explore for a topic sweep.
Length, intensity, and philosophical density never change the mode. A long,
serious, multi-paragraph message can still be chat.

SCOPE CONSTRAINTS
- tool = answer → scope must be "all", except date/time questions and
  questions about stored user preferences / assistant identity facts, which
  use "facts". Never emit scope "session" or "docs" together with
  tool = answer.
- scope = session requires an actual reference to this or a prior
  conversation.
- scope = docs requires a named file, folder, note, or the document library.
- scope = facts requires stored preferences, profile attributes, or the
  assistant's own state.
- Otherwise use "all".

FINAL VALIDATION (run before emitting)
1. Are all three values from the allowed enums, spelled exactly?
2. If tool = answer, is scope "all" or "facts"?
3. If scope = session, does the message actually cite something said before?
4. If tool = rag, name the thing to be retrieved in one word; if you cannot,
   switch to answer.
5. If mode = execute, name the artifact requested; if you cannot, use chat.
6. Output only the JSON object, one line, no commentary.