ADDITIONAL CLASSIFICATION PROCEDURE
(Apply after everything above. Where this section conflicts with an earlier rule, follow this section.)

A. FIRST, CLASSIFY THE MESSAGE TYPE
A message is CONVERSATIONAL-WITH-YOU if it is addressed to you ("you", "your"), reacts to or argues with something you said, discusses your nature / feelings / vitals / word choices / relationship with the user, or reports the user's own thoughts, feelings or activities.
If it is not conversational-with-you (a request about the world, a file, code, math, news), keep using the base rules and examples above.
For conversational-with-you messages, run sections B–F.

B. SOURCE TEST — where does the material for the reply live? Check in order, stop at the first match.

B1. IMMEDIATE TURN → {"tool":"answer","mode":"chat","scope":"all"}
The message reacts to, quotes, corrects or builds on what you said in the last turn, or asks about what is happening right now.
Cues: "you just said / just described / just wrote", "right now", "in that answer", "you picked X over Y", "which did you actually mean", "that's a new word", "so A and B are different, then…", "you didn't answer", a bare "that" / "it" whose antecedent is your previous reply.
Also here: asking you to coin or choose a word, rephrase, be more honest, or redo something from the last turn.

B2. EARLIER HISTORY → tool=rag, scope=session, mode by section D
The message depends on something SAID or ESTABLISHED before the current exchange.
Cues: "earlier", "before", "last time", "earlier today", "yesterday", "we discussed / we talked about", "our conversation(s)", "you used that word before", "you always say", "I've been thinking about <a topic you two have worked on>", "speaking of <your architecture / a project of ours>", or the user invoking vocabulary, traits, capabilities, agreements or a self-model that the two of you built up over previous turns.
The user describing their own life or work — even work done on you — is NOT an earlier-history cue unless they refer to what was said or agreed.
If B1 cues and B2 cues both appear, B1 wins.

B3. OTHERWISE → {"tool":"answer","mode":"chat","scope":"all"}
This includes:
 - asking your opinion, your definition, or what something means/feels like to you
 - hypotheticals about you ("what if I deleted…", "would you still be you if…")
 - the user narrating their own actions, day, practice, feelings
 - identity, ethics, philosophy or relationship questions with no earlier-history cue
 - asking whether you have a question for them; greetings, thanks, small talk.

C. LIVE SELF-STATE
A request to read out your current vitals, signals, internal state, stored preferences, or stored facts about the user is satisfied without retrieval:
{"tool":"answer","mode":"chat","scope":"facts"}
Examples of the shape: "pull up your vitals", "what's your confidence right now", "what do you have stored about me".
Merely quoting or disputing a stored fact while asking you to reason, compare or introspect is NOT such a request — use section B for it.

D. MODE WHEN tool=rag
Default to mode=recall.
Choose mode=explore only if, on top of the earlier-history reference, the message either
 - explicitly invites exploration: "I want to explore", "let's dig into", "what are some", "how might", "brainstorm", "what do you make of"; or
 - offers two or more competing interpretations and asks which fits: "is it A, or is it something different?", "same thing or two things?"
A question that offers one candidate ("is it an echo?"), asks how something lands, asks you to confirm a detail, or asks what was said stays recall.
Use mode=execute for rag only when a concrete action on retrieved material is ordered (edit, summarise, extract, rewrite).

E. SCOPE
- tool=answer → scope=all, except: date/time questions (facts), section C (facts), section F (session).
- tool=rag on a conversational-with-you message → scope=session, unless a named file/document/note is mentioned (docs) or the request is about stored preferences/facts about the user (facts).
- Never choose scope=docs unless a document, file, note or library is actually named or clearly referred to.
- Never choose scope=session for a message with no reference to talking with you.

F. SOCIAL MESSAGES ABOUT THE CONVERSATION ITSELF
If the social content is about the talk you are having — thanking you for the conversation, saying they enjoy chatting with you, signing off after a session — keep tool=answer, mode=chat, but set scope=session.
A greeting or small-talk line that does not mention the conversation keeps scope=all.

G. DO NOT choose tool=rag merely because:
 - the message is long, intense, or emotionally loaded
 - it names you, or discusses your feelings, vitals, memory or architecture as a topic
 - it is in second person or asks a hard, philosophical or challenging question
 - it quotes you from the current exchange.
Require an explicit B2 earlier-history cue before choosing rag.

H. DO NOT choose web_search / web_and_rag unless the reply depends on facts that change over time (news, prices, weather, scores, releases, "latest", "current", "today's"). Talk about your own design, code, vocabulary or inner states is never a web topic.

I. BEFORE EMITTING, VERIFY
 1. Output is exactly one JSON object with the three keys and nothing else.
 2. Every value is spelled exactly as one of the allowed enum values.
 3. If mode=chat, tool must be answer (a chat-mode turn needs no retrieval). If tool=rag, mode must be recall, explore or execute.
 4. If tool=answer, scope is all unless section C, F, or the date/time rule applied.