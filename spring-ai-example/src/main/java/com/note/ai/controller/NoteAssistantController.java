package com.note.ai.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.note.ai.model.ChatRequest;
import com.note.ai.model.NoteInsights;
import com.note.ai.model.NoteRequest;
import com.note.ai.service.NoteAssistantService;

@RestController
@RequestMapping("/api/ai")
public class NoteAssistantController {

	private final NoteAssistantService assistant;

	public NoteAssistantController(NoteAssistantService assistant) {
		this.assistant = assistant;
	}

	@PostMapping("/summarize")
	public Map<String, String> summarize(@RequestBody NoteRequest note) {
		return Map.of("summary", assistant.summarize(note.title(), note.content()));
	}

	@PostMapping("/analyze")
	public NoteInsights analyze(@RequestBody NoteRequest note) {
		return assistant.analyze(note.title(), note.content());
	}

	@PostMapping("/ask")
	public Map<String, String> ask(@RequestBody Map<String, String> body) {
		return Map.of("answer", assistant.ask(body.get("question")));
	}

	@PostMapping("/chat")
	public Map<String, String> chat(@RequestBody ChatRequest request) {
		return Map.of("reply", assistant.chat(request.conversationId(), request.message()));
	}

}
