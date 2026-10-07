package com.note.ai.model;

import java.util.List;

/**
 * Structured result returned by Claude. Spring AI turns this record into a JSON schema,
 * asks the model to answer in that shape, and maps the reply back into the record.
 */
public record NoteInsights(String suggestedTitle, String summary, List<String> tags, List<String> actionItems) {
}
