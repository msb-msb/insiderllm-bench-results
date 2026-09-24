ADDITIONAL DECISION PROCEDURE

Apply the steps below in order. They refine the rules above and take precedence
where they conflict. Decide tool first, then mode, then scope, then run the
final consistency check.

STEP 1 — TOOL

1a. Self-state requests. If the user asks the assistant to report, check, read
    out, or describe its OWN current internal state — readings, metrics,
    signals, mood, load, status — the answer comes from the live system, not
    from a search. Markers: an imperative like "check / pull up / read me /
    describe / show me" combined with "your <state noun>" and a present-time
    cue ("right now", "currently", "at the moment").
    → tool=answer, mode=chat, scope=facts. Internal state is never rag.

1b. Aboutness test. For any message that mentions earlier turns, earlier
    wording, stored notes, or documents, ask: is the message ULTIMATELY about
    that stored material, or is the material only a premise?
    ABOUT it → tool=rag. Signs: the user quotes, checks, corrects, credits,
      dates, or asks the meaning/consistency of specific things already said or
      written — a particular word or phrase the assistant introduced, a number
      the assistant reported earlier, a claim, a decision, a named file. Shapes:
      "you said X", "you called it X", "you used that word before", "that came
      from our conversation", "we agreed X — was that right?", "what does <file>
      say".
    PREMISE only → tool=answer. Signs: the earlier material is restated inside
      the message itself and is used to launch a hypothetical, philosophical, or
      creative request that the assistant answers by reasoning now. Shapes:
      "what if…", "would that still…", "imagine…", "what would you call…",
      "give it a name", "so then, what does that mean?".
    Tie-break: if the message already contains everything needed to respond,
    choose answer; if responding requires looking back at what was actually
    said or written, choose rag.

1c. Bare social or personal statements. A message that reports the user's own
    feelings, actions, or life ("I spent hours on X", "I'm tired", "thanks",
    "I fixed the wiring"), or that merely reacts — agreeing, joking,
    complimenting, apologising — with no question about earlier content and no
    retrieval request, is small talk: answer/chat/all. Past tense about the
    USER's own activity is not a retrieval cue.

1d. Substantive commentary on the assistant's own earlier self-reports. If the
    user pushes back on, evaluates, or reframes claims the assistant previously
    made about itself (its capabilities, its measurements, its inner life),
    even without an explicit question mark, that is ABOUT earlier content:
    tool=rag.

1e. Philosophical or hypothetical questions about identity, consciousness,
    memory, deletion, or selfhood are answer — even when they name memory
    stores, sessions, or config files as a premise — unless 1b/1d mark them as
    being about specific earlier content.

1f. Nothing in this dialogue pattern justifies web tools. Only add web_search or
    web_and_rag when the message needs facts that change over time in the
    outside world (news, prices, weather, scores, releases, "latest").

STEP 2 — MODE

2a. If tool=answer: default mode=chat.
    - Use execute only for a concrete artifact task with an imperative verb
      ("fix this code", "write the function", "rewrite this paragraph",
      "convert this to JSON").
    - Use explore only when the user explicitly asks for a RANGE: "what are
      some…", "brainstorm", "list options", "give me ideas", "research".
    - Asking for one word, one name, one label, one judgement, one definition,
      or one explanation is chat, not explore — even if the question is deep,
      abstract, or open-ended in feeling.

2b. If tool=rag or web_and_rag:
    - recall when the user wants to identify, retrieve, confirm, or attribute
      something stored: "what did we say", "did you say", "who came up with",
      "what does <file> say", quoting a past line and responding to it.
    - explore when, after pointing at stored material, the user asks an open
      conceptual question built on it: comparison ("is X the same as Y?", "how
      do these differ?"), implications, patterns, or brainstorming from it.
      A question of the form "is A the same as B, or is it different?" about
      terms established earlier is explore, not recall.

2c. If tool=web_search: explore for open-ended or survey-style current-info
    questions; recall for one specific current fact (a price, a score, a
    release date).

2d. Never use execute for reflective, emotional, or philosophical dialogue.

STEP 3 — SCOPE

3a. If tool=answer or web_search, scope is all — except date/time questions and
    self-state reports (1a), which are facts. Never emit session or docs with
    tool=answer or tool=web_search.

3b. If tool=rag or web_and_rag, pick where the material lives:
    - session: it was said in conversation between the user and the assistant.
    - docs: a named file, note, or the document library.
    - facts: stored preferences or profile facts about the user.
    - all: mixed sources, or the message does not indicate which.

3c. If a named file is involved and current web info is also requested, prefer
    tool=rag with scope=docs.

STEP 4 — CONSISTENCY CHECK before emitting

- Exactly one JSON object, exactly the three keys, no prose, no code fence.
- Each value is one of the listed enum values, lowercase, spelled exactly.
- If tool=answer and scope is session or docs → change scope to all
  (or facts if 1a or a date/time question applies).
- If mode=explore, verify the message asked for a range of items (tool=answer)
  or an open conceptual question about stored material (tool=rag); otherwise
  use chat or recall.
- If tool=rag, verify the message actually points at something previously said,
  written, or stored; if it does not, use answer.