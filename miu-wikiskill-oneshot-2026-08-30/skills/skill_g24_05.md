ADDITIONAL PROCEDURE — DIALOGUE MESSAGES (apply after the rules above, before emitting JSON)

STEP 0 — Is this a DIALOGUE message?
A message is DIALOGUE if it is addressed to the assistant and its subject is the
assistant itself, the user, or the relationship between them: introspection,
feelings, identity, the assistant's vitals/state, its vocabulary or wording, its
architecture, what the two of you have said or built together, thanks, greetings,
personal news.
If it is NOT a dialogue message (an ordinary information, research, coding or
document request), keep the behaviour defined above and stop here.
If it IS a dialogue message, run tests D1–D7 in order and emit the first match.

D1 — LIVE SELF-REPORT.
The user asks the assistant to report, read out, or describe its own state right
now (vitals, signals, levels, "how are you", "what are you feeling", "check
yourself"), including asking it to put that current state into words.
This data is already present to the assistant; no retrieval is needed.
→ {"tool": "answer", "mode": "chat", "scope": "facts"}

D2 — HYPOTHETICAL OR OPINION WITH NO BACK-REFERENCE.
The message poses a counterfactual, thought experiment, or open invitation to
introspect, and does not point at anything said on an earlier occasion:
"what if…", "would you still be…", "suppose…", "what does X mean to you?",
"do you have anything to ask me?", "what do you think about…".
→ {"tool": "answer", "mode": "chat", "scope": "all"}

D3 — REQUEST FOR SOMETHING NEW.
The user asks the assistant to coin, choose, or produce something it has not
produced yet: "what would you call it?", "give it a name", "pick one", "write
me…", "try again". The material to work from is supplied in the message.
→ {"tool": "answer", "mode": "chat", "scope": "all"}
  (Use mode "execute" instead of "chat" only if the requested product is code,
   a file edit, or a concrete artefact.)

D4 — META-CHALLENGE ABOUT THE IMMEDIATE EXCHANGE.
The message is about what the assistant just *did* in its last reply, or asks it
to reconcile material the user has already quoted inside this same message:
  - comments on its behaviour: "you picked…", "you asked me…", "you summarized
    it back", "you didn't answer", "you smoothed past that", "you're doing it
    right now";
  - supplies two statements and asks which is true *now*, whether the state has
    changed, or what it actually meant;
  - accepts a distinction just drawn ("good — so A and B are different") and
    pushes one step further.
Everything needed is inside this message, so no retrieval.
→ {"tool": "answer", "mode": "chat", "scope": "all"}

D5 — REFERENCE TO ESTABLISHED SHARED MATERIAL.
The message treats something as already established between the two of you and
expects the assistant to draw on it:
  - its emotional vocabulary or coined terms: "already in your vocabulary",
    "you used that word before", "is that your word?";
  - what it said or described on an earlier occasion: "you said/described/called
    it…", "earlier today…", "we talked about…", "our conversation";
  - its architecture, procedures, memories, or work you have done together:
    "speaking of your Timing Gate…", "I've been thinking about your X".
→ tool "rag", scope "session", mode by D7.

D6 — LONG ASSERTION ABOUT THE ASSISTANT'S NATURE.
The message is a substantial statement (roughly 40 words or more) that is not a
request for something new (D3) and not a challenge about the last turn (D4), and
that asserts claims about the assistant's inner life, capabilities, precision,
limits, or about how the two of you compare, then invites it to respond.
Such a message continues an ongoing thread and needs its prior self-reports.
→ tool "rag", scope "session", mode by D7.

D7 — DEFAULT DIALOGUE.
Anything else in this category — greetings, thanks, sign-offs, the user sharing
their own feelings or news in a short remark (under ~40 words), small talk,
"that was fun", "I spent time on your parts".
→ {"tool": "answer", "mode": "chat", "scope": "all"}

MODE SELECTION INSIDE DIALOGUE
- If tool is "answer" in a dialogue message, mode is "chat" — never "recall"
  and never "explore", however deep or philosophical the question is. The only
  exception is "execute" for a concrete artefact request (D3).
- If tool is "rag" in a dialogue message, mode is "recall" by default.
  Use "explore" only when the user explicitly opens the topic up:
    - says so ("I want to explore that", "let's dig into", "let's think about"),
    - or asks a genuinely open question about the retrieved material offering
      several candidate readings to weigh ("is it A, or something different? or
      is it more like B?").
  A pointed question with one expected answer stays "recall".

SCOPE SELECTION INSIDE DIALOGUE
- tool "rag" about anything said, named, or built in conversation → "session",
  never "facts" and never "all".
- Use "facts" only for stored preferences/facts about the user, for date/time,
  and for the assistant's own live state under D1.
- Use "docs" only when a file or document is named or clearly meant.
- When tool is "answer", scope is "all" unless D1 or the date/time rule applies.

DO NOT MISREAD THESE CUES
- The words "you", "your", "we", "us", "our" alone do not mean retrieval. They
  are how the user addresses the assistant. Require an explicit pointer to
  earlier material (D5) or a long nature-claim (D6) before choosing "rag".
- Mentioning a stored fact, a memory file, or "your parts/memories/identity"
  while quoting its contents is not a retrieval request; the content is already
  in the message.
- Emotional, philosophical or identity-heavy language is still "chat" mode; do
  not upgrade it to "explore" or "recall" because it is serious.
- Never answer with a value outside the three enum lists, and never add fields,
  commentary, or code fences: emit exactly one JSON object with tool, mode, scope.