# Spring AI example: AI note assistant

A small Spring Boot app that uses [Spring AI](https://docs.spring.io/spring-ai/reference/) with Anthropic's Claude to add AI features to notes.
It is separate from `note-app/`. Spring AI needs Spring Boot 4 and Java 17+, and `note-app` still uses Spring Boot 2.1 and Java 8.

| Endpoint | Spring AI feature | What it does |
|---|---|---|
| `POST /api/ai/summarize` | Plain prompt -> `String` | Summarizes a note in two sentences |
| `POST /api/ai/analyze` | Structured output -> Java `record` | Returns a suggested title, a summary, tags and action items as JSON |
| `POST /api/ai/ask` | Tool calling (`@Tool`) | Claude searches, lists or creates notes to answer you |
| `POST /api/ai/chat` | Chat memory advisor | A multi-turn chat that remembers earlier messages per `conversationId` |

## Run it

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # from https://console.anthropic.com
cd spring-ai-example
mvn spring-boot:run                  # starts on http://localhost:8084
```

## Try it

```bash
curl -s localhost:8084/api/ai/summarize -H 'Content-Type: application/json' \
  -d '{"title":"Trip","content":"Book train to Mysore on 12th, pack charger, call hotel to confirm late check-in."}'

curl -s localhost:8084/api/ai/analyze -H 'Content-Type: application/json' \
  -d '{"title":"misc","content":"Ravi to fix login bug by Wed. Demo for customer Thursday. Need new logo."}'
# -> {"suggestedTitle":"...","summary":"...","tags":["..."],"actionItems":["..."]}

curl -s localhost:8084/api/ai/ask -H 'Content-Type: application/json' \
  -d '{"question":"Who has to do something before Thursday, according to my notes?"}'

curl -s localhost:8084/api/ai/ask -H 'Content-Type: application/json' \
  -d '{"question":"Save a note reminding me to renew my passport next month"}'

curl -s localhost:8084/api/ai/chat -H 'Content-Type: application/json' \
  -d '{"conversationId":"u1","message":"My name is Anjana. Give me one tip for organizing notes."}'
curl -s localhost:8084/api/ai/chat -H 'Content-Type: application/json' \
  -d '{"conversationId":"u1","message":"What is my name?"}'
```

## How it works

1. **Dependency.** `spring-ai-starter-model-anthropic` (version from `spring-ai-bom`) auto-configures a `ChatClient.Builder`.
2. **Config.** In `application.properties`, set the API key (`spring.ai.anthropic.api-key`), the model (`spring.ai.anthropic.chat.model=claude-opus-5-5`) and `max-tokens`.
3. **`ChatClient`.** `NoteAssistantService` builds one `ChatClient` with a default system prompt. Each method uses the fluent API: `chatClient.prompt().user(...).call().content()`.
   - `.entity(NoteInsights.class)` asks Claude for JSON that matches the record and converts the reply into the record.
   - `.tools(noteTools)` registers the `@Tool` methods in `NoteTools`. Spring AI runs the tool-calling loop for you.
   - `MessageChatMemoryAdvisor` stores earlier messages and adds them back into each new request.

`NoteStore` keeps notes in memory, so the example needs no database. To use these features in `note-app`, replace `NoteStore` with the `NoteRepository`.

## Notes

- Claude Opus 5.5 does not accept `temperature` or `top-p`, so don't set `spring.ai.anthropic.chat.temperature` with this model.
- Every request costs API credits. For cheaper, faster replies, switch the model to `claude-haiku-4-5` in `application.properties`.
- `mvn test` runs without a real API key.
