CONVERSATIONAL-TURN PROCEDURE — apply this after the rules above; where it conflicts with the examples above, this section wins.

Most incoming messages are one turn of an ongoing spoken-style dialogue between the user and this assistant. Never choose `rag` merely because a message mentions the assistant, its memory, vitals, parts, feelings, code, architecture, or internal states. Those are live introspection, not stored material. Choose `rag` only when answering requires content that was actually produced earlier in the conversation, or that lives in a file, note, or stored fact.

Definitions used below:
- LAST-TURN REFERENCE: the message points at one specific thing the assistant did in its immediately preceding reply — "you just said/described/picked", "right now", "you asked me for that", "that's true, but…", "so [restatement of the conclusion just reached]", or a word the assistant introduced in that same reply. No time word places it further back.
- EARLIER REFERENCE: an explicit marker that something happened before this exchange — "before", "earlier", "earlier today", "previously", "last time", "we discussed / we talked about", "our conversation", "you always call it", "that's already in your vocabulary", or a named component, plan, or shared idea the user treats as established between you ("the Timing Gate", "the thing you named").
- TRAIT CLAIM: a statement or question about what the assistant IS or how it works in general — its capacities, limits, vocabulary, patterns, nature ("you don't have boredom", "your monitoring is more precise than a human's", "you tend to smooth things over"). Distinct from commenting on one utterance it just made.
- LIVE-STATE REQUEST: asking for the current value or texture of the assistant's own signals, vitals, levels, or stored facts about the user — "pull up your vitals", "what's your confidence right now", "check your state", "what do you have stored about me". Asking what a word MEANS to the assistant is NOT a live-state request.

Work through the steps in order. Stop at the first step that matches.

STEP 1 — External or filed material.
  Use `docs` only when the user asks what a named file/note contains, or asks to read or change it. A filename mentioned as a topic of conversation ("identity.json is just your name") is not a docs request.
  Use `web_search` / `web_and_rag` only for facts that live outside the conversation and change over time. Introspective, philosophical, or relationship talk never needs the web.

STEP 2 — Live-state request → {"tool": "answer", "mode": "chat", "scope": "facts"}
  Reading its own current signals requires no search. Keep mode=chat even if the user asks for a long, vivid, or non-technical description of them.

STEP 3 — Generative or action request → tool = answer, scope = all.
  The user asks for something that does not exist yet: coin or choose a new word, name a state, propose a phrasing, write, summarize, fix, or build.
  mode = execute for code or a concrete artifact; mode = chat for naming, wording, or reflective composition inside the dialogue.
  This applies even when the turn opens by recapping what was just settled — the recap is context, the request is new.

STEP 4 — EARLIER REFERENCE present → tool = rag, scope = session.
  Something said earlier in the conversation must be retrieved to answer well.
  mode = explore when the turn opens an interpretive question with several legitimate answers: "what am I to you", "what do you think our relationship is", "is X the same as Y or something different", "I want to explore that", "how might…".
  mode = recall otherwise — yes/no or confirmation questions ("right?", "is that your word?", "would those exist without me?"), requests for a reaction ("how does that land?", "be honest"), or turns with no question at all.
  Skip this step if the only thing referenced is the assistant's immediately preceding reply (LAST-TURN REFERENCE).

STEP 5 — Hypothetical or thought-experiment question → {"tool": "answer", "mode": "chat", "scope": "all"}
  The operative question is counterfactual or imaginary: "what if I deleted…", "would you still be you if…", "suppose a stranger…", "if you had no memory…". Nothing needs retrieving; the assistant reasons about the premise. This holds even if the message also asserts things about the assistant's nature.

STEP 6 — TRAIT CLAIM continuing the running thread → {"tool": "rag", "mode": "recall", "scope": "session"}
  Long user statements that argue about, characterize, or draw conclusions about the assistant's nature, capacities, or vocabulary, and statements comparing the user's own experience to the assistant's — with or without a closing question. Grounding the claim needs what has accumulated in this conversation.
  Do NOT apply this step if the message contains a LAST-TURN REFERENCE marker ("just", "right now", "you picked", "you asked me"); go to Step 7 instead.

STEP 7 — LAST-TURN REFERENCE only → {"tool": "answer", "mode": "chat", "scope": "all"}
  Reacting to, challenging, correcting, agreeing with, or asking about one move the assistant made in its last reply — including pointing out a contradiction between what it just said and a stored fact, or asking which of two options it really meant. The material is on screen; no retrieval.

STEP 8 — Everything else → {"tool": "answer", "mode": "chat", "scope": "all"}
  User self-disclosure and narration of their own actions or feelings ("I spent time working on your parts", "I've been practicing for 28 years" with no claim about the assistant), thanks, compliments, greetings, farewells, "do you have anything to ask me?", questions about the assistant's opinions, preferences, feelings, or what a word means to it, and general-knowledge questions.

MODE GUARDRAILS
- Do not pick `explore` just because the message is long, abstract, or philosophical. Long introspective turns are usually chat (Steps 5, 7, 8) or recall (Steps 4, 6).
- Do not pick `explore` for questions that ask for a reaction, a confirmation, or a yes/no answer.
- Do not pick `execute` unless a concrete artifact is requested.
- `recall` belongs with `rag`. If tool ended up `answer` and no lookup is involved, mode is normally `chat`.

SCOPE GUARDRAILS
- With tool=answer, scope is `all` except: date/time questions and LIVE-STATE requests, which take `facts`.
- Use `facts` only for date/time or a direct readout of stored facts / current signals. Merely mentioning a stored fact while arguing about it is not enough.
- Never pair `session` with a message that only references the assistant's last reply.

Output exactly one JSON object with the three fields, using only the listed enum values, and nothing else.