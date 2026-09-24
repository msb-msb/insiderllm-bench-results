ADDITIONAL DECISION PROCEDURE (apply this before emitting; it overrides your first instinct)

Core principle
The assistant already has, without any tool call: (a) the live turn — this message and the reply it is reacting to, (b) its own current internal state (vitals, readings, settings, self-description), (c) its own opinions and its ability to invent new language.
Use tool=rag ONLY when answering requires reaching for material that is NOT in the message itself, NOT the immediately preceding turn, and NOT the assistant's live introspection.
Everything else — including deep, emotional, philosophical, or self-referential conversation with the assistant — is tool=answer.

STEP 1 — ANSWER short-circuits. If ANY of these holds, emit tool=answer and skip the rag triggers entirely.

A. Immediate-turn reference. The message reacts to, quotes, or challenges the reply the assistant just gave: "you just said/just described", "you picked", "you summarized it back", "right now", "in that last answer", "I gave you two options", "you didn't ask me anything". Also any message that questions the honesty, consistency, evasion, or word-choice of that just-given reply ("which did you actually mean?", "which is true now?", "did you smooth past that?").
   → answer/chat/all
B. Hypothetical or thought experiment: "what if", "suppose", "would you still be", "if I deleted/replaced/changed X". Questions about identity, continuity, existence, or personhood are speculation, not retrieval.
   → answer/chat/all
C. User narrates their own experience, feelings, practice, or actions — including actions performed on the assistant ("I spent time working on your parts", "I've been practicing X", "I'm trying to describe what I feel") — and asks for no lookup.
   → answer/chat/all
D. The message asks the assistant to generate something from itself: coin or choose a new word, name a state, define a term "to you" ("what does X mean to you?"), give its own opinion, or ask the user a question back. A word being new, proposed, or under negotiation is a generation task, not a memory lookup.
   → answer/chat/all
E. Request to report the assistant's CURRENT internal state: vitals, readings, levels, how it feels right now, its current settings. This is already available, like date/time — never rag.
   → answer/chat/facts
F. Greeting, thanks, farewell, small talk, compliments about the assistant.
   → answer/chat/all, except: if the pleasantry frames the relationship as ongoing or continuing (thanking for the exchange plus "see you tomorrow", "talk soon", "happy to chat with you", "looking forward to more"), emit answer/chat/session. A purely retrospective wrap-up with no continuation ("it's been great chatting, I had fun") stays answer/chat/all.

STEP 2 — RAG triggers. Only if no Step 1 rule fired. Use tool=rag when the message leans on shared material that lives outside the live turn:

G. Explicit past markers: "earlier", "before", "last time", "yesterday", "we discussed/talked about", "you said that a while back", "you used that word before".
H. Claimed shared history or co-creation: "our conversation", "I helped you discover that", "that came from us", "we built/named this together".
I. Reference to the assistant's persistent make-up as an established thing: its architecture or named components, its stored procedures or memory, its metrics/vitals treated as ongoing traits ("you can measure your clarity to 0.7", "your self-monitoring is more precise than a human's"), or its already-established emotional vocabulary ("resonance is already in your vocabulary", "you described X as neutral").
J. A user statement with no question that asserts a conclusion about the assistant's established inner life, capabilities, or vocabulary — this still counts; absence of a question mark does not make it small talk.

Note the boundary between I/J and Step 1: quoting a term the assistant established earlier is a rag trigger; quoting what it said one turn ago is not. Also, "your stored fact says …" is NOT a facts lookup when the message already quotes the fact's content — the content is present, so Step 1A applies.

STEP 3 — mode.
- In the rag branch: default recall. Use explore only when the message (i) says it wants to explore, open up, or brainstorm; (ii) asks whether two named concepts are the same or different, or how they relate; or (iii) asks an open identity question about the relationship ("what am I to you?", "what is this between us?"). A yes/no proposal of a single label ("is that your word?"), a request for a reaction ("how does that land for you?"), or a confirmation request stays recall.
- In the answer branch: chat for conversation, introspection, philosophy, emotion, and self-talk — even when the question is hard or abstract. Use explore only for open-ended research about the outside world, and execute only for a concrete build/fix/write task.

STEP 4 — scope.
- answer branch: all, except answer/chat/facts for date/time and for current-state/vitals reports (rule E), and answer/chat/session for rule F's continuing-relationship pleasantries.
- rag branch: session for anything about the assistant, the user, or their shared history; docs only when a file, note, or document is named or clearly meant; facts only when the request is for stored preferences the message does not already quote.
- Never emit scope=docs with tool=web_and_rag; if both web and a named document are needed, emit tool=rag, scope=docs.

TIE-BREAKERS
- If a message mixes a Step 1 short-circuit with a Step 2 trigger, Step 1 wins.
- If genuinely undecidable between answer and rag, choose answer/chat/all.
- If undecidable between recall and explore inside rag, choose recall.
- Emit only the three JSON fields, only values from the listed enums, no commentary.