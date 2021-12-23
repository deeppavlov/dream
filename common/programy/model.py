from typing import Union
import pathlib
import uuid
import logging
import re

from programy.clients.embed.basic import EmbeddedDataFileBot

logger = logging.getLogger(__name__)


spaces_patter = re.compile(r"\s+", re.IGNORECASE)
special_symb_patter = re.compile(r"[^a-zа-я0-9 ]", re.IGNORECASE)


class DataFileBot(EmbeddedDataFileBot):
    def ask_question(self, userid, question):
        client_context = self.create_client_context(userid)
        return self.renderer.render(client_context, self.process_question(client_context, question))

    def __call__(self, texts):
        userid = uuid.uuid4().hex
        for text in texts:
            logger.info(f"{text=}")
            text = special_symb_patter.sub("", spaces_patter.sub(" ", text.lower())).strip()
            response = self.ask_question(userid, text)
            logger.info(f"{response=}")
        response = response if response else ""
        return response


def path_filter(path: Union[pathlib.Path, list]):
    if isinstance(path, list):
        return [path_filter(i) for i in path if path_filter(i)]
    if isinstance(path, pathlib.Path):
        if path.exists() and path.is_dir() and [path_filter(i) for i in path.glob("./*") if path_filter(i)]:
            return path
        elif path.exists() and path.is_file():
            return path


def get_configuration_files(storage: pathlib.Path = pathlib.Path("data")):
    storage = pathlib.Path(storage)
    files = {
        "aiml": [storage / "categories"],
        "learnf": [storage / "categories/learnf"],
        "sets": [storage / "sets"],
        "maps": [storage / "maps"],
        "rdfs": [storage / "rdfs"],
        "properties": storage / "properties/properties.txt",
        "defaults": storage / "properties/defaults.txt",
        "denormals": storage / "lookups/denormal.txt",
        "normals": storage / "lookups/normal.txt",
        "genders": storage / "lookups/gender.txt",
        "persons": storage / "lookups/person.txt",
        "person2s": storage / "lookups/person2.txt",
        "triggers": storage / "triggers/triggers.txt",
        "regexes": storage / "regex/regex-templates.txt",
        "usergroups": storage / "security/usergroups.yaml",
        "spellings": storage / "spelling/corpus.txt",
        "preprocessors": storage / "processing/preprocessors.conf",
        "postprocessors": storage / "processing/postprocessors.conf",
        "postquestionprocessors": storage / "processing/postquestionprocessors.conf",
        "licenses": storage / "licenses/license.keys",
        "conversations": storage / "conversations",
        "duplicates": storage / "debug/duplicates.txt",
        "errors": storage / "debug/errors.txt",
        "services": storage / "services",
    }
    files = {name: path_filter(path) for name, path in files.items()}
    files = {name: path for name, path in files.items() if path}

    for name in files:
        files[name] = str(files[name]) if isinstance(files[name], pathlib.Path) else [str(i) for i in files[name]]
    return files


def get_programy_model(storage: pathlib.Path = pathlib.Path("data")):
    return DataFileBot(get_configuration_files(storage), defaults=True)
