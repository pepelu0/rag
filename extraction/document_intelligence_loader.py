import os
import argparse
import json
from pathlib import Path
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

class DocumentIntelligenceLoader:
    def __init__(self, di_endpoint, di_key):
        self._di_endpoint = di_endpoint
        self._di_key = di_key

    def load(self, document_path):
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=self._di_endpoint, credential=AzureKeyCredential(self._di_key)
        )

        with open(document_path, "rb") as f:
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-layout", analyze_request=f, locale="en-US", content_type="application/octet-stream"
            )
            result = poller.result()
            return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_data", type=str, help="Path to source data for indexing")
    parser.add_argument("--cognitive_service_key", type=str, help="Cognitive service key")
    parser.add_argument("--cognitive_service_endpoint", type=str, help="Cognitive service endpoint")
    parser.add_argument("--content_output", type=str, help="Path to content output")
    parser.add_argument("--paragraphs_output", type=str, help="Path to paragraphs output")
    args = parser.parse_args()

    source_data = args.source_data
    content_output = args.content_output
    paragraphs_output = args.paragraphs_output
    end_point = args.cognitive_service_endpoint
    key = args.cognitive_service_key

    di_loader = DocumentIntelligenceLoader(end_point, key)
    result = di_loader.load(args.source_data)
    with open(f"{paragraphs_output}/paragraphs.jsonl", "w") as f:
        for paragraph in result.paragraphs:
            f.write(json.dumps({
                "role": paragraph.role,
                "content": paragraph.content
                }))
            f.write("\n")

    print("Finish saving paragraphs: ", f"{paragraphs_output}/{filename.split('.')[0]}-paragraphs.json")