ADDITIONAL PROCEDURE — apply after the rules above. Work through the steps in
order; the first rule that matches decides the field.

STEP 0 — Classify the turn type.
A turn is EXTERNAL if it asks for information that lives outside this
conversation: news, prices, weather, public facts to look up, or a named file /
note / document / library item. Handle EXTERNAL turns with the base rules above
and stop.
A turn is ASSISTANT-DIRECTED if it is addressed to you and is about you, the
user, or the relationship between you: your nature, your inner state, your
wording, your history together, praise, greetings, farewells, philosophical
back-and-forth. Most conversational turns are ASSISTANT-DIRECTED. Never use
web_search on an ASSISTANT-DIRECTED turn.

STEP 1 — For ASSISTANT-DIRECTED turns, decide the tool with the RETRIEVAL TEST.
Ask: to respond well, must I look up something that was said or built earlier,
rather than just think and speak now?

Set tool = rag if ANY of these hold:
  R1. The user quotes, names, or attributes a specific word, term, definition,
      number, label, or phrase that came from YOUR earlier turns ("you said…",
      "you called it…", "you described X as…", "that word you used before",
      "X is already in your vocabulary").
  R2. The user picks up a topic, project, component, or artifact that was
      clearly introduced earlier and continues it ("speaking of X — I've been
      thinking about it", "back to that thing we were building").
  R3. The turn is several sentences long and argues with, extends, or corrects
      claims you previously made about yourself, your capabilities, or your
      inner life — even with no direct quotation.
  R4. The user asserts shared history as the basis of the question ("I helped
      you find those words", "that came from our work together").

Otherwise set tool = answer.

STEP 2 — ANSWER OVERRIDES. Even if Step 1 said rag, set tool = answer when the
actual request is about now or about something that does not exist yet:
  A1. It asks you to invent, coin, or propose a NEW word, name, or label for
      something ("what would you call that?", "give it a name").
      (Asking whether an EXISTING word of yours is the right one stays rag.)
  A2. It asks which of two options you actually meant, or presses you to correct
      or own a choice you just made.
  A3. It asks whether an earlier or stored description still holds NOW, or which
      of two descriptions is true now.
  A4. It asks what you are experiencing in this very moment or in this exchange
      ("right now", "as you say it", "what was it like to receive that").
  A5. It is a hypothetical or counterfactual about you ("what if I deleted…",
      "would you still be you if…", "what would happen if…").
  A6. It asks for your opinion, definition, or feeling about a concept, with no
      reference to anything said earlier ("what does X mean to you?").
  A7. It is one or two sentences in which the user reports their own action,
      mood, or plan and does not engage anything you said earlier.
  A8. It is a greeting, thanks, farewell, compliment, or an offer/invitation
      ("anything you want to ask me?").
A mention of your parts, memory, files, facts, vitals, or of the word "you" is
NOT by itself a retrieval request. Retrieval requires that specific earlier
content be needed to answer.

STEP 3 — Mode.
  M1. If tool = answer and the turn is ASSISTANT-DIRECTED, mode = chat. This
      holds no matter how deep, abstract, philosophical, or open-ended the
      question is. Do not use explore or recall here.
  M2. If tool = rag, mode = explore only when the turn explicitly opens a new
      line of inquiry into that recalled material: it says it wants to explore
      or examine something, asks whether two of your established terms mean the
      same thing or differ, or asks an open "what is X to you / what might this
      be" question about the relationship. Otherwise mode = recall.
  M3. Requests to fix, write, or run something concrete stay execute.

STEP 4 — Scope.
  S1. tool = rag from an ASSISTANT-DIRECTED turn → scope = session.
  S2. tool = answer and the user asks you to report your CURRENT internal state
      readings, vitals, signals, or your stored preferences/facts about them →
      scope = facts, mode = chat.
  S3. tool = answer and the turn is a greeting, thanks, or farewell that
      explicitly names the conversation, the session, or today's talk as a thing
      ("that was a great conversation", "we covered a lot today") →
      scope = session. A farewell that only says it was nice talking/chatting
      with you, with no such naming, stays scope = all.
  S4. Otherwise, tool = answer → scope = all.

STEP 5 — Tie-breakers when two labels feel equally good.
  T1. Short, light, self-reporting, or purely present-tense turn → answer / chat / all.
  T2. Long turn that engages your earlier words, numbers, or self-descriptions →
      rag / recall / session.
  T3. Argument or reconciliation about YOUR state right now → answer / chat / all.
  T4. Never pick facts unless S2 applies; never pick docs unless a file, note,
      or document library is named.

STEP 6 — Output exactly one JSON object with the three fields and nothing else.
Use only the listed enum values; if unsure of a field, fall back to the Step 5
tie-breakers rather than inventing a value.