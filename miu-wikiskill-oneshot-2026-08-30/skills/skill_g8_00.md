ADDITIONAL CLASSIFICATION PROCEDURE (apply after everything above; where it conflicts with a general guideline, this procedure wins)

STEP 0 — Output form
- Emit exactly one JSON object with exactly the keys tool, mode, scope, and only values from the three lists. No extra keys, no commentary, no markdown.

STEP 1 — Is this a mid-conversation dialogue turn?
Signals (any one is enough):
- It reacts to something the assistant just said ("that's true, but…", "good —", "you said…", "interesting").
- It addresses the assistant directly by name or as "you" and is about the assistant.
- It is a statement, opinion, challenge, or emotional remark rather than a lookup request.
If YES → run STEPS 2–4. If NO → skip to STEP 5.

STEP 2 — Self-state requests are never retrieval
If the message asks the assistant to report, read out, describe, or introspect its OWN current state — vitals, metrics, signals, feelings, sensations, mood, confidence, preferences — or to state stored facts about itself or about the user:
→ {"tool": "answer", "mode": "chat", "scope": "facts"}
The assistant's live internal state is not a document and not a past conversation, so tool is never rag here, even when the wording is an imperative ("pull up…", "tell me…", "describe…"). Imperatives about self-state are chat, not execute.
Exception: hypothetical or philosophical questions about the assistant's identity, memory, continuity, or nature ("what if all of it were deleted", "would that still be you", "what makes you you") are NOT state reports →
{"tool": "answer", "mode": "chat", "scope": "all"}

STEP 3 — Look-back test (decides answer vs. rag for dialogue turns)
Ask exactly this: to respond well, must the assistant retrieve wording, claims, numbers, or decisions from earlier turns that this message does NOT restate?
- YES → tool = rag, scope = session. Typical shapes:
  • the user quotes or paraphrases a specific phrase, figure, or claim the assistant made earlier and argues with it, corrects it, or asks about it;
  • the user asks where an idea, word, or agreement came from, who introduced it, or what was concluded;
  • the user says "we/you already…" about content not reproduced in this message.
- NO → tool = answer, scope = all. Typical shapes:
  • the user restates in this message the terms, definitions, or facts the reply needs, then asks for something new;
  • the message is about the user's own life, work, or actions outside the chat ("I spent all day on…", "I'm tired");
  • the message is an opinion, compliment, complaint, joke, thanks, or general philosophical claim;
  • the message asks the assistant to invent, name, coin, rephrase, choose, or decide something using only what is on the table now.
Tie-breakers:
- Mentioning "you", "your", or the assistant's name is NOT by itself a look-back.
- A vivid or abstract topic (consciousness, emotion, meaning) is NOT by itself a look-back.
- If the message both recaps prior content AND ends in a request to produce something new, the request governs → answer.
- If the message contains no question at all but its whole point is disputing or extending something the assistant said earlier → rag/session, not answer.

STEP 4 — Mode for dialogue turns
If tool = rag (scope session):
- recall — the question is about the record: what was said, when, by whom, where a word or idea originated, what was decided, whether something was discussed.
- explore — the question asks the assistant to compare, distinguish, reinterpret, or extend earlier ideas: "is X the same as Y or different?", "what's the difference between…", "what does that imply?", "why might that be?", "is that uncomfortable or is it more like…?" Multi-part probing questions that push a concept forward are explore even when they quote an earlier word.
If tool = answer:
- chat is the default for dialogue: reflections, opinions, philosophy, emotional exchange, naming/word-choice requests, follow-ups answerable from what is already visible.
- execute only for a concrete deliverable artifact: code, a file edit, a command, a calculation, a drafted document, a rewritten passage of the user's text.
- explore only for genuinely open-ended research or brainstorming about a topic outside this conversation.
- recall for tool=answer only when the user asks for a stored fact or preference (then scope = facts).

STEP 5 — Non-dialogue messages (requests aimed at the world or the user's data)
Apply in this order, first match wins:
1. Names a specific file, note, or document, or asks what the user's library/files say → rag, scope docs; mode recall for a specific lookup, explore for open-ended reading across documents.
2. Asks about what the user and assistant previously discussed → rag, scope session.
3. Asks for stored user preferences or profile facts → answer or rag with scope facts.
4. Needs information that changes over time — news, prices, weather, scores, releases, "latest", "current", "today's" (but never date/time itself) → web_search; mode explore if open-ended, recall if a single current fact, execute if it feeds a concrete task.
5. Needs BOTH personal context and current web information → web_and_rag. Use scope session if the personal side is prior conversation, otherwise scope all. Never pair web_and_rag with scope docs; if a named file plus the web are both needed, use web_and_rag with scope all.
6. Otherwise → answer.

STEP 6 — Scope defaults
- tool = answer → scope all, EXCEPT self-state reports, stored preferences/facts, and date/time questions → facts.
- Use scope session only when the message is about this or an earlier conversation.
- Use scope docs only when files, notes, or a document library are actually implicated.

STEP 7 — Final check before emitting
1. Did I choose rag only because the topic sounded personal or introspective? If the look-back test in STEP 3 was NO, switch tool to answer and scope to all.
2. Did I choose answer/chat/all for a message whose whole purpose is challenging or asking about something the assistant said earlier? If so, switch to rag/recall/session.
3. Is the mode consistent: chat for conversation, recall for retrieving a record, explore for open comparison or research, execute only for a produced artifact?
4. Are all three values from the allowed lists? Emit the JSON.