package com.note.bean;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "User")
public class User {

	@Id
	@GeneratedValue(strategy = GenerationType.AUTO)
	@Column(name = "user_id")
	private Long userId;

	@Column(name = "user_name", unique = true)
	private String userName;

	@Column(name = "email", unique = true)
	private String email;

	@Column(name = "user_password")
	private String userPassword;

	public User(String userName, String emailId, String password) {
		this.userName = userName;
		this.email = emailId;
		this.userPassword = password;
	}
	public User() {
		
	}

	public Long getUserId() {
		return userId;
	}

	public void setUserId(Long userId) {
		this.userId = userId;
	}

	public String getUserName() {
		return userName;
	}

	public void setUserName(String userName) {
		this.userName = userName;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public String getUserPassword() {
		return userPassword;
	}

	public void setUserPassword(String userPassword) {
		this.userPassword = userPassword;
	}

	public String toString() {
		return "{ User ID :" + getUserId() + ", User Name:" + getUserName() + ", email:" + getEmail() + "}";
	}

}
