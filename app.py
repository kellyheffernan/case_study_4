import os

import gradio as gr
from google import genai
from google.genai import types


REMOTE_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")

MAX_OUTPUT_TOKENS = 900

fancy_css = """
.gradio-container {
    width: 96% !important;
    max-width: none !important;
    background: url("/gradio_api/file=cute_kitchen_background.png") center / cover fixed !important;
}
#app-title,
#app-subtitle,
#model-note {
    background: var(--block-background-fill);
    color: var(--body-text-color);
    padding: var(--block-padding);
    border-radius: var(--block-radius);
}
#app-title,
#app-subtitle {
    text-align: center;
}
@media (max-width: 768px) {
    .gradio-container {
        width: 98% !important;
    }
}
"""


def normalize_history(history):
    normalized = []

    for item in history:
        content = item["content"]

        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )

        normalized.append({"role": item["role"], "content": content})

    return normalized


def create_vertex_client():
    if not GOOGLE_CLOUD_PROJECT:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT must be configured for Vertex AI."
        )

    return genai.Client(
        enterprise=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
        http_options=types.HttpOptions(api_version="v1"),
    )


def to_vertex_contents(history, message, time_required, pantry_staples):
    contents = []

    for item in normalize_history(history):
        role = "model" if item["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=item["content"])],
            )
        )

    pantry_text = ", ".join(pantry_staples) if pantry_staples else "None selected"
    user_prompt = (
        f"{message}\n\n"
        f"Time Required: {time_required or 'Not specified'}\n"
        f"Pantry Staples Available: {pantry_text}"
    )
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_prompt)],
        )
    )

    return contents


def respond(
    message,
    history: list[dict[str, str]],
    system_message,
    time_required,
    pantry_staples,
):
    try:
        client = create_vertex_client()
        contents = to_vertex_contents(
            history,
            message,
            time_required,
            pantry_staples,
        )
        response = ""

        for chunk in client.models.generate_content_stream(
            model=REMOTE_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_message,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        ):
            response += chunk.text or ""
            yield response
    except Exception as error:
        yield f"Error: {error}"


with gr.Blocks() as demo:
    gr.Markdown(
        "# 🍽️ What's For Dinner?",
        elem_id="app-title",
    )

    gr.Markdown(
        "**Don't know what to make for dinner? Plan your meals with our chatbot. "
        "Select the time you have and input your ingredients or special requests.**",
        elem_id="app-subtitle",
    )

    time_required = gr.Dropdown(
        choices=["20 minutes", "30 minutes", "1 hour", "2 hours"],
        value=None,
        label="How Much Time Do You Have?",
        elem_id="time-required",
    )

    pantry_staples = gr.CheckboxGroup(
        choices=[
            "Salt",
            "Pepper",
            "Olive Oil",
            "Butter",
            "Garlic",
            "Onions",
            "Peppers",
            "Rice",
            "Pasta",
            "Eggs",
            "Flour",
            "Sugar",
            "Milk",
            "Cheese",
            "Tomatoes",
            "Bread",
            "Vinegar",
        ],
        label="Which Pantry Staples Do You Have?",
        elem_id="pantry-staples",
    )

    system_message = gr.Textbox(
        value=(
            "You are a recipe assistant chatbot. Use the user's input ingredients, "
            "checked pantry staples, and cooking time to suggest 1 recipe that can be "
            "made within the amount of time specified. If you suggest ingredients that "
            "the user does not explicitly have, list these as optional."
        ),
        label="System message",
        render=False,
    )

    with gr.Column(elem_id="chat-container"):
        gr.ChatInterface(
            fn=respond,
            additional_inputs=[
                system_message,
                time_required,
                pantry_staples,
            ],
        )


if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Soft(),
        css=fancy_css,
        allowed_paths=["cute_kitchen_background.png"],
        server_name="0.0.0.0",
        server_port=7860,
    )
