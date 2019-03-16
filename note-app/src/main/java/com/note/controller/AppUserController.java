package com.note.controller;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Date;
import java.util.List;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.MessageSource;
import org.springframework.ui.ModelMap;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.ModelAndView;
import org.springframework.web.servlet.resource.HttpResource;
import org.thymeleaf.expression.Messages;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Controller;

import com.note.bean.Note;
import com.note.bean.User;
import com.note.repository.NoteRepository;
import com.note.repository.UserRepository;
import com.note.service.NoteService;
import com.note.service.UserService;
import com.note.util.AppConstants;

@Controller
public class AppUserController {
	@Autowired
	MessageSource messageSource;

	@Autowired
	NoteService noteService;

	@Autowired
	UserService userService;

	@Autowired
	UserRepository userRepo;
	
	@Autowired
	NoteRepository noteRepo;
	
	@RequestMapping(value=AppConstants.PAGE_ROOT)
	public String index() {
		return AppConstants.PAGE_LOGIN;
	}
	
	@RequestMapping(value = "/dashboard")
	public ModelAndView dashboard(HttpServletRequest request,HttpServletResponse response) {
		ModelAndView view=new ModelAndView();
		List getNoteList=(List) request.getSession().getAttribute("notes");
		String username= (String) request.getSession().getAttribute("username");
		view.addObject(AppConstants.NOTE_LIST, getNoteList);
		view.addObject("username",username);
		view.setViewName("note");
		request.getSession().invalidate();
		return view;
	}
	
	@RequestMapping(value = "/"+AppConstants.SIGN_UP, method = RequestMethod.POST)
	public String signup(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(value = AppConstants.PARAM_USER_NAME, required = false) String userName,
			@RequestParam(value = AppConstants.PARAM_USER_EMAIL, required = false) String emailId,
			@RequestParam(value = AppConstants.PARAM_USER_PASSWORD, required = false) String password,
			ModelMap modelMap) {
		User user = new User(userName, emailId, password);
		if (modelMap.isEmpty()) {
			if (user != null) {
				boolean isUserCreated = false;
				if (userRepo.findUserByUserName(emailId)==null &userRepo.findUserByUserName(userName)==null) {
					isUserCreated = true;
					userRepo.save(user);
				}
				else {
					modelMap.addAttribute("signup_err", "Username/ Mail already exist please try with a different user name/mail id");
				}
			} 
		} 
		return AppConstants.PAGE_LOGIN;
	}
	
	

	@RequestMapping(value = "/"+AppConstants.PAGE_LOGIN, method = RequestMethod.POST)
	public ModelAndView login(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(name = AppConstants.PARAM_USER_NAME, required = false) String requestUserName,
			@RequestParam(name = AppConstants.PARAM_USER_PASSWORD,required = false)String requestPassword,
			@RequestParam(name = AppConstants.PARAM_ERROR, required = false) String error, ModelMap modelMap) {
		ModelAndView modelAndView= new ModelAndView();
		if(userRepo.findUserByUserName(requestUserName)!=null) {
			User user=userRepo.findUserByUserName(requestUserName);
			if(user.getUserPassword().equals(requestPassword)) {
				modelMap.addAttribute("username", user.getUserName());
				List<Note> getNoteList=noteRepo.findAllByUser(user);
					modelAndView.setViewName("note");
					modelAndView.addObject(AppConstants.NOTE_LIST, getNoteList);
			}else {
				modelMap.addAttribute("login_err", "Username/ Password is incorrect please try again.....");
			}
		}else{
			new ModelAndView("redirect:/");
		}
		return modelAndView;
		
	}

	
	@RequestMapping(value = "/"+AppConstants.NEW_NOTE, method=RequestMethod.POST)
	public String note(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(value=AppConstants.USER_DETAILS,required=false) String username,
			@RequestParam(value = "notes_title", required = false) String title,
			@RequestParam(value = AppConstants.PARAM_NOTE_TITLE, required = false) String no_title,
			@RequestParam(value = "notes_description", required = false) String no_discription,
			@RequestParam(value="noteid",required = false) Long noteid,
			@RequestParam(value="notes_username",required = false) String no_username,
			@RequestParam(value = AppConstants.PARAM_NOTE_DISCRIPTION, required = false) String discription,
			ModelMap modelMap) {
		Note note=noteRepo.findByNoteId(noteid);
		if(note!=null) {
			note.setUpdatedDate(new Date());
		}
		else {
			note = new Note();
		}
		note.setNoteTitle(title);
		note.setNoteDiscription(discription);
		String user_name=username;
		if(no_username!=null) {
			user_name=no_username;
		}
		User user=userRepo.findUserByUserName(user_name);
		note.setUser(user);
		if(no_title!=null)
			note.setNoteTitle(no_title);
		if(no_discription!=null)
			note.setNoteDiscription(no_discription);
		noteRepo.save(note);
		List getNoteList=noteRepo.findAllByUser(user);
		request.getSession().setAttribute("notes", getNoteList);
		request.getSession().setAttribute("username", user.getUserName());
		return "redirect:/dashboard";
	}
	
	@RequestMapping(value = "/delete", method=RequestMethod.POST)
	public String delete(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(value=AppConstants.USER_DETAILS,required=false) String username,
			@RequestParam(value="noteid",required = false) Long noteid,
			ModelMap modelMap) {
		Note note=noteRepo.findByNoteId(noteid);
		if(note!=null) {
			noteRepo.deleteById(noteid);
		}
		User user=userRepo.findUserByUserName(username);
		List getNoteList=noteRepo.findAllByUser(user);
		request.getSession().setAttribute("notes", getNoteList);
		request.getSession().setAttribute("username", user.getUserName());
		return "redirect:/dashboard";
	}
	
}
