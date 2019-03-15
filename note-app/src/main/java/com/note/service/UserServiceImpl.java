package com.note.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.note.bean.User;
import com.note.repository.UserRepository;
@Service
public class UserServiceImpl implements UserService {
	
	@Autowired
	private UserRepository userRepo;
	@Override
	public User findUser(String userNameOrEmail) {
		return userRepo.findUserByUserName(userNameOrEmail);
	}

}
