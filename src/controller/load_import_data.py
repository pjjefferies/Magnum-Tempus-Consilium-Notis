import base64
from html.parser import HTMLParser
from io import BytesIO
import os
from typing import Any, Optional, Protocol

from PIL import Image, UnidentifiedImageError


class LoggerProto(Protocol):
    def debug(self, msg: str) -> None:
        ...


class MyHTMLParser(HTMLParser):
    def __init__(
        self, *, convert_charrefs: bool = True, replace_tags_char: str = ""
    ) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.data: str = ""
        self.tags_to_skip: list[str] = [
            "en-note",
            "div",
            "br",
        ]  # ["note-attributes", "resource"]
        self.replace_tags_char: str = replace_tags_char

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # print(f"starttag:{tag=}")
        if self.replace_tags_char:
            # print(f"{self.replace_tags_char=}")
            self.data += self.replace_tags_char
            return
        if tag in self.tags_to_skip:
            return
        if attrs:
            # print(f"{attrs=}")
            self.data += f"<{tag} "
            for attrib in attrs:
                self.data += f' {attrib[0]}="{attrib[1]}"'
                # print(f"{these_attrs=}")
            self.data += " />"
        else:
            self.data += f"<{tag}>"

    def handle_endtag(self, tag: str) -> None:
        # print(f"endtag:{tag=}")
        if self.replace_tags_char:
            self.data += self.replace_tags_char
            return
        if tag in self.tags_to_skip:
            return
        self.data += f"</{tag}>"

    def handle_data(self, data: str) -> None:
        # print(f"data:{data}")
        # if data in ["\n      ", "      \n    ", "\n"]:
        #     return
        # self.data += f"Data: '{data}'"
        self.data += f"{data}"

    def handle_decl(self, decl: str) -> None:
        if self.replace_tags_char:
            self.data += self.replace_tags_char
            return
        # print(f"Found decl. Ignoring. Data: {decl=}")


def read_input_file(path: str):
    import xml.etree.ElementTree as ET

    # Parse the XML file
    tree = ET.parse(path)

    # Get the root of the XML document
    root = tree.getroot()

    # Iterate over the children of the root node
    # for child in root:
    #     print(child.tag, child.text)

    return root


def save_image(image_data: dict[str, str]) -> bool:
    try:
        image = Image.open(BytesIO(base64.b64decode(image_data["data"])))
    except UnidentifiedImageError:
        print(
            f"Could not create image with filename: {image_data['file_name']} and hash: {image_data['hash']}"
        )
        return False
    if image_data["file_name"] is None:
        print(f"{image_data=}")
    filename_base_old: str = ".".join(image_data["file_name"].split(".")[:-1])
    # print(f"{filename_base_old=}")
    filename_base_new: str = "_".join((filename_base_old, image_data["hash"]))
    filename_ext: str = image_data["file_name"].split(".")[-1]
    filename: str = ".".join((filename_base_new, filename_ext))
    folder: str = "data\images"
    filepath: str = os.path.join(folder, filename)
    # print(f"{filepath=}")
    try:
        image.save(fp=filepath)
    except OSError as e:
        print(
            f"Cannot save image with filename: {image_data['file_name']} and hash: {image_data['hash']} due to error: {e}"
        )
    return True


def load_enex_backup(
    filepath: str,
    logger: LoggerProto,
    max_notes_to_read: Optional[int] = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Returns two lists of dictionaries
        - List of Notes, each as a dictionary
        - List of Resources, mainly pictures, as dictionary with picture as base64 text
    """

    data = read_input_file(path=filepath)
    notes: list[dict[str, Any]] = []
    resources: list[dict[str, str]] = []
    # parser.feed('<html><head><title>Test</title></head>'
    #             '<body><h1>Parse me!</h1></body></html>')

    for note_no, note in enumerate(data):
        # if note_no == 0:  # Skip export note
        #     continue
        # print(f"\nNote No.: {note_no}")
        this_note: dict[str, str | list[str]] = {}

        for field in note:
            match field.tag:
                case "content":
                    parser = MyHTMLParser()
                    field_text_stripped: str = field.text.strip()
                    # print(f"content:{field_text_stripped=}")
                    parser.feed(field_text_stripped)
                    temp = parser.data.strip()
                    # print(f"content:{temp=}")
                    this_note[field.tag] = temp
                case "resource":
                    image_data: dict[str, str] = {}
                    for sub_field in field:
                        # print(f"{sub_field.tag=}")
                        match sub_field.tag:
                            case "data" | "mime" | "width" | "height":
                                image_data[sub_field.tag] = sub_field.text
                            case "resource-attributes":
                                for sub_sub_field in sub_field:
                                    match sub_sub_field.tag:
                                        case "file-name":
                                            image_data["file_name"] = sub_sub_field.text
                                            # print(f"{image_data['file_name']=}")
                                        case "source-url":
                                            image_data[
                                                "hash"
                                            ] = sub_sub_field.text.split("+")[2]
                                        case _:
                                            print(
                                                f"Ignoring image field: {sub_sub_field.tag=}"
                                            )
                                if image_data["file_name"] is None:
                                    image_data["file_name"] = ".".join(
                                        [
                                            image_data["hash"],
                                            image_data["mime"].split("/")[1],
                                        ]
                                    )
                                    print(
                                        f"image filename changed from None to {image_data['file_name']}"
                                    )
                            case _:
                                print(f"Ignoring image field: {sub_field.tag=}")
                    if len(image_data) == 6:
                        result: bool = save_image(image_data=image_data)
                        resources.append(image_data)
                    else:
                        print(
                            f"Didn't find all image data. Have: {image_data.keys()}, hash: {image_data['hash']}"
                        )
                case "note-attributes":
                    for sub_field in field:
                        this_note[sub_field.tag] = sub_field.text
                case _ if field.tag != "tag":
                    this_note[field.tag] = field.text
                case _:  # if field.tag == "tag"
                    if "tag" not in this_note:
                        this_note["tags"] = [field.text]
                    else:
                        this_note["tags"] = this_note["tags"] + [field.text]
        if this_note["title"] == "Untitled Note":
            parser = MyHTMLParser(replace_tags_char=".")
            parser.feed(this_note["content"])
            temp = parser.data.strip().strip(".")
            # print(f"{temp=}")
            new_title = temp.split(".")[0][
                :50
            ]  # First sentence of max length 50 characters, not including tags
            if new_title:
                this_note["title"] = new_title
            elif this_note["content"][:9] == "<en-media":
                this_note["title"] = "Saved Image"

        if (
            this_note["title"] not in ["Untitled Note", ""]
            or this_note["content"] != ""
        ):
            notes.append(this_note)
        else:
            print(
                f"Skipping note {note_no} due to empty title and content. {this_note=}"
            )

        if max_notes_to_read and (note_no >= max_notes_to_read):
            break

    return notes, resources


if __name__ == "__main__":
    from src.config.config_logging import logger

    filepath: str = "data/import_data/Evernote_Actions_2023-08-09.enex"
    MAX_NOTES_TO_READ: int = 25
    MAX_NOTES_TO_SHOW: int = 25

    notes, resources = load_enex_backup(
        filepath=filepath, max_notes_to_read=MAX_NOTES_TO_READ, logger=logger
    )

    note_no: int
    note_dict: dict[str, Any]

    for note_no, note_dict in enumerate(notes):
        print(f"\nNote No.: {note_no}:")
        print(f"{note_dict}")
        if note_no >= MAX_NOTES_TO_SHOW:
            break

    for resource_no, resource_dict in enumerate(resources):
        print(f"\Resource No.: {resource_no}:")
        print(f"{resource_dict['hash']=}, {resource_dict['file_name']=}")
        if resource_no >= MAX_NOTES_TO_SHOW:
            break

    print(f"{notes}")
