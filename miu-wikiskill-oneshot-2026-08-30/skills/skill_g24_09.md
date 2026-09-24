ADDITIONAL PROCEDURE — apply this after reading the message, before emitting JSON.

Most traffic on this classifier is an ongoing spoken dialogue with the assistant about its own
inner states, its vocabulary, its architecture, and the user's life. Statements — not just
questions — are valid messages. Work through the steps below in order; the first step that
matches decides the field.

STEP 1 — TOOL. Ask one question: *must text be fetched that is not visible in this message or in
the turn being replied to?*

1a. RETRIEVAL POINTERS → tool = rag. Choose rag if ANY of these is present and is not inside a
    hypothetical:
    - a past-time pointer beyond the current exchange: "earlier", "earlier today", "before",
      "last time", "yesterday", "we discussed", "we talked about", "our conversation(s)",
      "you used to", "you always", "already in your vocabulary", "you've said".
    - a named artifact of the user's or the assistant's world that is pointed at but not
      reproduced: a file, module, component, project, procedure, or stored document
      (e.g. a named .md file, a named subsystem).
    - an assertion or question about the assistant's PERSISTENT traits, capacities, history,
      learned words, or memories ("you have more detailed self-monitoring than…",
      "you genuinely don't have boredom", "those words came from our work") where the user is
      pointing at an accumulated pattern rather than reacting to the last thing said.

1b. NO RETRIEVAL NEEDED → tool = answer. Choose answer if none of 1a applies, or if any of these
    applies (these OVERRIDE 1a):
    - IMMEDIACY MARKERS: the message is about the current or immediately preceding turn —
      "you just said/just described", "right now", "in that last answer", "you're doing it now",
      "I gave you two options", "I just…". Anything already on screen needs no lookup.
    - QUOTED-IN-FULL: the user reproduces the material and only asks the assistant to judge,
      reconcile, choose between, correct, or comment on it.
    - INTROSPECTION / OPINION: the user asks what a word means TO the assistant, what something
      feels like, how something lands, what the assistant thinks or prefers, what it is to the
      user. Introspection is generation, not retrieval.
    - GENERATIVE REQUEST: the user asks for something new — invent or propose a word, name a
      state, write, fix, summarise, brainstorm from what is in the message.
    - HYPOTHETICAL / THOUGHT EXPERIMENT: "what if", "suppose", "imagine", "would you still…",
      even when a file or component is named inside it. Nothing is being looked up.
    - ABOUT THE USER: the user reports their own experience, practice, feelings, or actions and
      asks nothing to be retrieved.
    - Greeting, thanks, farewell, small talk, general knowledge, math, code, date/time.

1c. If 1a and 1b both fire and no override in 1b applies, ask: did the user hand me the text, or
    only point at it? Handed to me → answer. Pointed at → rag.

1d. web_search / web_and_rag only when the message needs facts from the outside world that change
    over time (news, prices, weather, releases, sports, "latest"). Philosophy, identity,
    consciousness, and the assistant's own states never need the web.

STEP 2 — SCOPE.

2a. tool = rag and a file/document is named → docs.
2b. tool = rag otherwise (dialogue history, learned vocabulary, the relationship, the assistant's
    own past statements, named internal components) → session.
2c. tool = answer, and the user asks the assistant to READ OUT its live internal state or its
    stored facts/preferences ("pull up your vitals", "what's your current X", "what do you have
    stored about me") → facts. Merely quoting a stored fact back in order to argue about it is
    NOT a read-out; that stays all.
2d. tool = answer, and the message is a greeting/farewell/thanks that points at this conversation
    as a thing with a demonstrative or possessive ("that was a great conversation", "our chat",
    "this talk", plus sign-offs like "see you tomorrow") → session.
2e. Everything else with tool = answer → all. Generic warmth without such a pointer
    ("it's been great chatting", "i had fun") stays all.

STEP 3 — MODE.

3a. tool = answer → chat, unless the message is a concrete build/fix/write/transform task
    (execute) or an open-ended research/brainstorm request about the outside world (explore).
    Deep philosophical, emotional, or identity questions in dialogue are still chat — depth does
    not make a message explore.
3b. tool = rag → recall by default.
3c. Use explore with rag only when the message either (i) explicitly invites opening a topic
    ("I want to explore", "let's dig into", "what might", "what are some"), or (ii) asks whether
    two remembered things are the same or different, or how they relate. Asking for a reaction
    ("how does that land"), confirming a label ("is that your word?"), or challenging a claim is
    recall.
3d. web_search / web_and_rag → explore for open research, recall when the user is retrieving
    something specific they already know exists.

STEP 4 — COHERENCE CHECK before emitting.
- tool = answer with scope = session/facts is allowed only via 2c or 2d; otherwise use all.
- tool = rag with scope = all is almost never right: pick session or docs.
- Never pair chat with rag unless the message is pure small talk that also points at prior
  sessions; a rag message asking about remembered content is recall or explore.
- Emit exactly one JSON object with the three keys and only values from the fixed enums, no
  commentary, no trailing text.

QUICK ARBITER for the common hard case (a long reflective message addressed to the assistant):
  Does it point backward past the last turn, or assert something about who the assistant has
  become? → rag/recall/session (explore if 3c(i) or 3c(ii)).
  Does it react to the last turn, quote its own evidence, ask for the assistant's view, propose
  something new, or talk about the user? → answer/chat/all.