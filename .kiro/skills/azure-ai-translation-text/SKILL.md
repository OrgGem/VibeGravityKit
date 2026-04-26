---
name: azure-ai-translation-text
description: "Azure AI Text Translation — real-time text translation, language detection, and transliteration via REST API. Use for in-app translation features with Azure Cognitive Services."
user-invocable: true
risk: safe
---

# Azure AI Text Translation

Real-time text translation supporting 100+ languages using Azure Cognitive Services Translator API.

## When to Use
- Translating short text strings or UI content in real time
- Auto-detecting source language
- Transliterating text between scripts (e.g., Arabic to Latin)
- Building multilingual chat or content applications

## Setup

```bash
pip install azure-ai-translation-text
```

```python
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

client = TextTranslationClient(
    credential=AzureKeyCredential(os.environ["AZURE_TRANSLATOR_KEY"]),
    region=os.environ["AZURE_TRANSLATOR_REGION"]
)
```

## Basic Translation

```python
response = client.translate(
    body=["Hello, world!", "How are you?"],
    to_language=["fr", "es"],
    from_language="en"
)
for item in response:
    for translation in item.translations:
        print(f"[{translation.to}] {translation.text}")
```

## Language Detection

```python
response = client.detect_language(body=["Bonjour le monde"])
print(response[0].language, response[0].confidence)
```

## Transliteration

```python
response = client.transliterate(
    body=["こんにちは"],
    language="ja",
    from_script="Jpan",
    to_script="Latn"
)
```

## Best Practices
- Cache supported languages list (`client.get_languages()`) — changes infrequently
- Batch up to 100 strings per request for efficiency
- Use `text_type="html"` when translating HTML to preserve tags
