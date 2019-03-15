package com.note.service;

import org.springframework.stereotype.Service;

import com.note.bean.User;

@Service
public interface UserService {
	
	public User findUser(String userNameOrEmail);
}
