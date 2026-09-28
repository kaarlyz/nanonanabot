# Provider metadata catalog for 9Router
FEATURED_PROVIDERS = [
    {"id": "antigravity", "name": "Google Antigravity", "icon": "🚀", "type": "oauth", "desc": "Gemini / Claude Pro-Tier Pool (OAuth)"},
    {"id": "openai", "name": "OpenAI", "icon": "🟢", "type": "apikey", "desc": "GPT-4o, o1, o3-mini (Official API)"},
    {"id": "anthropic", "name": "Anthropic Claude", "icon": "🎭", "type": "apikey", "desc": "Claude 3.5 Sonnet / Haiku"},
    {"id": "gemini", "name": "Google Gemini API", "icon": "✨", "type": "apikey", "desc": "Gemini 2.5 / 2.0 Flash & Pro API"},
    {"id": "deepseek", "name": "DeepSeek", "icon": "🔵", "type": "apikey", "desc": "DeepSeek V3 & R1 Reasoning Engine"},
    {"id": "groq", "name": "Groq LPU", "icon": "⚡", "type": "apikey", "desc": "Ultra-fast Llama & Mixtral Inference"},
    {"id": "openrouter", "name": "OpenRouter", "icon": "🟠", "type": "apikey", "desc": "Aggregated Multi-model Gateway"},
    {"id": "cerebras", "name": "Cerebras", "icon": "🧠", "type": "apikey", "desc": "Fastest Llama Inference on Wafer Scale"},
    {"id": "together", "name": "Together AI", "icon": "🤝", "type": "apikey", "desc": "Open Source Model Cloud"},
    {"id": "fireworks", "name": "Fireworks AI", "icon": "🎆", "type": "apikey", "desc": "Fast Production Inference"},
    {"id": "mistral", "name": "Mistral AI", "icon": "🌪️", "type": "apikey", "desc": "Mistral Large, Codestral, Pixtral"},
    {"id": "xai", "name": "xAI (Grok)", "icon": "⚫", "type": "apikey", "desc": "Grok 2 / Grok Vision"},
    {"id": "perplexity", "name": "Perplexity AI", "icon": "🔍", "type": "apikey", "desc": "Sonar Online Search Models"},
    {"id": "cohere", "name": "Cohere", "icon": "🌿", "type": "apikey", "desc": "Command R+ & Embed Models"},
    {"id": "huggingface", "name": "Hugging Face", "icon": "🤗", "type": "apikey", "desc": "Inference Endpoints & Hub"},
    {"id": "siliconflow", "name": "SiliconFlow", "icon": "🌊", "type": "apikey", "desc": "Fast Chinese & Global Open Models"},
    {"id": "ollama", "name": "Ollama (Local)", "icon": "🦙", "type": "custom", "desc": "Local device models via private URL"},
    {"id": "custom", "name": "Custom Endpoint", "icon": "🌐", "type": "custom", "desc": "Any OpenAI-Compatible Base URL"}
]

PROVIDER_MAP = {p["id"]: p for p in FEATURED_PROVIDERS}
