package com.note.bean;

import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.Lob;
import javax.persistence.ManyToOne;
import javax.persistence.Table;

@Entity
@Table(name="Note")
public class Note {
	
	@Id
	@GeneratedValue(strategy=GenerationType.AUTO)
	@Column(name="note_id")
	private Long noteId;
	
	@Column(name="note_title")
	private String noteTitle;
	
	@Lob
	@Column(name="note_discription")
	private String noteDiscription;
	
	@Column(name="created_date")
	private Date createdDate= new Date();
	
	@Column(name="updated_date")
	private Date updatedDate= new Date();
	
	@ManyToOne
	@JoinColumn(name="user_id")
	private User user;

	public Note(String title1, String discription, User user) {
		this.noteTitle=title1;
		this.noteDiscription=discription;
		this.user=user;
	}
	public Note() {
		
	}

	public Long getNoteId() {
		return noteId;
	}

	public void setNoteId(Long noteId) {
		this.noteId = noteId;
	}

	public String getNoteTitle() {
		return noteTitle;
	}

	public void setNoteTitle(String noteTitle) {
		this.noteTitle = noteTitle;
	}

	public String getNoteDiscription() {
		return noteDiscription;
	}

	public void setNoteDiscription(String noteDiscription) {
		this.noteDiscription = noteDiscription;
	}

	public User getUser() {
		return user;
	}

	public void setUser(User user) {
		this.user = user;
	}

	public Date getCreatedDate() {
		return createdDate;
	}

	public Date getUpdatedDate() {
		return updatedDate;
	}
	
	public void setUpdatedDate(Date updatedDate) {
		this.updatedDate = updatedDate;
	}
	
	public String toString() {
		return "{ Note ID:"+getNoteId()+", Title:"+getNoteTitle()+", Discription:"+getNoteDiscription()+", Created Date:"+getCreatedDate()+", Updated Date:"+getUpdatedDate()+", User:"+getUser()+"}";
		
	}
	
	
}
