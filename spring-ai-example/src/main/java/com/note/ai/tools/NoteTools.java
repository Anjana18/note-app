package com.note.ai.tools;

import java.util.List;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

import com.note.ai.model.Note;
import com.note.ai.service.NoteStore;

/**
 * Methods Claude may call while answering ("tool calling" / "function calling").
 * Spring AI sends the descriptions to the model, runs the method the model picks,
 * and sends the result back - you never write the request/response loop yourself.
 */
@Component
public class NoteTools {

	private final NoteStore noteStore;

	public NoteTools(NoteStore noteStore) {
		this.noteStore = noteStore;
	}

	@Tool(description = "List every note the user has saved")
	public List<Note> listNotes() {
		return noteStore.findAll();
	}

	@Tool(description = "Find the user's notes whose title or content contains a keyword")
	public List<Note> searchNotes(@ToolParam(description = "A single keyword, e.g. 'meeting'") String keyword) {
		return noteStore.search(keyword);
	}

	@Tool(description = "Save a new note for the user")
	public Note createNote(@ToolParam(description = "Short title of the note") String title,
			@ToolParam(description = "Full text of the note") String content) {
		return noteStore.save(title, content);
	}

}
