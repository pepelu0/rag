import os
import argparse
import json
from .hierarchy_heading_building.hierarchy_heading_component import build_hierarchy_heading

class SemanticChunkingSplitter():
    """A document splitter based on the document intelligence analyzer result.

    The input format should be an array of:
    [
        {
            "role": "...", //title, sectionHeading, null, pageFooter, pageHeader, pageNumber
            "content": "...", //content of the paragraph
        },
        ...
    ]

    The output format should be an array of:
    [
        {
            "content": "...", //content of the splitted document 
            "heading": "..." //hierarchy heading of the splitted document, in format of Title1->Title1.1->Title1.1.1
        }
    ]
    """

    def __init__(self, max_chunk_size, openai_api_base, openai_api_key, openai_api_type, openai_api_version, openai_engine):
        self._max_chunk_size = max_chunk_size
        self._openai_api_base = openai_api_base
        self._openai_api_key = openai_api_key
        self._openai_api_type = openai_api_type
        self._openai_api_version = openai_api_version
        self._openai_engine = openai_engine
        self._length_function = lambda x: len(x)

    def split(self, paragraphs):
        # Build hierarchy heading
        print("Start building hierarchy heading...")
        build_hierarchy_heading(
            paragraphs,
            self._openai_api_base,
            self._openai_api_key,
            self._openai_api_type,
            self._openai_api_version,
            self._openai_engine)

        print("Start splitting document...")
        splitted_chunks = []
        chunk_content = ""
        chunk_heading = ""
        def section_end(previous_heading, current_heading):
            """ Whether we hit a section end.

            For example:

            Case 1:
                Previous hierarchy heading: 1
                Current hierarchy heading: 1.1

                This is not a section end.
            
            Case 2:
                Previous hierarchy heading: 1.1
                Current hierarchy heading: 1.2 or 2

                This is a section end.

            """
            if previous_heading == "":
                return False
            if current_heading == "":
                return True
            return not current_heading["hierarchy_number"].startswith(previous_heading["hierarchy_number"])

        previous_heading = ""
        for paragraph in paragraphs:
            if self._length_function(chunk_content) + self._length_function(paragraph["content"]) > self._max_chunk_size or section_end(previous_heading, paragraph["heading"][-1]):
                # Save the chunk when one of the following conditions is met:
                # 1. The chunk is full
                # 2. We hit a section end
                chunk = {
                    "content": chunk_content,
                    "metadata": {
                        "heading": chunk_heading,
                    }
                }
                print("Save current chunk: ", chunk)
                splitted_chunks.append(chunk)
                chunk_content = ""
                chunk_heading = ""

            if self._length_function(paragraph["content"]) > self._max_chunk_size:
                # If the paragraph is too large, split it into multiple chunks
                # TODO: Use text splitter to split then paragraph and save the chunk
                print("The paragraph is too large, split it into multiple chunks")
                pass

            chunk_content += paragraph["content"] + "\n"
            temp = ""
            for heading in paragraph["heading"]:
                temp += heading["original_heading_content"] + "->"
            chunk_heading = temp[:-2]
            previous_heading = paragraph["heading"][-1]

        return splitted_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser("data_chunking")
    parser.add_argument("--paragraphs_file_path", type=str, help="Path to extracted data for chunking.")
    parser.add_argument("--max_chunk_size", type=int, help="Max chunk size.")
    parser.add_argument("--openai_api_key", type=str, help="OpenAI API key")
    parser.add_argument("--openai_api_type", type=str, help="OpenAI API type")
    parser.add_argument("--openai_api_base", type=str, help="OpenAI API base")
    parser.add_argument("--openai_api_version", type=str, help="OpenAI API version")
    parser.add_argument("--openai_engine", type=str, help="OpenAI engine")
    parser.add_argument("--output", type=str, help="Path to chunked data.")
    args = parser.parse_args()

    paragraphs = []
    with open(args.paragraphs_file_path, "r", encoding='utf-8') as f:
        # load jsonl file
        for line in f:
            paragraphs.append(json.loads(line))

    semantic_chunking_splitter = SemanticChunkingSplitter(
        max_chunk_size=args.max_chunk_size,
        openai_api_base=args.openai_api_base,
        openai_api_key=args.openai_api_key,
        openai_api_type=args.openai_api_type,
        openai_api_version=args.openai_api_version,
        openai_engine=args.openai_engine)
    splitted_chunks = semantic_chunking_splitter.split(paragraphs)

    with open(os.path.join(args.output, "chunks.jsonl"), "w") as f:
        for chunk in splitted_chunks:
            f.write(json.dumps(chunk))
            f.write("\n")