# Document Retriever

## Description

Document Retriever is an annotator with two endpoints used to retrieve `PARAGRAPHS_NUM` document parts most relevant to the user request.

1. **train_and_upload_model** endpoint converts the documents provided by the user to txt format (if necessary) and splits them into chunks of ~100 words. Chunks are then transformed into a TF-IDF matrix; the resulting vectors and the vectorizer are saved for future use. This step is performed only once, in the beginning of the dialog.
Documents (txt format), matrix, and vectorizer are uploaded to file server to be used by **return_candidates** endpoint and **dff_document_qa_llm** skill.
2. **return_candidates** endpoint downloads TF-IDF matrix and vectorizer from the file server. It then converts the user’s utterance into a TF-IDF vector and finds `PARAGRAPHS_NUM` candidates with highest cosine similarity among TF-IDF vectors of text chunks.

## Parameters

```
CONFIG_PATH: configuration file with parameters for doc_retriever model
FILE_SERVER_TIMEOUT: timeout for request where files are stored
PARAGRAPHS_NUM: number of most relevant chunks to retrieve. Don't make this number too large or the chunks won't fit into LLM context!
DOC_PATH_OR_LINK: paths or link to the files to be use for Question Answering. If paths, those are paths to files in `documents` folder in dream. If links, those must point to a file, not an Internet page. NB: file paths/links must be separated by a comma and no whitespace. 
```

## Dependencies

- **return_candidates** endpoint depends on **train_and_upload_model** endpoint