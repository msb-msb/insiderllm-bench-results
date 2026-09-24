ADDENDUM — DECISION PROCEDURE (apply the steps in order; the first step that matches decides the field; then run the final checks)

DEFINITIONS (used below)

- OPERATIVE REQUEST = the sentence(s) carrying the actual question or ask.
  Ignore opening acknowledgements ("that's fair", "thanks", "ok, got it") when
  deciding — they are not the operative request.
- PRESENT-TURN ANCHOR = the message locates the material it is discussing inside
  the current exchange. Signals: "just said / just described / just now",
  "right now", "in that answer", "you're doing it as you say it", or the message
  narrates a completed back-and-forth that plainly happened here
  ("you asked me X, I gave it to you, you did Y with it"), or the message itself
  already quotes the full content it is asking about.
- PAST-TIME MARKER = "before", "earlier", "last time", "yesterday",
  "you used to", "we discussed / we talked about", "our conversation(s)",
  "you've said", "you always", or a topic resumed with no location in this turn.
- RELATIONSHIP TALK = the user comments on the conversation or the ongoing
  relationship itself: "great conversation", "nice talking with you",
  "happy to chat with you", "see you tomorrow", "I enjoy these sessions".

STEP 1 — External or file needs (unchanged rules apply first)
If the message needs live web information, or names a specific file/document,
classify by the existing rules and stop. Everything below concerns
conversational, introspective and personal messages.

STEP 2 — Relationship talk
If the message is greeting, thanks, sign-off or small talk AND contains
RELATIONSHIP TALK → {"tool":"answer","mode":"chat","scope":"session"}.
Plain greetings or small talk with no reference to the conversation or the
relationship stay answer/chat/all.

STEP 3 — The message cites something the assistant said, felt, or chose
3a. If the citation carries a PRESENT-TURN ANCHOR → answer/chat/all.
    The material is already in front of you; no retrieval is needed. This holds
    even if the message quotes a stored fact, a vital, a metric or an earlier
    word — if the message supplies the content, do not retrieve it.
3b. If the citation carries a PAST-TIME MARKER, or is given with no temporal
    location at all (a characterisation, word or stance attributed to the
    assistant "in general"), or the message asks whether something changed
    across time / where a word or idea came from / whether the two of you built
    it together → tool=rag, scope=session.

STEP 4 — Questions about the assistant's current inner state, meaning or opinion
"What does X mean to you?", "how does that feel now?", "what do you want?",
"do you have anything to ask me?" with no cited prior material →
answer/chat/all. Introspection is generated, not looked up. Do not use rag or
scope=facts merely because the question is about the assistant's states,
emotions, vitals or self-model.

STEP 5 — User statements with no question
5a. A short update, remark, or present-moment self-description (roughly one or
    two sentences, about what the user is doing, feeling, or just did) →
    answer/chat/all.
5b. An extended disclosure (roughly three or more sentences) about the user's
    own history, practice, therapy, background, or their long-running theory of
    the assistant and the relationship → tool=rag, mode=recall, scope=session.
    Such messages continue a thread that has prior context worth loading.

STEP 6 — Ongoing shared projects
If the operative request resumes work on a named component, feature, design or
plan the two of you have been developing (architecture, a gate, a pipeline, a
phase) without naming a file → tool=rag, mode=recall, scope=session.

MODE SELECTION

If tool = answer:
  - mode = execute only for a concrete artifact or action request
    ("fix this", "write the function", "rewrite this paragraph").
  - mode = explore only for open-ended research or brainstorming requests
    ("what are some options for...", "how might we...").
  - otherwise mode = chat. Conversational, philosophical, emotional,
    introspective and general-knowledge messages are all chat.

If tool = rag (or web_and_rag):
  - mode = recall when the user wants a specific remembered thing: what was
    said, what a document states, what happened, whether something changed,
    or when they are asserting something about the shared history.
  - mode = explore when the operative request is open-ended: it offers two or
    more candidate readings and asks which fits ("is X the same as Y, or
    something different?"), trails into alternatives ("or is it more like..."),
    asks the assistant to speculate, distinguish, or map a concept space rather
    than report a fact.
  - mode = execute when the user asks for an action performed on retrieved
    material.

SCOPE SELECTION

- With tool = answer: scope = all, except date/time questions (facts) and
  Step 2 relationship talk (session).
- With tool = rag in conversational messages: scope = session. Use scope = docs
  only for a named file or an explicit reference to stored documents/notes.
- Use scope = facts only when the user asks the system to look up their own
  stored preferences or profile facts ("what do you know about me?",
  "what's my stored preference for X?"), or for date/time. Do not use facts
  because the message mentions the words "fact", "stored", "memory" or a vital.
- scope = all with tool = rag only when the user explicitly asks to search
  everything.

TIE-BREAKERS

- If both a PRESENT-TURN ANCHOR and a PAST-TIME MARKER appear, follow the one
  attached to the operative request; if still ambiguous, prefer rag/…/session.
- If unsure between answer and rag for an emotional or philosophical message
  that contains no citation and no past-time marker → answer/chat/all.
- If unsure between recall and explore inside rag → recall.

FINAL CHECKS
1. Exactly one JSON object, three keys, no prose, no markdown.
2. Each value is one of the listed enum strings — never invent a value, never
   leave a field empty, never combine two values.
3. Re-read the operative request once and confirm the tool matches whether
   information must be retrieved (rag) or is already present (answer).