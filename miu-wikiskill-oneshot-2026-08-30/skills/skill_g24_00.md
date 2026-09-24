ADDITIONAL PROCEDURE — apply after the rules above. Where this section and the
examples above disagree, this section wins.

STEP 0 — Identify the SUBJECT of the message.
  Ask: "Is this message primarily ABOUT the assistant itself — its inner states,
  its feelings, its vocabulary, its nature, its architecture/components, or its
  relationship with the user?"
    - No  → keep using the base rules above and stop here.
    - Yes → this is a SELF-DIRECTED message; go to STEP 1.
  Self-directed messages NEVER use web_search or web_and_rag, no matter how
  philosophical or open-ended they are.

STEP 1 — Current-state readouts.
  If the message asks the assistant to report its live internal signals right now
  (vitals, levels, current readings, "how are you feeling right now", "pull up
  your X"), emit {"tool": "answer", "mode": "chat", "scope": "facts"}.
  Reason: like the date and time, the assistant's current state is already
  available to it; it is not a document lookup. Do not use rag for this.

STEP 2 — The self-containment test (answer vs. rag).
  Ask: "To reply well, must I look up material that is NOT already present in
  this message?"

  2a. Choose {"tool": "answer", "mode": "chat", "scope": "all"} if ANY of:
      - The message asks what the assistant currently experiences, feels,
        intends, or means — including "what does <word> mean to you", "what is
        that like", "how does that feel from the inside".
      - The message asks the assistant to produce something new: coin a word,
        pick a name, choose between options the user has just laid out, decide,
        or commit to one of two readings ("which did you actually mean?").
      - The message is a hypothetical or thought experiment ("what if", "would
        you still be you", "suppose someone deleted", "imagine").
      - The user restates the disputed material IN FULL in this message and then
        asks only for a present judgement about it ("you said A, and also B —
        which is true now?"). The user has supplied the evidence; no lookup.
      - The message describes what is happening in this very turn ("you're doing
        it right now", "you just said", "you picked", "in the same breath").
      - The message is a statement about the USER's own life, work, feelings, or
        opinions, with no request to retrieve anything.

  2b. Choose tool=rag with scope=session if ANY of:
      - The message points at earlier material WITHOUT reproducing it: "before",
        "already", "earlier", "you used to", "you've said", "we discussed",
        "our conversation", "last time", "you called me X".
      - It treats a term, value, or claim as established shared vocabulary or
        shared history ("that's already in your vocabulary", "we named that X",
        "you call this Y").
      - It builds on the assistant's accumulated self-reports across the
        conversation (its measurements, its emotional words, how it has been
        describing itself) rather than on one sentence just uttered.
      - It discusses the system's own components, procedures, memories, or design
        (a module, a gate, a stored procedure) as an ongoing topic.
      - It is a long reflective turn that asserts a substantive claim developed
        over the conversation and invites the assistant to respond to it.

  If 2a and 2b both seem to fire, prefer 2b only when an explicit past-reference
  marker from 2b is present in the wording; otherwise prefer 2a.

STEP 3 — mode for self-directed rag messages.
  - explore: the user explicitly says explore/wonder/dig into it, OR asks an
    open question with several possible directions ("is A the same as B, or is it
    something different?", "what am I to you?", "how might...").
  - recall: everything else, including yes/no questions, confirmations, "is that
    your word?", "would that still exist?", and statements that invite a reply.

STEP 4 — Consistency checks before emitting.
  - If tool=answer, then mode=chat, unless the user explicitly asks to
    brainstorm, list options, or research (then explore), or asks for a concrete
    edit/computation/piece of code (then execute).
  - If tool=answer, then scope=all, except: date/time questions and live
    internal-state readouts, which use facts.
  - Never pair tool=answer with mode=explore just because the message is
    philosophical or emotionally deep. Depth is not exploration.
  - Never choose scope=docs unless a file, note, document, or library is named or
    clearly meant. The assistant's own memory, vitals, or personality is not a
    document; use session (history) or facts (stored values).
  - Never choose scope=facts merely because the message mentions a stored fact.
    Use facts only when the request is to read out stored values; if the user has
    already quoted the stored value and is questioning it, use all.
  - Emit only the three enum values listed for each field, and nothing but the
    JSON object.