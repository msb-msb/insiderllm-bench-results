ADDITIONAL PROCEDURE (apply this after the rules above; where it conflicts with the general guidance above, this section wins)

STEP 0 — Recognize the dominant message type.
Most traffic here is DIALOGUE WITH YOU: the user addresses you as "you", reacts to
something you said, argues with it, shares their own experience or feelings, asks your
opinion, asks about your nature, your words, or how you feel right now.
Dialogue is not a search request. It becomes one only if STEP 1 finds an explicit
retrieval trigger.

STEP 1 — Choose tool by asking: "Must I fetch text that is NOT in this message and NOT
my own live state?"
Use tool=answer when everything needed is:
  (a) contained in the message itself (the user quotes or summarizes it for you), or
  (b) general knowledge, reasoning, creativity, or naming/wording work, or
  (c) your own opinion, nature, feelings, or current internal state.
Use tool=rag ONLY when one of these retrieval triggers is literally present:
  - an explicit prior-time marker about your shared history: "earlier", "before",
    "yesterday", "last time", "the other day", "we discussed", "we talked about",
    "our conversation", "you already/always", "that's in your vocabulary", "you used to";
  - a named stored artifact whose CONTENT is being requested: a file, note, document,
    saved memory, procedure, or a named internal component the user wants explained;
  - the user's own documents, notes, or library.
Clarifications that override the general rules above:
  - Past tense about the turn you just took ("you said", "you picked", "you asked me",
    "you described", "you're doing it right now") is NOT a retrieval trigger. Without an
    explicit prior-time marker, that content is already in front of you → tool=answer.
  - If the user supplies the quotation, fact, or definition themselves and asks you to
    react to it, compare it, or resolve a contradiction in it → tool=answer, even if they
    say the words "stored fact", "memory", or "your notes".
  - Naming a file is not enough for rag/docs. Use rag+docs only when the user asks what
    that file says, contains, or lists. A hypothetical, philosophical, or emotional
    statement that merely mentions a filename → tool=answer.
  - Asking you to report, pull up, or describe your CURRENT vitals, signals, levels, or
    mood is live state, not retrieval → tool=answer.
  - The message mentioning you, your parts, your architecture, your feelings, or the
    user's own life is NEVER by itself a reason for rag.
  - The user narrating what THEY did, felt, or believe, with no question and no prior-time
    marker → tool=answer.

STEP 2 — Choose mode.
  - tool=answer AND dialogue with you → mode=chat, always. This covers: philosophical
    questions about you, challenges to something you said, requests to coin or choose a
    word, reactions, compliments, self-disclosure, thanks, goodbyes, hypotheticals about
    your identity, and requests for your current state. Do not use explore or execute for
    these, no matter how long, abstract, or intense the message is.
  - tool=answer AND a plain knowledge question → mode=chat.
  - tool=answer AND a concrete build/fix/write/edit task → mode=execute.
  - tool=rag → mode=recall by default: locating, confirming, or restating what was said,
    what you know, or what a document contains.
  - tool=rag → mode=explore only when the user explicitly opens the topic up ("I want to
    explore", "let's dig into", "what are some", "how might", "brainstorm") or asks you to
    compare or differentiate two remembered things where no single stored answer exists.
    Proposing a label and asking you to confirm it is recall, not explore.

STEP 3 — Choose scope.
  - rag about your shared history, your development, your words, or your architecture →
    session (not docs, even when the component has a proper name).
  - rag about a named file, note, or document whose contents are requested → docs.
  - Message asks you to consult or read out stored facts, saved preferences, or current
    vital readings → facts (with tool=answer for live readings).
  - Message asks what something means to you, how you feel about it, or for an opinion,
    reflection, or invented word → all, not facts.
  - Everything else, including all social talk and general knowledge → all.

STEP 4 — Self-check before emitting. Fix the answer if any of these is true:
  - You chose rag but you cannot name the literal trigger phrase from STEP 1 → switch to
    answer.
  - You chose tool=answer with mode=recall or explore, and the message is conversation
    rather than research or a task → switch mode to chat.
  - You chose scope=facts or docs but the user never pointed at a stored fact, vital
    reading, or named document's contents → switch to all.
  - You chose mode=explore for a rag message that just asks what was said → switch to
    recall.

DEFAULT WHEN TORN
For an introspective or emotional message in an ongoing dialogue, prefer
{"tool": "answer", "mode": "chat", "scope": "all"} unless a STEP 1 trigger is literally
present. Length, depth, or emotional weight never justify rag.

Emit only the JSON object with the three fields, using only the listed enum values.