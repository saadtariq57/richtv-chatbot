# LLM Module

Simple and clean separation of concerns for LLM interactions.

## Architecture

```
app/llm/
├── client.py      # LLM API abstraction (provider-agnostic)
├── generator.py   # Business logic (prompts, parsing)
└── README.md      # This file
```

## Usage

### Basic Usage

```python
from app.llm.client import get_llm_client

# Get the singleton client
llm = get_llm_client()

# Generate text
response = llm.generate("What is a stock?")
print(response)
```

### Async Usage

```python
from app.llm.client import get_llm_client

llm = get_llm_client()
response = await llm.generate_async("What is a stock?")
```

## Swapping LLM Providers

To switch from Gemini to another provider (OpenAI, Anthropic, local model), just modify `client.py`:

### Example: OpenAI

```python
class LLMClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.api_key = settings.openai_api_key  # Change this
        self.model = "gpt-4"  # Change this
        self.base_url = "https://api.openai.com/v1"  # Change this
    
    def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        # ... rest of implementation
```

### Example: Local Model (Ollama)

```python
class LLMClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.base_url = "http://localhost:11434"  # Ollama default
        self.model = "llama3"
    
    def generate(self, prompt: str, temperature: float = 0.3) -> Optional[str]:
        url = f"{self.base_url}/api/generate"
        body = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        # ... rest of implementation
```

## Design Principles

1. **Single Responsibility**: `client.py` handles API calls, `generator.py` handles business logic
2. **Provider Agnostic**: Easy to swap LLM providers without changing business logic
3. **Singleton Pattern**: One client instance reused across the app
4. **Simple Interface**: Just `generate()` and `generate_async()`
5. **No Dependencies**: Business logic doesn't know about API details

