package com.note.ai.service;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.stereotype.Service;

import com.note.ai.model.NoteInsights;
import com.note.ai.tools.NoteTools;

/**
 * Shows the four most common Spring AI patterns:
 * 1. a plain prompt -> text answer
 * 2. structured output mapped into a Java record
 * 3. tool calling, where Claude reads and writes the user's notes
 * 4. a multi-turn chat that remembers earlier messages
 */
@Service
public class NoteAssistantService {

	private final ChatClient chatClient;

	private final NoteTools noteTools;

	private final ChatMemory chatMemory = MessageWindowChatMemory.builder().maxMessages(20).build();

	public NoteAssistantService(ChatClient.Builder chatClientBuilder, NoteTools noteTools) {
		this.chatClient = chatClientBuilder
			.defaultSystem("You are a helpful assistant inside a note-taking app. Keep answers short and clear.")
			.build();
		this.noteTools = noteTools;
	}

	// 1. Plain text
	public String summarize(String title, String content) {
		return chatClient.prompt()
			.user(u -> u.text("Summarize this note in at most two sentences.\nTitle: {title}\nNote: {content}")
				.param("title", title)
				.param("content", content))
			.call()
			.content();
	}

	// 2. Structured output
	public NoteInsights analyze(String title, String content) {
		return chatClient.prompt()
			.user(u -> u.text("""
					Analyze this note. Suggest a better title, write a one-sentence summary,
					give up to 5 lowercase tags, and list any action items (empty list if none).
					Title: {title}
					Note: {content}
					""")
				.param("title", title)
				.param("content", content))
			.call()
			.entity(NoteInsights.class);
	}

	// 3. Tool calling
	public String ask(String question) {
		return chatClient.prompt()
			.system("Use the note tools to look up or save the user's notes. Never invent notes.")
			.user(question)
			.tools(noteTools)
			.call()
			.content();
	}

	// 4. Chat with memory (each conversationId keeps its own history)
	public String chat(String conversationId, String message) {
		return chatClient.prompt()
			.advisors(MessageChatMemoryAdvisor.builder(chatMemory).build())
			.advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
			.user(message)
			.call()
			.content();
	}

}
