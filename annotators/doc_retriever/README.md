# Document Retriever

## Description

Document Retriever is an annotator with two endpoints used to retrieve `PARAGRAPHS_NUM` document parts most relevant to the user request.

1. **vectorize_documents** endpoint splits the documents provided by the user into chunks of ~100 words. Chunks are then transformed into a TF-IDF matrix; the resulting vectors and the vectorizer are saved for future use. This step is performed only once, in the beginning of the dialog.
Documents (txt format), matrix, and vectorizer are uploaded to file server to be used by **return_candidates** endpoint and **dff_document_qa_llm_skill**.
2. **return_candidates** endpoint downloads TF-IDF matrix and vectorizer from the file server. It then converts the user’s utterance into a TF-IDF vector and finds `PARAGRAPHS_NUM` candidates with highest cosine similarity among TF-IDF vectors of text chunks.

## Dialog State

Here is an example of what Document Retriever may add to the dialog state for both endpoints.

### /vectorize_documents endpoint
```
{
    "human": {
        "attributes": {
            "model_info": {
                "db_link": "{FILE_SERVER_URL}/file?file=lmskdUBH9m_7ed546db9846ba7661ceda123837f7fc.db",
                "matrix_link": "{FILE_SERVER_URL}/file?file=lmskdUBH9m_7ed546db9846ba7661ceda123837f7fc.npz",
                "file_ids": ["nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc", "kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc"]
            }
        }
    }
}
```

`db_link` is a link to the dataset for all vectorized `documents_in_use`.

`matrix_link` is a link to the TF-IDF matrix for all vectorized `documents_in_use`.

`file_ids` are ids of files that were used to fit the vectorizer. Information about these files can be found in `documents_in_use`, in which their ids are dictionary keys.

### /return_candidates endpoint

```
{
    "utterances": [
        {
            "annotations": {
                "doc_retriever": {
                    "candidate_files": [
                        "26.txt",
                        "24.txt",
                        "3.txt",
                        "25.txt",
                        "4.txt"
                    ]
                }
            }
        }
    ]
}
```

`candidate_files` is a list of files (each file is a chunk of the given document or documents) most similar to the last user utterances in terms of cosine similarity over TF-IDF vectors. 

## Parameters

```
CONFIG_PATH: configuration file with parameters for doc_retriever model
FILE_SERVER_TIMEOUT: timeout for request where files are stored
PARAGRAPHS_NUM: number of most relevant chunks to retrieve. Don't make this number too large or the chunks won't fit into LLM context!
```

## Dependencies

- both **return_candidates** and **vectorize_documents** endpoints depend on **doc_processor** annotator
- **return_candidates** endpoint depends on **vectorize_documents** endpoint