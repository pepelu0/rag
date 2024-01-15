import os
import argparse
import json
from pathlib import Path
from .openai_access import call_chatgpt

def build_hierarchy_heading(paragraphs, openai_api_base, openai_api_key, openai_api_type, openai_api_version, openai_engine):
    hierarchy_heading_prompt_template = ""
    with open(os.path.join(os.getcwd(), os.path.dirname(__file__), "hierarchy_heading_prompt_template.txt"), "r", encoding='utf-8') as f:
        hierarchy_heading_prompt_template = f.read()

    heading = []
    for paragraph in paragraphs:
       if paragraph["role"] == "sectionHeading" or paragraph["role"] == "title":
            heading.append(paragraph["content"])

    hierarchy_heading_prompt = hierarchy_heading_prompt_template.format(
        "\n".join(heading))
    print("Hierarchy heading prompt: ", hierarchy_heading_prompt)

    gpt_result_iterator = call_chatgpt(
        hierarchy_heading_prompt,
        openai_api_base,
        openai_api_key,
        openai_api_type,
        openai_api_version,
        openai_engine,
        0,
        1,
        16384,
        True) #16K tokens for results.

    gpt_result = ""
    for chunk in gpt_result_iterator:
        gpt_result += chunk

    print("GPT result: ", gpt_result)

    hierarchy_heading_strs = gpt_result.split("Hierarchy Headings:")[1].split("Notes:")[0].strip().split("\n")

    print("Start finding missing heading...")
    # TODO: find the missing heading
    print("Finish finding missing heading...")

    original_heading_content_str = "original_heading_content"
    tag_str = "tag"
    hierarchy_heading = []
    for line in hierarchy_heading_strs:
        original_heading_content_start_index = line.index(original_heading_content_str)+len("\""+original_heading_content_str+"\"")+2
        original_heading_content_end_index = -len(line)+line.index(tag_str)-4
        original_heading_content = line[original_heading_content_start_index:original_heading_content_end_index]
        if "\"" in original_heading_content:
            line = line[:original_heading_content_start_index] + original_heading_content.replace("\"", "\\\"") + line[original_heading_content_end_index:]
        print("Processing line: ", line)
        hierarchy_heading.append(json.loads(line))

    print("Start enriching hierarchy heading to input paragraphs...")
    heading_index = 0
    current_heading = [hierarchy_heading[heading_index]]
    removed_heading = []

    def trim_non_alphanumeric(s: str):
        # remove non-alphanumeric characters
        return ''.join(c for c in s if c.isalpha() or c.isdigit() or c == ' ')

    for paragraph in paragraphs:
        next_heading = heading_index + 1 < len(hierarchy_heading) and hierarchy_heading[heading_index + 1] or ""
        while next_heading != "" and next_heading["tag"] == "REMOVED_HEADING":
            # Skip removed heading
            heading_index += 1
            removed_heading.append(next_heading)
            next_heading = heading_index + 1 < len(hierarchy_heading) and hierarchy_heading[heading_index + 1] or ""
        if next_heading != "" and trim_non_alphanumeric(paragraph["content"]) == trim_non_alphanumeric(next_heading["original_heading_content"]):
            print("Next heading: ", json.dumps(next_heading))
            # Heading changed
            new_current_heading = []
            for ch in current_heading:
                if next_heading["hierarchy_number"].startswith(ch["hierarchy_number"]):
                    new_current_heading.append(ch)
                else:
                    break
            new_current_heading.append(next_heading)
            print("Heading changed...")
            print("==================Current heading: ", json.dumps(current_heading))
            print("==================New heading: ", json.dumps(new_current_heading))
            current_heading = new_current_heading
            heading_index += 1

        paragraph["heading"] = current_heading
    print("Finish enriching hierarchy heading to input paragraphs...")
    return hierarchy_heading

if __name__ == "__main__":
    print("Start hierarchy heading component")

    parser = argparse.ArgumentParser("hierarchy_heading")
    parser.add_argument("--paragraphs_data_path", type=str, help="Path to paragraph data")
    parser.add_argument("--openai_api_key", type=str, help="OpenAI API key")
    parser.add_argument("--openai_api_type", type=str, help="OpenAI API type")
    parser.add_argument("--openai_api_base", type=str, help="OpenAI API base")
    parser.add_argument("--openai_api_version", type=str, help="OpenAI API version")
    parser.add_argument("--openai_engine", type=str, help="OpenAI engine")
    parser.add_argument("--output_path", type=str, help="Path to paragraphs with hierarchy heading")
    args = parser.parse_args()

    paragraphs = []
    with open(args.paragraphs_data_path, "r", encoding='utf-8') as f:
        for line in f:
            paragraphs.append(json.loads(line))

    hierarchy_heading = build_hierarchy_heading(paragraphs, args.openai_api_base, args.openai_api_key, args.openai_api_type, args.openai_api_version, args.openai_engine)
 
    with open(os.path.join(args.output_path, "paragraphs_with_hierarchy_heading.jsonl"), "w") as f:
        for paragraph in paragraphs:
            f.write(json.dumps(paragraph))
            f.write("\n")

    with open(os.path.join(args.output_path, "hierarchy_heading.jsonl"), "w") as f:
        for l in hierarchy_heading:
            f.write(json.dumps(l))
            f.write("\n")