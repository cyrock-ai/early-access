# Data Faker (`DATA_FAKER`)

Generates synthetic test data and returns it as a JSON array.

**Category:** Data Sources · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Result (`out_result`) | Output | A JSON array of generated rows |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port |

No input port — it generates rather than transforms.

## Properties

| Field | Required | Meaning |
|---|---|---|
| Provider (`provider`) | **Yes** | The data category to generate, chosen from a list |
| Fields (`fields`) | **Yes** | Which fields to include in each row, chosen from the provider's set |
| Row Count (`rowCount`) | **Yes** | How many rows to generate |

## Use cases

- **Developing a pipeline before real data exists** — stand in for a SQL Database or API Call while you get
  the downstream logic right.
- **Load and shape testing:** generate 500 rows and confirm your Iterator and Embedding chain holds up.
- **Demos** without exposing production data.

## Notes

- All three fields are required; leaving any empty drops the module from the deployment.
- Fields depend on the chosen Provider — pick the Provider first.
- This is a development aid. Replace it with the real source before going live; nothing warns you if a
  production pipeline is still fed synthetic data.
