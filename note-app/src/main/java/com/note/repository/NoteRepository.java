package com.note.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.note.bean.Note;
import com.note.bean.User;

@Repository
public interface NoteRepository extends JpaRepository<Note, Long>{

	Note findByNoteId(Long noteId);
	List<Note> findAllByUser(User user);
}

