package com.note.ai;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import com.note.ai.service.NoteStore;

// A dummy key is enough: the context starts without calling the Anthropic API
@SpringBootTest(properties = "spring.ai.anthropic.api-key=test-key")
class SpringAiExampleApplicationTests {

	@Autowired
	NoteStore noteStore;

	@Test
	void contextLoads() {
		assertThat(noteStore.findAll()).hasSize(3);
	}

	@Test
	void searchIsCaseInsensitive() {
		assertThat(noteStore.search("MEETING")).extracting("title").containsExactly("Team meeting 6 Oct");
	}

}
