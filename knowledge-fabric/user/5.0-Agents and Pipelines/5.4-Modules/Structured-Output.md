# Structured Output (`STRUCTURED_OUTPUT`)

Uses an LLM to turn unstructured text into a structured JSON array.

**Category:** Data Sources · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Text (`in_text`) | Input | The unstructured text to extract from |
| Result (`out_result`) | Output | A JSON array |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Model Provider (`model.provider`) | **Yes** | `OLLAMA` or `OPEN_AI` |
| Model Name (`model.name`) | **Yes** | Model identifier |
| Model URL (`model.url`) | **Yes** | Base URL of the endpoint |
| API Key (`model.apiKey`) | No | Required for `OPEN_AI` |
| Model Timeout (`model.timeoutMinutes`) | No | Minutes, 1–120, default 20 |
| Input (`inputText`) | No | Default text used when no upstream module provides input |
| Expected JSON Schema (`jsonSchema`) | No | JSON Schema for each array element — guides the extraction. Empty lets the model infer a shape |

## Use cases

- **Turning prose into rows:** an email or report becomes a JSON array you can iterate.
- **Extraction before branching** — produce JSON so a [Validator](Validator.md) in `CONDITION` mode has a
  field to test.
- **Normalising varied inputs** into one consistent shape for downstream processing.

## Notes

- **Supply the Expected JSON Schema whenever the downstream steps depend on specific field names.** Without
  it the model infers a structure, and the field names may change between runs — which quietly breaks a
  Validator or Template that expects a fixed key.
- The output is always an **array**, even for a single extracted record. Pair with
  [Iterator](Iterator.md) to process the elements.
- This is a model call, with the usual cost and latency. For mechanical reshaping, a
  [Python Script](Python-Script.md) is cheaper and deterministic.
