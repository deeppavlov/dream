import requests
import logging
import os
import re
import docx
import filetype
import pypdfium2 as pdfium
import io

from typing import List, Dict, Union, Tuple
from pathlib import PurePath
from simplify_docx import simplify
from bs4 import BeautifulSoup
from common.files_and_folders_processing import upload_document, generate_unique_file_id


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL", None)
FILE_SERVER_TIMEOUT = float(os.environ.get("FILE_SERVER_TIMEOUT"))
HTTP_PATTERN = re.compile(r"https?://[a-zA-Z\-0-9]+[\.:].+")
FIND_ID = re.compile(r"file=([0-9a-zA-Z]*).txt")
FIND_FILENAME = re.compile(r"filename=\"?(.+)\"?(;|\b)")


def pdf_to_text(file: str) -> str:
    """Extracts text data from the given .pdf file using pypdfium.

    Args:
        file: Path to pdf file or the file itself.

    Returns:
        The text of the pdf file as string.
    """
    pdf = pdfium.PdfDocument(file)
    n_pages = len(pdf)
    full_doc_text = ""
    for page in range(n_pages):
        page_index = pdf[page]
        textpage = page_index.get_textpage()
        text_all = textpage.get_text_range()
        full_doc_text += text_all
    return full_doc_text


def html_to_text(file: str) -> str:
    """Extracts text data from the given .html file using BeautifulSoup.

    Args:
        file: Path to html file or the file itself.

    Returns:
        The text of the html file as string.
    """
    soup = BeautifulSoup(file)
    full_doc_text = soup.get_text(strip=True)
    return full_doc_text


def structure_data(meeting_transcipt: List[str]) -> Dict[str, Union[List[str], List[Dict[str, Union[str, list]]]]]:
    """Structures meeting transcript for further processing by extracting people present and utterances.

    Args:
        meeting_transcipt: A list of chunks of an unprocessed meeting transcript.

    Returns:
        A dictionary with information about the given meeting:

        {'people_present': ['A', 'B', 'C'],
         'utterances': [{'time_start': '0:0:0.0', 'person': 'A', 'sentences': 'Hello'}]}
    """
    meeting_transcipt_dict = {"people_present": [], "utterances": []}
    people = []
    for item in meeting_transcipt:
        if "   " in item or "\r" in item:
            item = [x for x in re.split(r"   |\r", item) if x]
            time = item[0]
            person = item[1]
            utts = " ".join(item[2:])
            one_utt = {"time_start": time, "person": person, "sentences": utts}
            meeting_transcipt_dict["utterances"].append(one_utt)
            if person not in people:
                people.append(person)
    meeting_transcipt_dict["people_present"] = people
    return meeting_transcipt_dict


def concat_utterances(
    utterances: List[Dict[str, Union[List[str], List[Dict[str, Union[str, list]]]]]]
) -> List[Dict[str, str]]:
    """Concatenates subsequent utterances of one person.

    Args:
        utterances: A list of dictionaries containing information about each utterance in a meeting.

    Returns:
        A dict with information about the given meeting and concatenated subsequent utterances:

        [{'person': 'A', 'sentences': 'Hello. How are you?'},
        {'person': 'B', 'sentences': 'Good. You?'}]
    """
    speaker = utterances[0]["person"]
    concat_utt = utterances[0]["sentences"]
    transcript_concat = []
    for utt in utterances[1:]:
        if speaker == utt["person"]:
            concat_utt += f' {utt["sentences"]}'
        else:
            transcript_concat.append({"person": speaker, "sentences": concat_utt})
            concat_utt = utt["sentences"]
            speaker = utt["person"]
    return transcript_concat


def make_transcript(dict_data: Dict[str, Union[List[str], List[Dict[str, Union[str, list]]]]]) -> str:
    """Creates a text transcript from a dictionary of separate utterances.

    Args:
        dict_data: A dictionary containing the information about the meeting -- people present
            and list of all utterances with metainformation.

    Returns:
        A string with the text of the meeting transcript (speakers included). Utterances of different speakers
            are separated with newlines.

        'A: Hello!\nB: Hi!'
    """
    utterances = dict_data["utterances"] if "utterances" in dict_data else dict_data
    transcript_concat = concat_utterances(utterances)
    transcript_list = [f'{utt["person"]}: {utt["sentences"]}' for utt in transcript_concat]
    transcript = "\n".join(transcript_list)
    return transcript


def teams_meeting_transcript_to_text(file: str) -> str:
    """Transforms a .docx file of Teams meeting transcript into a string with the text of the meeting.

    Args:
        file: Path to docx file (Teams meeting transcript) or the file itself.

    Returns:
        A string with the text of the meeting transcript (speakers included). Utterances of different speakers
            are separated with newlines:

        'A: Hello!\nB: Hi!'
    """
    my_doc = docx.Document(file)
    my_doc_as_json = simplify(my_doc)
    list_data = [json_part["VALUE"][-1]["VALUE"] for json_part in my_doc_as_json["VALUE"][0]["VALUE"]]
    dict_data = structure_data(list_data)
    transcript = make_transcript(dict_data)
    return transcript


def get_text_from_filepath(filepath: str) -> str:
    """Processes file of any format (.pdf, .html, .txt, .docs) to get plain text to work with.

    Args:
        filepath: Path to file (.pdf, .html, .txt, .docs).

    Returns:
        A string with the text of the file for further use.
    """
    file_extension = PurePath(filepath).suffix
    if "pdf" in file_extension:
        full_doc_text = pdf_to_text(filepath)
    elif "html" in file_extension:
        with open(filepath, "r") as f:
            html_doc = f.read()
        full_doc_text = html_to_text(html_doc)
    elif "docx" in file_extension:
        full_doc_text = teams_meeting_transcript_to_text(filepath)
    else:
        with open(filepath, "r") as f:
            full_doc_text = f.read()
    return full_doc_text


def get_text_from_fileobject(file_object: str, file_extension: str) -> str:
    """Processes file of any format (.pdf, .html, .txt, .docs) to get plain text to work with.

    Args:
        file_object: File object(.pdf, .html, .txt, .docs).

    Returns:
        A string with the text of the file for further use.
    """
    if "pdf" in file_extension:
        full_doc_text = pdf_to_text(file_object.content)
    elif "html" in file_extension:
        full_doc_text = html_to_text(file_object.text)
    elif "docx" in file_extension:
        full_doc_text = teams_meeting_transcript_to_text(io.BytesIO(file_object.content))
    else:
        full_doc_text = file_object.text
    return full_doc_text


def get_docs_to_process(all_docs_to_check: List[str], all_docs_info: dict, docs_in_use_info: dict) -> Dict[str, str]:
    """Selects the documents that need to be processed and returns their references and the types
        of each reference. For docs that were processed before but are not in docs_in_use,
        returns documents id to be used for getting link to processed doc.

    Args:
        all_docs_to_check: A list of all documents that we got from attributes or arguments.
        all_docs_info: A dict with information about all docs that were ever processed.
        docs_in_use_info: A dict with information about docs that are used now.

    Returns:
        A dict mapping document reference that needs to be processed to its type
        (link, path, or, if already processed, id):

        {'documents/example.txt': 'path',
         'https://website.com/example.txt': 'link',
         'https://other_website.com/example.pdf': 'MNpfn94j0j_7ed546db9846ba7661ceda123837f7fc'}
    """
    docs_to_process_types = {}
    # all ids of processed docs and links to processed docs
    processed_docs_links_and_ids = dict(
        [(all_docs_info[file_id].get("initial_path_or_link", ""), file_id) for file_id in all_docs_info.keys()]
    )
    if docs_in_use_info:
        # all links to processed docs in use
        docs_in_use_links = [all_docs_info[file_id].get("initial_path_or_link", "") for file_id in docs_in_use_info]
    else:
        docs_in_use_links = []
    # check if the text of the doc we're using fully corresponds to docs coming from atts/args
    if docs_in_use_links != all_docs_to_check:
        # if no, for each doc get reference type (where to get text from) – link, path, or, if already processed, id
        for doc_reference in all_docs_to_check:
            # if not processed
            if doc_reference not in processed_docs_links_and_ids.keys():
                # file server http://files:3000 will also be found
                if HTTP_PATTERN.search(doc_reference):
                    docs_to_process_types[doc_reference] = "link"
                else:
                    docs_to_process_types[doc_reference] = "path"
            # if processed
            else:
                docs_to_process_types[doc_reference] = processed_docs_links_and_ids[doc_reference]
    return docs_to_process_types


def upload_documents_save_info(
    docs_in_atts: List[str], doc_paths_or_links: List[str], all_docs_info: dict, docs_in_use_info: dict, dialog_id: str
) -> Tuple[list, dict, dict]:
    """Processes the given documents to get plain text if they were not processed before,
        uploads them to file server and returns information about each.
        NB: If there are multiple documents, their text is concatenated and uploaded to server as one .txt file.

    Args:
        docs_in_atts: Doc references that we get from attributes of user utterance.
        doc_paths_or_links: Doc references that we get from arguments of docker container.
        all_docs_info: A dict with information about all docs that were ever processed.
        docs_in_use_info: A dict with information about docs that are used now.

    Returns:
        A list containing ids of all files currently in use:
        documents_in_use = ['nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc',
        'kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc']

        A dictionary mapping combination id with ids of files currently in use:
        docs_combination_ids = {
            'LKNpck0nke_7ed546db9846ba7661ceda123837f7fc':
            ['nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc-kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc']
            }

        Another one mapping ids of all files that were ever used and information about them, such as
        file source and link to the file with processed text:
        processed_documents = {
            'nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc':
            {
                'initial_path_or_link': 'https://website.com/example.txt',
                'processed_text_link': '{FILE_SERVER_URL}/file?file=nlkr09lnvJ_7ed546db9846ba7661ceda123837f7fc.txt',
                'filename': 'Daily Syncup_24-09-2020'
                },
            'kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc':
            {
                'initial_path_or_link': 'https://website.com/other_example.pdf',
                'processed_text_link': '{FILE_SERVER_URL}/file?file=kKmcdwiow9_7ed546db9846ba7661ceda123837f7fc.txt'
                'filename': 'Example_PDF_File_Name'
                }
            }

        NB: in the first dict, the file contains concatenated processed texts for all docs.
        In the second dict, there are separate files with processed text for each doc.
    """
    # get docs we need to process
    # (either fully unprocessed or processed sometime earlier but not yet present in current docs_in_use)
    all_docs_to_check = list(set(docs_in_atts + doc_paths_or_links))
    docs_and_types = get_docs_to_process(all_docs_to_check, all_docs_info, docs_in_use_info)
    all_docs_info_new, docs_combination_ids_new = {}, {}
    docs_in_use_info_new = []
    # check if we need to process anything
    if docs_and_types:
        for file_source in docs_and_types.keys():
            file_source_type = docs_and_types[file_source]
            # if we have processed text for this file, file_source_type is its id
            # then we just save the id of existing processed file to add it to docs_in_use later
            if file_source_type != "link" and file_source_type != "path":
                file_id = file_source_type
            # if we don't have processed text for this file
            else:
                file_id = generate_unique_file_id(10, dialog_id)
                all_docs_info_new[file_id] = {"initial_path_or_link": file_source}
                if file_source_type == "link":
                    # without verify=False, downloading files from our service does not work
                    orig_file = requests.get(file_source, timeout=FILE_SERVER_TIMEOUT, verify=False)
                    content_headers = orig_file.headers.get("Content-disposition", "filename=NoNameFile")
                    filename = re.search(FIND_FILENAME, content_headers)
                    if filename:
                        filename = filename.group(1)
                    else:
                        filename = "No Name (filename possibly lost)"
                    file_extension = PurePath(file_source).suffix
                    if not file_extension:
                        try:
                            file_extension = filetype.guess(orig_file.content).extension
                        # for some reason filetype always fails to get extension for .txt files
                        # thus if we didn't get an extension, we just assume that the file is .txt
                        except Exception:
                            file_extension = "txt"
                    orig_file_text = get_text_from_fileobject(orig_file, file_extension)
                    file_text_with_filename = f"***FILENAME: {filename}***\n{orig_file_text}"
                elif file_source_type == "path":
                    orig_file_text = get_text_from_filepath(file_source)
                    filename = PurePath(file_source).stem
                    file_text_with_filename = f"***FILENAME: {filename}***\n{orig_file_text}"
                doc_text_link = upload_document(
                    file_text_with_filename, f"{file_id}.txt", FILE_SERVER_URL, FILE_SERVER_TIMEOUT, type_ref="text"
                )
                all_docs_info_new[file_id]["processed_text_link"] = doc_text_link
                all_docs_info_new[file_id]["filename"] = filename
            docs_in_use_info_new.append(file_id)
        if len(docs_in_use_info_new) > 1:
            doc_combination_id = generate_unique_file_id(10, dialog_id)
            docs_combination_ids_new[doc_combination_id] = docs_in_use_info_new
    return docs_in_use_info_new, all_docs_info_new, docs_combination_ids_new
