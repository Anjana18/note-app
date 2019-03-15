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
	@RequestMapping(value="/dashboard")
	public String dashboard() {
		return AppConstants.PAGE_DASHBORD;
	}
	
	@RequestMapping(value="/newnotes")
	public String addnote() {
		return "newnotes";
	}

	@RequestMapping(value = "/"+AppConstants.PAGE_LOGIN, method = RequestMethod.POST)
	public ModelAndView login(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(name = AppConstants.PARAM_USER_NAME, required = false) String requestUserName,
			@RequestParam(name = AppConstants.PARAM_USER_PASSWORD,required = false)String requestPassword,
			@RequestParam(name = AppConstants.PARAM_ERROR, required = false) String error, ModelMap modelMap) {
		ModelAndView modelAndView= new ModelAndView();
		if(userRepo.findUserByUserName(requestUserName)!=null) {
			User user=userRepo.findUserByUserName(requestUserName);
			System.out.println("user:"+user.getUserPassword());
			System.out.println("user1"+requestPassword);
			if(user.getUserPassword().equals(requestPassword)) {
				List<Note> getNoteList=noteRepo.findAllByUser(user);
				System.err.println(getNoteList.size());
				if(!getNoteList.isEmpty() && getNoteList!=null && getNoteList.size()>=1) {
					modelAndView.setViewName(AppConstants.PAGE_DASHBORD);
					modelAndView.addObject(AppConstants.NOTE_LIST, getNoteList);
				}
				else {
					modelAndView.setViewName("note");
				}
			}else {
				getRedirect(request, response, "User Name (or) Password is Incorrect...", "/login.html");
			}
		}else{
			new ModelAndView("redirect:/");
		}
		return modelAndView;
		
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
				if (userRepo.findUserByUserName(emailId)==null) {
					isUserCreated = true;
					userRepo.save(user);
				}
				else {
					getRedirect(request, response, "Sorry User Name or Email already exist!", "/login");
				}
			} 
		} 
		return AppConstants.PAGE_LOGIN;
	}
	
	@RequestMapping(value=AppConstants.URL_LOGOUT)
	public String loginOutPage(HttpServletRequest request,HttpServletResponse response){
		
		Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
		if(authentication!=null){
			SecurityContextHolder.getContext().setAuthentication(null);
		}
		return "redirect:"+AppConstants.PAGE_ROOT;
	}
	
	@RequestMapping(value = "/"+AppConstants.NEW_NOTE, method = RequestMethod.POST)
	public String note(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(value=AppConstants.USER_DETAILS,required=false) User user,
			@RequestParam(value = AppConstants.PARAM_NOTE_TITLE, required = false) String title,
			@RequestParam(value = AppConstants.PARAM_NOTE_DISCRIPTION, required = false) String discription,
			ModelMap modelMap) {

		Note note = new Note(title, discription,user);
		if(note!=null) {
			noteRepo.save(note);
		}
		return "note";
	}
	
	@RequestMapping(value = AppConstants.NOTE_LIST, method = RequestMethod.GET)
	public ModelAndView getMyNotes(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(value=AppConstants.USER_DETAILS,required=false) User user,
			ModelMap modelMap) {
		ModelAndView modelAndView=new ModelAndView();
		modelAndView.setViewName(AppConstants.LIST_VIEW_OF_NOTES);
		List<Note> getNoteList=noteRepo.findAllByUser(user);
		modelAndView.addObject(AppConstants.NOTE_LIST, getNoteList);
		
		return modelAndView;
	}
	
	@RequestMapping(value = AppConstants.UPDATE_NOTE, method = RequestMethod.GET)
	public String updateNote(HttpServletRequest request, HttpServletResponse response,
			@RequestParam(value=AppConstants.USER_DETAILS,required=false) User user,
			@RequestParam(value=AppConstants.NOTE_DETAILS,required=false) Note note,
			@RequestParam(value = AppConstants.PARAM_NOTE_TITLE, required = false) String title,
			@RequestParam(value = AppConstants.PARAM_NOTE_DISCRIPTION, required = false) String discription,
			ModelMap modelMap) {

		if(note!=null) {
			note.setNoteDiscription(discription);
			note.setNoteTitle(title);
			note.setUpdatedDate(new Date());
			noteRepo.save(note);
			modelMap.put(AppConstants.NOTE_SAVED,AppConstants.MESSAGE_NOTE_SAVED);
		}
		return AppConstants.PAGE_DASHBORD;
	}
	
	public void getRedirect(HttpServletRequest request,HttpServletResponse response,String msg,String redirectPage) {
		response.setContentType("text/html");  
		PrintWriter out = null;
        RequestDispatcher rd=request.getRequestDispatcher(redirectPage);  
        try {
        	out = response.getWriter();
        	out.print(msg);  
			rd.include(request, response);
			
		} catch (ServletException | IOException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
	}
	
	
}
