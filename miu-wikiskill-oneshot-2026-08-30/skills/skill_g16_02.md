ADDENDUM — DECISION PROCEDURE
Apply the steps in order. Stop at the first rule that fires inside a step.

STEP 0 — Normalise before judging
- Strip direct address by name ("Monica, ...", "hey Monica"). A name is never evidence
  for rag, facts, or session.
- Ignore message length, emotional intensity, and philosophical depth. None of them
  imply that anything must be retrieved.

STEP 1 — TIME-ANCHOR TEST (this decides whether retrieval is needed at all)
Find every reference the message makes to something outside itself and label it:

NOW-anchored (nothing to look up) when the referenced content is
  - quoted or restated inside this very message ("you said 'thin'", "your stored fact
    says X", "you described it as Y"), or
  - about the turn that just happened: "just", "right now", "in that answer",
    "you picked", "you answered", "I gave you", "I asked you", "you summarised it", or
  - about the present moment or the current state of either participant, or
  - a recent action the user reports doing ("I just spent time on X", "I fixed Y").

THEN-anchored (retrieval needed) when it points at material NOT reproduced here:
  - explicit past markers: "before", "earlier", "previously", "last time", "yesterday",
    "we discussed", "we talked about", "our conversation(s)", "you used to", "you
    always", "you used that word before", "came from our ...", "back when"
  - something named but not explained, assumed already shared: a file, a note, a
    project component, a feature, a plan, a prior decision, a running thread
  - the user's long-term background offered as context (years of practice, formative
    history, past therapy or work), or a claim about the assistant's behaviour or
    state ACROSS time (patterns, tendencies, ongoing vitals, "you tend to")

Decision:
  - one or more THEN-anchored references → RETRIEVAL = yes
  - only NOW-anchored references, or none → RETRIEVAL = no
Quoting is what removes the need to look something up: a message may quote you at
length and still be RETRIEVAL = no.

STEP 2 — Choose tool
- Needs live external information (news, prices, weather, scores, "latest") →
  web_search, or web_and_rag if RETRIEVAL is also yes.
- Else RETRIEVAL = yes → rag.
- Else → answer.

STEP 3 — Choose scope
If tool = answer:
  - date / time / day question → facts
  - the message is about this conversation or the relationship itself: thanking you for
    the talk, saying goodbye or "see you tomorrow", "nice chatting with you",
    commenting on how the conversation is going → session
  - everything else → all
If tool = rag or web_and_rag:
  - a file, note, or document named or clearly meant → docs
  - the user asks what is stored/remembered about THEM (preferences, profile) without
    quoting it → facts
  - anything anchored in prior turns, shared history, or this ongoing work → session
  - truly unclear which store → all

STEP 4 — Choose mode
- Imperative build/fix/write/change/run task → execute.
- Else if tool = answer → chat. This includes serious, deep, or probing questions put
  to you about yourself ("what does X mean to you?", "how does that land?", "are you
  doing that right now?", "which did you actually mean?"): answer + chat.
- Else (rag, web_search, web_and_rag):
  - explore when the question is open-ended, comparative, or generative: "is X the same
    as Y or something different?", "what are some…", "how might…", laying out
    alternatives and asking you to weigh them, stacking several open questions.
  - recall otherwise: asking what was said, decided, or stored; or putting one specific
    earlier item to you and asking you to respond to it.

STEP 5 — ANTI-PATTERNS (check each before emitting; these are the common errors)
- Do NOT choose facts merely because the words "fact", "stored", "remember", or
  "preference" appear. If the message already contains the content, RETRIEVAL = no.
- Do NOT choose rag merely because the message is about you — your words, states,
  parts, architecture, feelings, or design. Only a THEN-anchored reference justifies rag.
- Do NOT choose rag merely because the user is being personal, vulnerable, or
  confrontational, or because they describe what they just did with you.
- Do NOT drop to answer just because a message ends with a feelings question: if a
  THEN-anchored reference is present, keep rag and scope = session.
- Do NOT treat a bare present-moment self-report from the user ("I'm feeling X right
  now", "this is a nice state") as retrieval: answer/chat/all.
- Do NOT use web_search for anything the user's own history or your general knowledge
  can answer.

STEP 6 — CONSISTENCY CHECK before output
- tool = answer → mode must be chat or execute (never recall or explore).
- tool = rag / web_search / web_and_rag → mode must be recall, explore, or execute
  (never chat).
- scope = session with tool = answer is allowed only for talk about this conversation
  or the relationship; otherwise answer takes all (or facts for date/time).
- scope = docs only when a document, file, or note is actually indicated.
- Emit exactly the three fields, values only from the listed enums, JSON only, no prose.