# llm_service.py

import json


def clean_json_output(raw_output):
    raw_output = raw_output.strip()

    if raw_output.startswith("```"):
        raw_output = (
            raw_output
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    return raw_output


def call_llm_json(client, model, system_prompt, user_prompt):
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_output = response.output_text.strip()
    cleaned_output = clean_json_output(raw_output)

    return json.loads(cleaned_output), raw_output