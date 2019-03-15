package com.note.service;

import java.util.List;

import org.springframework.stereotype.Service;

import com.note.bean.Note;
import com.note.bean.User;

@Service
public interface NoteService {
	List<Note> listOfNotes(User user);
	Note findNodeById(Long noteId);
}
