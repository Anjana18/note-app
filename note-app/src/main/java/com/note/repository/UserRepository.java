package com.note.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import com.note.bean.User;

@Repository
public interface UserRepository extends JpaRepository<User, Long>{
	@Query(value="SELECT u FROM User u where u.email=?1 or u.userName=?1 ")
	User findUserByUserName(String userNameOrEmail);
}
