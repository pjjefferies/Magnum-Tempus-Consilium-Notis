import base64
from html.parser import HTMLParser
from io import BytesIO
import os
from typing import Any

from PIL import Image


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
    image = Image.open(BytesIO(base64.b64decode(image_data["data"])))
    filename_base_old: str = ".".join(image_data["file_name"].split(".")[:-1])
    # print(f"{filename_base_old=}")
    filename_base_new: str = "_".join((filename_base_old, image_data["hash"]))
    filename_ext: str = image_data["file_name"].split(".")[-1]
    filename: str = ".".join((filename_base_new, filename_ext))
    folder: str = "data\images"
    filepath: str = os.path.join(folder, filename)
    # print(f"{filepath=}")
    image.save(fp=filepath)
    return True


if __name__ == "__main__":
    data = read_input_file("data/import_data/Evernote_Actions_2023-08-09.enex")
    data_list: list[dict[str, Any]] = []
    # parser.feed('<html><head><title>Test</title></head>'
    #             '<body><h1>Parse me!</h1></body></html>')

    for note_no, note in enumerate(data):
        # if note_no == 0:  # Skip export note
        #     continue
        # print(f"\nNote No.: {note_no}")
        new_note: dict[str, str | list[str]] = {}

        for field in note:
            match field.tag:
                case "content":
                    parser = MyHTMLParser()
                    field_text_stripped: str = field.text.strip()
                    # print(f"content:{field_text_stripped=}")
                    parser.feed(field_text_stripped)
                    temp = parser.data.strip()
                    # print(f"content:{temp=}")
                    new_note[field.tag] = temp
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
                            case _:
                                print(f"Ignoring image field: {sub_field.tag=}")
                    if len(image_data) == 6:
                        result: bool = save_image(image_data=image_data)
                        if result:
                            pass
                            # print(
                            #     f"Image data saved with data for tags: {image_data.keys()}"
                            # )
                        else:
                            pass
                            # print(
                            #     f"Image data not saved with data for tags: {image_data.keys()}"
                            # )
                    else:
                        print(f"Didn't find all image data. Have: {image_data.keys()}")
                case "note-attributes":
                    for sub_field in field:
                        new_note[sub_field.tag] = sub_field.text
                case _ if field.tag != "tag":
                    new_note[field.tag] = field.text
                case _:  # if field.tag == "tag"
                    if "tag" not in new_note:
                        new_note["tags"] = [field.text]
                    else:
                        new_note["tags"] = new_note["tags"] + [field.text]
        if new_note["title"] == "Untitled Note":
            parser = MyHTMLParser(replace_tags_char=".")
            parser.feed(new_note["content"])
            temp = parser.data.strip().strip(".")
            # print(f"{temp=}")
            new_title = temp.split(".")[0][
                :50
            ]  # First sentence of max length 50 characters, not including tags
            if new_title:
                new_note["title"] = new_title
            elif new_note["content"][:9] == "<en-media":
                new_note["title"] = "Saved Image"

        if new_note["title"] not in ["Untitled Note", ""] or new_note["content"] != "":
            data_list.append(new_note)
        else:
            print(
                f"Skipping note {note_no} due to empty title and content. {new_note=}"
            )

        if note_no >= 10:
            break

    note_no: int
    note_dict: dict[str, Any]

    for note_no, note_dict in enumerate(data_list):
        print(f"\n{note_no}:")
        print(f"{note_dict}")
        # if note_no >= 5:
        #     break
