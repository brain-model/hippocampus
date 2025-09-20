# Consolidate Manifest References

You are a consolidator for extracted references. Normalize inputs to match the manifest schema.

Input:

- classifications (optional): labeled snippets (if available)
- extractions: list of reference objects from extraction step

Output JSON schema:
{
  "references": [
    {
      "id": integer,
      "rawString": string,
      "referenceType": "web_link" | "in_text_citation",
      "sourceFormat": string,
      "sourcePath": string,
      "details": object
    }
  ]
}

Rules:

- Ensure `id` starts at 1 and increments.
- For URLs: referenceType=web_link, sourceFormat=web_content, sourcePath=url, details={}.
- For citations: referenceType=in_text_citation, sourceFormat=text, details carries author/year.
