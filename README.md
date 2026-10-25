# Helios
Helios is an AI-powered Django web application that simplifies website creation. Leveraging HTML5, CSS3, JavaScript, and Bootstrap 5, Helios allows users to generate responsive and visually appealing websites effortlessly.

## Publishing Sites

After iterating on a design in the chat interface, send a message starting with `launch` followed by a name. Helios will save the current website and make it available at `/sites/<name>`.

## OpenAI configuration

Set `OPENAI_API_KEY` in the environment of the Django server before starting Helios. Keep the key in your deployment secret manager or local shell environment; never commit it to this repository. Without a configured key, AI generation is unavailable.
