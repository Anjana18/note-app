package com.note.ai.service;

import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

import org.springframework.stereotype.Component;

import com.note.ai.model.Note;

/**
 * Simple in-memory note store with a few sample notes, so the example runs without a database.
 * In the real note-app this would be the NoteRepository backed by MySQL.
 */
@Component
public class NoteStore {

	private final Map<Long, Note> notes = new ConcurrentHashMap<>();

	private final AtomicLong ids = new AtomicLong();

	public NoteStore() {
		save("Grocery list", "Milk, eggs, spinach, rice. Buy birthday cake for Friday.");
		save("Team meeting 6 Oct", "Discussed release date. Ravi to fix the login bug by Wednesday. "
				+ "Priya will prepare the demo for the customer on Thursday.");
		save("Spring AI ideas", "Summarize notes, suggest tags, let users ask questions about their notes.");
	}

	public Note save(String title, String content) {
		Note note = new Note(ids.incrementAndGet(), title, content);
		notes.put(note.id(), note);
		return note;
	}

	public List<Note> findAll() {
		return notes.values().stream().sorted((a, b) -> a.id().compareTo(b.id())).toList();
	}

	public List<Note> search(String keyword) {
		String k = keyword.toLowerCase(Locale.ROOT);
		return findAll().stream()
			.filter(n -> n.title().toLowerCase(Locale.ROOT).contains(k)
					|| n.content().toLowerCase(Locale.ROOT).contains(k))
			.toList();
	}

}
