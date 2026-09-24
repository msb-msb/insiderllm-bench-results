Wrong field values in **bold**. Pass 1 of 2; pass 2 was identical on every item for both models.

| item | gold tool/mode/scope | Qwen3.8-27B Q4_K_XL | Bonsai 2 PQ2_0 | correct | fields that differ |
|---:|---|---|---|---|---|
| 1 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 2 | answer/chat/all | **rag**/**recall**/**session** | **rag**/**recall**/**session** | neither | — |
| 4 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 6 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 7 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 10 | answer/chat/session | answer/chat/**all** | answer/chat/**facts** | neither | scope |
| 12 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — |
| 13 | rag/recall/docs | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 15 | answer/chat/all | **rag**/**recall**/**session** | **rag**/**recall**/**session** | neither | — |
| 16 | answer/chat/all | answer/chat/**facts** | answer/chat/**facts** | neither | — |
| 18 | rag/recall/session | **answer**/**chat**/**facts** | **answer**/**chat**/**facts** | neither | — |
| 22 | rag/recall/session | **answer**/**chat**/**facts** | **answer**/**chat**/**facts** | neither | — |
| 24 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 25 | rag/recall/session | rag/recall/session | rag/recall/session | both | — |
| 26 | rag/recall/session | rag/**explore**/session | **answer**/**chat**/session | neither | tool, mode |
| 28 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 29 | rag/explore/session | **answer**/**chat**/session | **answer**/**chat**/session | neither | — |
| 30 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 33 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 34 | answer/chat/all | answer/chat/all | **rag**/**recall**/**session** | qwen only | tool, mode, scope |
| 35 | answer/chat/all | answer/chat/**facts** | answer/chat/**facts** | neither | — |
| 36 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 37 | answer/chat/all | **rag**/**recall**/all | answer/chat/**facts** | neither | tool, mode, scope |
| 38 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 39 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 40 | answer/chat/all | **rag**/**recall**/**session** | **rag**/chat/**session** | neither | mode |
| 41 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 44 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 48 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 49 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |
| 50 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 51 | answer/chat/all | answer/chat/all | answer/chat/**facts** | qwen only | scope |
| 53 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 58 | rag/recall/session | rag/**explore**/session | rag/**explore**/session | neither | — |
| 60 | answer/chat/session | **rag**/**recall**/**docs** | answer/chat/**facts** | neither | tool, mode, scope |
| 61 | rag/explore/session | rag/explore/session | rag/explore/session | both | — |
| 62 | rag/recall/session | rag/recall/session | rag/recall/session | both | — |
| 65 | answer/chat/facts | **rag**/**recall**/**session** | answer/chat/facts | bonsai only | tool, mode, scope |
| 68 | rag/recall/session | rag/**execute**/session | **answer**/**execute**/**facts** | neither | tool, scope |
| 69 | rag/explore/all | **answer**/explore/all | **answer**/**chat**/all | neither | mode |
| 71 | answer/chat/facts | answer/chat/facts | answer/chat/facts | both | — |
| 72 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 73 | answer/chat/session | **rag**/**recall**/session | answer/chat/session | bonsai only | tool, mode |
| 74 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 77 | rag/explore/session | rag/**recall**/session | **answer**/**chat**/session | neither | tool, mode |
| 78 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**facts** | neither | scope |
| 82 | rag/explore/docs | rag/**recall**/docs | rag/**recall**/docs | neither | — |
