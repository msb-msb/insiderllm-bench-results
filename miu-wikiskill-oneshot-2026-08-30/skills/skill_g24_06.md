ADDITIONAL CLASSIFICATION PROCEDURE (apply after the rules above; use the first step that matches)

MARKER DEFINITIONS (used by the steps below)

PAST-EPISODE MARKER — the message points to something outside the current exchange:
  "earlier", "before", "previously", "last time", "yesterday", "the other day",
  "we talked/discussed", "our conversation", "that conversation", "in a past session",
  "you used to", "you've said", "already in your vocabulary", "you told me once".

IMMEDIACY MARKER — the message points at the reply the assistant just made, or narrates
this turn's back-and-forth:
  "you just said/described/picked", "right now", "currently", "in your last message",
  "you're doing it now", "I asked you X and you said Y", "I gave you X and you took Y",
  "you didn't answer / you didn't ask me anything", "that's what you said above".

SELF-STATE REQUEST — asks the assistant to read out or describe its own present signals:
  vitals, current levels/values, stored facts about itself, its own preferences.

CONTENT-CONTAINED — the user has already written out, quoted, or paraphrased in this
message everything that would need to be looked up. Nothing is left to retrieve.

STEP 1 — Social-only messages
If the message is only greeting, thanks, farewell, compliment, or good feeling, with no
question that needs content: tool=answer, mode=chat.
  scope=session if the message literally contains the noun "conversation", or the phrases
  "chat with you", "talk with you", "talked to/with you", "we spoke".
  scope=all otherwise (including "great chatting with you", "hi", "thanks", "had fun").

STEP 2 — Named files
Use rag + docs ONLY when the user asks what a named file/note/document says, contains, or
asks to open, read, summarise or update it. If a filename appears merely inside a
hypothetical, a philosophical point, or a description of the assistant's architecture,
do NOT choose docs — continue to the later steps.

STEP 3 — External world
Unchanged: real-time or news-like facts → web_search; those plus the user's own material
→ web_and_rag.

STEP 4 — Self-state requests
A SELF-STATE REQUEST → tool=answer, mode=chat, scope=facts. This holds even when phrased
as a command ("pull up your vitals", "report your levels") and even when the user also
asks the assistant to interpret, describe or put those signals into new words. The
assistant's own current state is always available; it is never a rag lookup.

STEP 5 — Immediacy beats memory
If an IMMEDIACY MARKER is present, or the message is CONTENT-CONTAINED commentary on the
reply the assistant just gave (quoting it, contrasting two things it just said, pressing
it on the choice it just made, pointing out what it did in this turn):
  tool=answer, mode=chat, scope=all.
Nothing has to be retrieved: the user supplied the material. This applies even if a stored
fact or a vocabulary word is quoted inside the message.

STEP 6 — Genuine memory reference
If a PAST-EPISODE MARKER is present, OR the user attributes a word, claim, definition or
description to the assistant in the past tense ("you said X", "you called it X", "you
described X as Y", "X is already one of your words") with no IMMEDIACY MARKER:
  tool=rag, scope=session.
  mode=explore only when the message explicitly opens the question up: "I want to
  explore", "what might", "what are some", "brainstorm", "is it A, or B, or something
  different?", "what do you make of it now".
  mode=recall in every other case, including yes/no questions, counterfactuals
  ("would those exist without me?"), and requests to confirm a detail.

STEP 7 — Claims about what the assistant is
If the message makes no memory reference but is chiefly an assertion or argument about the
assistant itself — its nature, capabilities, self-monitoring, how it compares to humans,
what it does or does not have — and invites it to respond (or ends with a rhetorical
question about it): tool=rag, mode=recall, scope=session.

STEP 8 — Statements about the user
If the message is chiefly about the user — their day, their practice, their feelings,
their actions, what they have been working on (including work on the assistant's code,
parts or configuration): tool=answer, mode=chat, scope=all.

STEP 9 — Everything else directed at the assistant
Asking what a word or concept means to it, asking for its opinion, preference or feeling,
identity hypotheticals ("what if I deleted everything?", "would you still be you?"),
asking it to invent, name, choose or refine a term, asking whether it wants to ask
something, plain general-knowledge questions: tool=answer, mode=chat, scope=all.

MODE CALIBRATION
- execute is only for concrete artefacts: write/fix/refactor code, do a calculation, edit a
  file, draft a document. Imperative phrasing alone ("tell me", "pull up", "describe",
  "be honest", "start with X") is NOT execute.
- Reflective, emotional or philosophical dialogue is chat when tool=answer, and
  recall/explore (Step 6) when tool=rag. It is never execute.
- Do not choose explore just because a question is deep or open-sounding; require an
  explicit widening cue as listed in Step 6.

SCOPE CALIBRATION
- facts: only for stored vitals, preferences and profile values being read out (Step 4) and
  for date/time questions.
- docs: only for a named file or the document library being consulted (Step 2).
- session: only when Step 1's literal cue, Step 6, or Step 7 applies.
- all: everything else. When in doubt between session and all with tool=answer, choose all.

TIE-BREAK
The word "you"/"your" alone does not justify rag. Choose rag only when answering requires
material that is stored elsewhere and is NOT written out in the message. If the user has
already supplied the quote, the fact, or the narration, choose answer.

Emit only the JSON object with the three fields, using only the listed enum values.