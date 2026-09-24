ADDITIONAL PROCEDURE — apply the steps below in order. The first step whose test
matches decides the label. These steps refine the rules above for messages that are
part of an ongoing personal conversation with the assistant.

STEP 0 — Live external information.
If the message asks for information about the outside world that changes over time
(news, prices, weather, scores, releases, "latest"), use the existing web rules and stop.
Never choose web_search for a message about the assistant itself, about the user, or
about this conversation, no matter how novel or introspective it sounds.

STEP 1 — Named artifact test.
If the message names a specific file, document, component, feature, module, phase, or
project term (e.g. a .md file, "the Timing Gate", "Phase 12", "the scheduler"), the
content lives outside this turn:
  tool = rag
  scope = docs if a filename is named, otherwise session
  mode  = recall (or explore if the question is open-ended research about it)
Stop.

STEP 2 — History-dependence test. Ask exactly one question:
"To respond well, do I need material from EARLIER in our history — things said in turns
before the last one or two?"

  Answer YES if any of these hold:
    - The message contains an explicit backward-time marker: before, earlier,
      previously, last time, yesterday, we discussed, we talked about, our conversation,
      you used to, you've said, you kept, always, again.
    - The message asserts, tests, or reasons about a PATTERN, trait, capacity, tendency,
      or ongoing state of the assistant that could only be established across many turns
      ("you genuinely don't have X", "your vocabulary came from...", "your vitals are
      more precise than...", "you keep doing Y").
    - The message asks the assistant to compare something now against something it said
      or was like at an earlier point.

  Answer NO if the message is confined to the here-and-now:
    - It talks only about the immediately preceding turn or the current one. Markers:
      just said, you just, right now, in this reply, in the same breath, you picked,
      you answered, that word you used, "you didn't ask me anything".
    - It reports or describes the USER's own life, actions, feelings, or work
      ("I spent time on X", "I'm describing my present state").
    - It asks the assistant for its present view, definition, preference, feeling, or
      what something "is like from the inside", with no backward reference.
    - It quotes or paraphrases a stored fact, vital, or setting purely in order to
      question the assistant about the present moment.

If YES:
  tool  = rag
  scope = session
  mode  = explore if the main question asks to distinguish or compare two or more named
          things ("is A the same as B, or something different?"), or is open-ended
          research/brainstorming; otherwise mode = recall
Stop.

If NO, continue to STEP 3.

STEP 3 — Present-turn and personal messages.
  tool = answer
  mode:
    execute if the user asks for a concrete artifact or edit (write, fix, refactor,
      summarise this text, compute this).
    explore if the user asks for open-ended generation of options or research on general
      knowledge ("what are some ways", "how might").
    chat in every other case, including probing questions about the assistant's inner
      experience, challenges to what it just said, emotional disclosure, appreciation,
      and small talk. Introspective depth does NOT make it explore or recall.
  scope:
    session if the message explicitly names the interaction itself — "this
      conversation", "chatting with you", "talking to you", "see you tomorrow", "that was
      a great session", "thanks for this" — i.e. a pleasantry or comment whose subject is
      the act of conversing with the assistant.
    facts only for date/time/day answers, or when the user explicitly asks what
      preferences or facts are stored about them.
    all in every other case, including all questions about the assistant's feelings,
      words, definitions, or state in the current turn.
Stop.

TIE-BREAKERS (use only when two steps seem to match equally)
- Explicit backward-time marker beats present-moment marker: choose rag/session.
- Present-moment marker beats mere emotional or introspective depth: choose answer.
- A long message is not automatically rag. Length is irrelevant; only the
  history-dependence test in STEP 2 matters.
- A short one-line statement about what the user did is answer/chat/all, even if it
  mentions the assistant's internals.
- The words "fact", "stored", "vitals", "memory", "profile" appearing in a message are
  NOT by themselves grounds for scope=facts or tool=rag. Ask STEP 2 first.
- When the user challenges, corrects, or catches the assistant out about its own last
  reply, that is answer/chat/all — the evidence is already in the message.
- Never emit tool=rag with mode=chat, and never emit scope=docs unless a document, file,
  or note is actually referenced.
- Prefer answer/chat/all when genuinely undecidable and the message is conversational;
  prefer rag/recall/session when genuinely undecidable and the message points backward.

OUTPUT CHECK before responding:
1. Exactly one JSON object, three keys, no prose, no code fence.
2. tool is one of answer, web_search, rag, web_and_rag.
3. mode is one of recall, explore, execute, chat.
4. scope is one of session, docs, facts, all.
5. If any value would be outside these lists, replace it using the steps above, not with
   free text.