---
name: azure-ai-translation-document
description: "Azure AI Document Translation — batch translate entire documents (PDF, DOCX, PPTX) preserving layout and formatting. Use for bulk document translation workflows with Azure Cognitive Services."
user-invocable: true
risk: safe
---

# Azure AI Document Translation

Batch translate entire documents while preserving formatting, layout, and structure using Azure Cognitive Services Document Translation API.

## When to Use
- Translating PDF, DOCX, PPTX, XLSX, HTML files at scale
- Preserving document structure (tables, headers, footnotes)
- Batch processing multiple documents asynchronously
- Custom glossary or translation model integration

## Setup

```bash
pip install azure-ai-translation-document
```

```python
from azure.ai.translation.document import DocumentTranslationClient
from azure.core.credentials import AzureKeyCredential

client = DocumentTranslationClient(
    endpoint=os.environ["AZURE_DOCUMENT_TRANSLATION_ENDPOINT"],
    credential=AzureKeyCredential(os.environ["AZURE_DOCUMENT_TRANSLATION_KEY"])
)
```

## Batch Translation

```python
poller = client.begin_translation(
    source_url="https://<storage>.blob.core.windows.net/source?<sas>",
    target_url="https://<storage>.blob.core.windows.net/target?<sas>",
    target_language="fr"
)
result = poller.result()
for doc in result:
    print(f"{doc.source_document_url} -> {doc.status} ({doc.translated_to})")
```

## Supported Formats
PDF, DOCX, PPTX, XLSX, ODT, HTML, Markdown, TXT, XLIFF

## Best Practices
- Use SAS tokens with minimum required permissions
- Store credentials in Azure Key Vault or environment variables
- Monitor status with `poller.status()` for large batches
- Use custom glossaries (TSV format) for domain-specific terminology
