# embcheck-1 automatic summary (grade by hand before trusting)

Dataset revision: `2ec07608ee2a77a59a3f5995ca3c10e9cba4c976`; script 0.1.0; finished 2026-11-11T01:11:30Z.

## otel (otel-0.6b, farbodtavakkoli/OTel-Embedding-600M)

- header: max_elements 2097152, cur_element_count 1064960, size_data_per_element 4236, M 16, maxM0 32
- pickle: {"type": "dict", "total_elements_added": 1064960, "id_to_label_len": 1064960, "label_to_id_len": 1064960, "id_to_seq_id_len": 0}
- prompts: {"default_prompt_name": "Retrieval-query", "query_prompt_name": "Retrieval-query", "query_prompt": "Instruct: Given a telecom domain query, retrieve relevant passages that answer the query\nQuery:", "document_prompt": "", "prompt_names": ["Classification", "Retrieval-document", "Retrieval-query", "document", "query"], "sentence_transformers": "5.7.0", "torch": "2.15.0+cpu"}
- summary: {"sampled": 100, "resolved": 100, "verdicts": {"query": 100}, "median_cos_stored_doc": 0.9618844609787554, "median_cos_stored_query": 1.000100059395411, "median_cos_doc_vs_query": 0.9624002400551035}

## control (qwen3-embedding-0.6b, Qwen/Qwen3-Embedding-0.6B)

- header: max_elements 2097152, cur_element_count 1064960, size_data_per_element 4236, M 16, maxM0 32
- pickle: {"type": "dict", "total_elements_added": 1064960, "id_to_label_len": 1064960, "label_to_id_len": 1064960, "id_to_seq_id_len": 0}
- prompts: {"default_prompt_name": null, "query_prompt_name": "query", "query_prompt": "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:", "document_prompt": "", "prompt_names": ["document", "query"], "sentence_transformers": "5.7.0", "torch": "2.15.0+cpu"}
- summary: {"sampled": 40, "resolved": 40, "verdicts": {"document": 40}, "median_cos_stored_doc": 1.000883392275334, "median_cos_stored_query": 0.9707456301493148, "median_cos_doc_vs_query": 0.969535769572758}

## Predictions (automatic)

- E1: failed
- E2: held
- E3: held
- E4: held
- E5: failed
