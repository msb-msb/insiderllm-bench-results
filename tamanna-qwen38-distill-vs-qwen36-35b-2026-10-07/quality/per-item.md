# Per-item results

Wrong field values in **bold**.

### Primary: thinking off, max_tokens 100 (pass 1 of 2; pass 2 identical for both models)

| item | gold tool/mode/scope | Qwen3.6-35B-A3B Q4_K_M | Distill Q4_K_M | correct | fields that differ | note |
|---:|---|---|---|---|---|---|
| 1 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 2 | answer/chat/all | answer/**recall**/**session** | answer/chat/**session** | neither | mode |  |
| 4 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 6 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 7 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 10 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — |  |
| 12 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — |  |
| 13 | rag/recall/docs | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 15 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 16 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 18 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 22 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 24 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 25 | rag/recall/session | rag/recall/session | rag/recall/session | both | — |  |
| 26 | rag/recall/session | **answer**/**chat**/session | **answer**/**chat**/**all** | neither | scope | distill unparseable |
| 28 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | distill unparseable |
| 29 | rag/explore/session | **answer**/**chat**/session | **answer**/**chat**/**all** | neither | scope | distill unparseable |
| 30 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 33 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 34 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 35 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 36 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 37 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 38 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 39 | answer/chat/all | answer/chat/all | answer/chat/**facts** | base only | scope |  |
| 40 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | distill unparseable |
| 41 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | distill unparseable |
| 44 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 48 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 49 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 50 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 51 | answer/chat/all | answer/chat/all | answer/chat/all | both | — |  |
| 53 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 58 | rag/recall/session | **answer**/**chat**/**all** | rag/recall/session | distill only | tool, mode, scope |  |
| 60 | answer/chat/session | **rag**/**recall**/**docs** | answer/chat/**all** | neither | tool, mode, scope |  |
| 61 | rag/explore/session | rag/explore/session | rag/**recall**/session | base only | mode |  |
| 62 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/session | neither | scope |  |
| 65 | answer/chat/facts | answer/chat/**all** | answer/chat/**all** | neither | — |  |
| 68 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 69 | rag/explore/all | **answer**/**chat**/all | **answer**/**chat**/all | neither | — |  |
| 71 | answer/chat/facts | answer/chat/**all** | answer/chat/**all** | neither | — |  |
| 72 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | distill unparseable |
| 73 | answer/chat/session | answer/chat/session | answer/chat/session | both | — |  |
| 74 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 77 | rag/explore/session | **answer**/**chat**/session | **answer**/**chat**/session | neither | — |  |
| 78 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — |  |
| 82 | rag/explore/docs | rag/**recall**/docs | rag/**recall**/docs | neither | — |  |

### Secondary: thinking on, max_tokens 8,192 (one pass)

| item | gold tool/mode/scope | Qwen3.6-35B-A3B Q4_K_M | Distill Q4_K_M | correct | fields that differ | note |
|---:|---|---|---|---|---|---|
| 1 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 209 vs 50 |
| 2 | answer/chat/all | answer/chat/**session** | answer/chat/**session** | neither | — | reasoning tokens 642 vs 94 |
| 4 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 72 vs 35 |
| 6 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 158 vs 44 |
| 7 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 177 vs 132 |
| 10 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — | reasoning tokens 138 vs 42 |
| 12 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — | reasoning tokens 80 vs 38 |
| 13 | rag/recall/docs | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | base unparseable; reasoning tokens 8192 vs 134; base hit cap |
| 15 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 109 vs 64 |
| 16 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 105 vs 52 |
| 18 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 666 vs 167 |
| 22 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 990 vs 102 |
| 24 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 729 vs 56 |
| 25 | rag/recall/session | rag/recall/session | rag/recall/session | both | — | reasoning tokens 209 vs 240 |
| 26 | rag/recall/session | rag/**explore**/session | **answer**/**chat**/session | neither | tool, mode | reasoning tokens 1578 vs 133 |
| 28 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 606 vs 104 |
| 29 | rag/explore/session | **answer**/**chat**/session | **answer**/**chat**/session | neither | — | reasoning tokens 1255 vs 228 |
| 30 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 634 vs 55 |
| 33 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 273 vs 71 |
| 34 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 777 vs 63 |
| 35 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 828 vs 80 |
| 36 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 149 vs 68 |
| 37 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 113 vs 98 |
| 38 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 83 vs 57 |
| 39 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 615 vs 184 |
| 40 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 153 vs 158 |
| 41 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | base unparseable; reasoning tokens 8192 vs 71; base hit cap |
| 44 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 91 vs 36 |
| 48 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 60 vs 36 |
| 49 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 96 vs 49 |
| 50 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 95 vs 36 |
| 51 | answer/chat/all | answer/chat/all | answer/chat/all | both | — | reasoning tokens 252 vs 101 |
| 53 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 1007 vs 90 |
| 58 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | base unparseable; reasoning tokens 8192 vs 270; base hit cap |
| 60 | answer/chat/session | answer/chat/**all** | answer/chat/**all** | neither | — | base unparseable; reasoning tokens 8192 vs 318; base hit cap |
| 61 | rag/explore/session | rag/explore/session | rag/explore/session | both | — | reasoning tokens 762 vs 153 |
| 62 | rag/recall/session | rag/recall/session | **answer**/**chat**/**all** | base only | tool, mode, scope | reasoning tokens 483 vs 298 |
| 65 | answer/chat/facts | answer/chat/**all** | answer/chat/**all** | neither | — | reasoning tokens 846 vs 145 |
| 68 | rag/recall/session | **answer**/**explore**/**all** | **answer**/**chat**/**all** | neither | mode | distill unparseable; reasoning tokens 711 vs 8192; distill hit cap |
| 69 | rag/explore/all | **answer**/**chat**/all | **answer**/**chat**/all | neither | — | reasoning tokens 1031 vs 162 |
| 71 | answer/chat/facts | answer/chat/**all** | answer/chat/**all** | neither | — | reasoning tokens 1685 vs 141 |
| 72 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 388 vs 156 |
| 73 | answer/chat/session | **rag**/**recall**/session | answer/chat/**all** | neither | tool, mode, scope | distill unparseable; reasoning tokens 3431 vs 361 |
| 74 | rag/explore/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 355 vs 81 |
| 77 | rag/explore/session | **answer**/**chat**/session | **answer**/**chat**/session | neither | — | reasoning tokens 848 vs 374 |
| 78 | rag/recall/session | **answer**/**chat**/**all** | **answer**/**chat**/**all** | neither | — | reasoning tokens 454 vs 59 |
| 82 | rag/explore/docs | rag/**recall**/docs | rag/**recall**/docs | neither | — | reasoning tokens 151 vs 50 |
