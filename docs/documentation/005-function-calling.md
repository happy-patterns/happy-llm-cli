---
id: DOC-005
title: OpenAI Responses API Function Calling Guide
description: Guide to using function calling with the OpenAI Responses API. Provider-specific.
tags: [function-calling, openai]
---

> **Note**: This guide covers function calling using OpenAI’s Responses API. Other LLM providers or APIs may differ.

## Function Calling in OpenAI’s Responses API

## Overview

Function calling provides a powerful and flexible way for OpenAI models to interface with your code or external services. This guide explains how to connect models to your custom code to fetch data or take action.

### Primary Use Cases

- **Fetching Data**: Retrieve up-to-date information to incorporate into the model's response (RAG). Useful for searching knowledge bases and retrieving specific data from APIs.
- **Taking Action**: Perform actions like submitting a form, calling APIs, modifying application state, or taking agentic workflow actions.

## Basic Example

```python
from openai import OpenAI

client = OpenAI()

tools = [{
    "type": "function",
    "name": "search_knowledge_base",
    "description": "Query a knowledge base to retrieve relevant info on a topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The user question or search query."
            },
            "options": {
                "type": "object",
                "properties": {
                    "num_results": {
                        "type": "number",
                        "description": "Number of top results to return."
                    },
                    "domain_filter": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "description": "Optional domain to narrow the search (e.g. 'finance', 'medical'). Pass null if not needed."
                    },
                    "sort_by": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "enum": [
                            "relevance",
                            "date",
                            "popularity",
                            "alphabetical"
                        ],
                        "description": "How to sort results. Pass null if not needed."
                    }
                },
                "required": [
                    "num_results",
                    "domain_filter",
                    "sort_by"
                ],
                "additionalProperties": False
            }
        },
        "required": [
            "query",
            "options"
        ],
        "additionalProperties": False
    }
}]

response = client.responses.create(
    model="gpt-4.1",
    input=[{"role": "user", "content": "Can you find information about ChatGPT in the AI knowledge base?"}],
    tools=tools
)

print(response.output)
```

Example output:

```json
[{
    "type": "function_call",
    "id": "fc_12345xyz",
    "call_id": "call_4567xyz",
    "name": "search_knowledge_base",
    "arguments": "{\"query\":\"What is ChatGPT?\",\"options\":{\"num_results\":3,\"domain_filter\":null,\"sort_by\":\"relevance\"}}"
}]
```

## Implementation Steps

### 1. Define a Function

First, implement the actual function in your codebase:

```python
import requests

def get_weather(latitude, longitude):
    response = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    data = response.json()
    return data['current']['temperature_2m']
```

### 2. Call the Model with Function Definition

```python
from openai import OpenAI
import json

client = OpenAI()

tools = [{
    "type": "function",
    "name": "get_weather",
    "description": "Get current temperature for provided coordinates in celsius.",
    "parameters": {
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"}
        },
        "required": ["latitude", "longitude"],
        "additionalProperties": False
    },
    "strict": True
}]

input_messages = [{"role": "user", "content": "What's the weather like in Paris today?"}]

response = client.responses.create(
    model="gpt-4.1",
    input=input_messages,
    tools=tools,
)
```

### 3. Model Returns Function Call

```json
[{
    "type": "function_call",
    "id": "fc_12345xyz",
    "call_id": "call_12345xyz",
    "name": "get_weather",
    "arguments": "{\"latitude\":48.8566,\"longitude\":2.3522}"
}]
```

### 4. Execute the Function

```python
tool_call = response.output[0]
args = json.loads(tool_call.arguments)

result = get_weather(args["latitude"], args["longitude"])
```

### 5. Supply Results Back to the Model

```python
input_messages.append(tool_call)  # append model's function call message
input_messages.append({                               # append result message
    "type": "function_call_output",
    "call_id": tool_call.call_id,
    "output": str(result)
})

response_2 = client.responses.create(
    model="gpt-4.1",
    input=input_messages,
    tools=tools,
)
print(response_2.output_text)
```

### 6. Final Response

```
"The current temperature in Paris is 14°C (57.2°F)."
```

## Defining Functions

Functions can be set in the `tools` parameter of each API request. A function is defined by its schema, which includes:

| Field | Description |
|-------|-------------|
| type | This should always be "function" |
| name | The function's name (e.g., get_weather) |
| description | Details on when and how to use the function |
| parameters | JSON schema defining the function's input arguments |
| strict | Whether to enforce strict mode for the function call |

### Example Function Schema

```json
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Retrieves current weather for the given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country e.g. Bogotá, Colombia"
                },
                "units": {
                    "type": "string",
                    "enum": [
                        "celsius",
                        "fahrenheit"
                    ],
                    "description": "Units the temperature will be returned in."
                }
            },
            "required": [
                "location",
                "units"
            ],
            "additionalProperties": false
        },
        "strict": true
    }
}
```

## Best Practices

### Writing Clear Function Definitions

- Write clear and detailed function names, parameter descriptions, and instructions
- Explicitly describe the purpose and format of each parameter
- Include examples and edge cases, especially to fix recurring failures

### Software Engineering Principles

- Make functions obvious and intuitive (principle of least surprise)
- Use enums and object structure to prevent invalid states
- Pass the "intern test" - can someone correctly use the function given only what you gave the model?

### Offload Work from the Model

- Don't make the model fill arguments you already know
- Combine functions that are always called in sequence

### Keep It Simple

- Keep the number of functions small for higher accuracy (aim for fewer than 20)
- Evaluate performance with different function counts

## Token Usage

Functions are injected into the system message and count against the model's context limit. They are billed as input tokens. If you run into token limits, consider:

- Limiting the number of functions
- Shortening parameter descriptions
- Using fine-tuning to reduce token usage with many functions

## Handling Function Calls

The model can make zero, one, or multiple function calls. A response with function calls will include an output array where entries with `type` of `function_call` will have:

- `call_id` (used to submit results)
- `name` (function name)
- `arguments` (JSON-encoded arguments)

### Example Response with Multiple Function Calls

```json
[
    {
        "id": "fc_12345xyz",
        "call_id": "call_12345xyz",
        "type": "function_call",
        "name": "get_weather",
        "arguments": "{\"location\":\"Paris, France\"}"
    },
    {
        "id": "fc_67890abc",
        "call_id": "call_67890abc",
        "type": "function_call",
        "name": "get_weather",
        "arguments": "{\"location\":\"Bogotá, Colombia\"}"
    },
    {
        "id": "fc_99999def",
        "call_id": "call_99999def",
        "type": "function_call",
        "name": "send_email",
        "arguments": "{\"to\":\"bob@email.com\",\"body\":\"Hi bob\"}"
    }
]
```

### Executing Multiple Function Calls

```python
for tool_call in response.output:
    if tool_call.type != "function_call":
        continue

    name = tool_call.name
    args = json.loads(tool_call.arguments)

    result = call_function(name, args)
    input_messages.append({
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": str(result)
    })

def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)
    if name == "send_email":
        return send_email(**args)
```

### Formatting Results

Results must be strings, but the format is up to you (JSON, error codes, plain text, etc.). For functions with no return value, simply return a success or failure message.

### Incorporating Results into Response

```python
response = client.responses.create(
    model="gpt-4.1",
    input=input_messages,
    tools=tools,
)
```

Example final response:

```
"It's about 15°C in Paris, 18°C in Bogotá, and I've sent that email to Bob."
```

## Additional Configurations

### Tool Choice

Control when and how tools are used with the `tool_choice` parameter:

- **Auto** (Default): Call zero, one, or multiple functions. `tool_choice: "auto"`
- **Required**: Call one or more functions. `tool_choice: "required"`
- **Forced Function**: Call exactly one specific function. `tool_choice: {"type": "function", "name": "get_weather"}`

You can also set `tool_choice` to `"none"` to imitate the behavior of passing no functions.

### Parallel Function Calling

The model may call multiple functions in a single turn. To prevent this, set `parallel_tool_calls` to `false`, ensuring exactly zero or one tool is called.

**Note**: When the model calls multiple functions in one turn, strict mode is disabled for those calls.

**Note for gpt-4.1-nano-2025-04-14**: This snapshot can sometimes include multiple tool calls for the same tool if parallel tool calls are enabled. It's recommended to disable this feature for this nano snapshot.

### Strict Mode

Setting `strict` to `true` ensures function calls adhere to the function schema. It's recommended to always enable strict mode.

Requirements for strict mode:

- `additionalProperties` must be set to `false` for each object in the parameters
- All fields in `properties` must be marked as `required`
- Optional fields can be denoted by adding `null` as a type option

```json
{
    "type": "function",
    "name": "get_weather",
    "description": "Retrieves current weather for the given location.",
    "strict": true,
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and country e.g. Bogotá, Colombia"
            },
            "units": {
                "type": ["string", "null"],
                "enum": ["celsius", "fahrenheit"],
                "description": "Units the temperature will be returned in."
            }
        },
        "required": ["location", "units"],
        "additionalProperties": false
    }
}
```

Limitations of strict mode:

- Some JSON schema features aren't supported
- Schemas undergo additional processing on first request (then cached)
- Schemas are cached and not eligible for zero data retention

## Streaming

Streaming can show progress by displaying which function is called and its arguments in real-time.

```python
from openai import OpenAI

client = OpenAI()

tools = [{
    "type": "function",
    "name": "get_weather",
    "description": "Get current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and country e.g. Bogotá, Colombia"
            }
        },
        "required": [
            "location"
        ],
        "additionalProperties": False
    }
}]

stream = client.responses.create(
    model="gpt-4.1",
    input=[{"role": "user", "content": "What's the weather like in Paris today?"}],
    tools=tools,
    stream=True
)

for event in stream:
    print(event)
```

Example output events:

```
{"type":"response.output_item.added","response_id":"resp_1234xyz","output_index":0,"item":{"type":"function_call","id":"fc_1234xyz","call_id":"call_1234xyz","name":"get_weather","arguments":""}}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":"{\""}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":"location"}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":"\":\""}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":"Paris"}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":","}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":" France"}
{"type":"response.function_call_arguments.delta","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"delta":"\"}"}
{"type":"response.function_call_arguments.done","response_id":"resp_1234xyz","item_id":"fc_1234xyz","output_index":0,"arguments":"{\"location\":\"Paris, France\"}"}
{"type":"response.output_item.done","response_id":"resp_1234xyz","output_index":0,"item":{"type":"function_call","id":"fc_1234xyz","call_id":"call_2345abc","name":"get_weather","arguments":"{\"location\":\"Paris, France\"}"}}
```

### Event Types

When streaming function calls, there are several event types:

1. `response.output_item.added`: Emitted for each function call, containing:
   - `response_id`: ID of the response the function call belongs to
   - `output_index`: Index of the output item in the response
   - `item`: In-progress function call item (includes name, arguments, id)

2. `response.function_call_arguments.delta`: Contains delta of arguments field:
   - `response_id`: Response ID
   - `item_id`: Function call item ID
   - `output_index`: Output item index
   - `delta`: Delta of arguments field

### Accumulating Tool Call Deltas

```python
final_tool_calls = {}

for event in stream:
    if event.type === 'response.output_item.added':
        final_tool_calls[event.output_index] = event.item;
    elif event.type === 'response.function_call_arguments.delta':
        index = event.output_index

        if final_tool_calls[index]:
            final_tool_calls[index].arguments += event.delta
```

Example accumulated tool call:

```json
{
    "type": "function_call",
    "id": "fc_1234xyz",
    "call_id": "call_2345abc",
    "name": "get_weather",
    "arguments": "{\"location\":\"Paris, France\"}"
}
```

When the model finishes calling functions, an event of type `response.function_call_arguments.done` is emitted, containing the entire function call.
