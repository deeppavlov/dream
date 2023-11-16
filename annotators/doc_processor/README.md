# Document Processor

## Description

Document Processor is an annotator that converts the given file to .txt format and uploads it to file server for future use. Currently works with .txt, .pdf, .html files and, additionally, .docx Teams meeting transcripts.

## Dialog State

Here is an example of what Document Processor may add to the dialog state:
```
{
    "human": {
        "attributes": {
            "documents_in_use" = ["nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc", "kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc"],
            "documents_combination_ids" = {
                "LKNpck0nke_7ed546db9846ba7661ceda123837f7f":
                [
                    "nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc", 
                    "kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc"
                    ],
                "kfmIOJkm9e_7ed546db9846ba7661ceda123837f7f":
                [
                    "nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc", 
                    "lrfmovor99_jdcn096db9846ba681ceda398kewn93"
                    ]
                }
            "processed_documents" = {
            "nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc":
            {
                "initial_path_or_link": "https://website.com/example.txt",
                "processed_text_link": "{FILE_SERVER_URL}/file?file=nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc.txt",
                "filename": "example"
                },
            "kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc":
            {
                "initial_path_or_link": "https://website.com/other_example.pdf",
                "processed_text_link": "{FILE_SERVER_URL}/file?file=kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc.txt"
                "filename": "other_example"
                },
            "lrfmovor99_jdcn096db9846ba681ceda398kewn93":
            {
                "initial_path_or_link": "https://website.com/another_example.docx",
                "processed_text_link": "{FILE_SERVER_URL}/file?file=lrfmovor99_jdcn096db9846ba681ceda398kewn93.txt"
                "filename": "another_example"
                }
            }
        }
    }
}
```

`documents_in_use` are the documents that are being discussed on this step of the dialog. These are typically the documents specified in the attributes of the last human utterance or the arguments of doc-processor docker container.

`documents_combination_ids` is a dictionary mapping combination id with ids of documents that this combination includes. Each docs (2 and more) that were ever used together in `documents_in_use` have their own combination id and are stored in `documents_combination_ids`.

`processed_documents` are all documents that were given by the user during the dialog and processed by system with all the information available about these documents. `processed_documents` always include `documents_in_use` and may include previously discussed documents if there are any.

## Parameters

```
SERVICE_PORT: 8188
SERVICE_NAME: doc_processor
FILE_SERVER_TIMEOUT: timeout for request to the server where files are stored.
DOC_PATHS_OR_LINKS: paths or link to the files to be used for Question Answering. If paths, those are paths to files in `documents` folder in dream. If links, those must point to a file, not an Internet page.
    NB: file paths/links must be separated by a comma and no whitespace.
    NB: you only need DOC_PATHS_OR_LINKS if you are using doc-processor-from-args. Otherwise, paths or links will be specified in the attributes of the last human utterance.
N_TURNS_TO_KEEP_DOC: number of dialog turns for which one file is saved after it was last discussed.
    NB: you only need N_TURNS_TO_KEEP_DOC if you are using doc-processor-from-atts. Otherwise, files from docker container argument (in case of doc-processor-from-args) are stored and discussed for the entire dialog.

```