package com.note.service;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.note.bean.Note;
import com.note.bean.User;
import com.note.repository.NoteRepository;
@Service
public class NoteServiceImpl implements NoteService{
	
	@Autowired
	private NoteRepository noteRepo;
	@Override
	public List<Note> listOfNotes(User user) {
		
		return noteRepo.findAllByUser(user);
	}

	@Override
	public Note findNodeById(Long noteId) {
		return noteRepo.findByNoteId(noteId);
	}

}
