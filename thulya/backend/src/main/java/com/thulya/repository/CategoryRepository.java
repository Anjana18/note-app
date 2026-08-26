package com.thulya.repository;

import com.thulya.domain.Category;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface CategoryRepository extends MongoRepository<Category, String> {
    List<Category> findByActiveTrueOrderByOrderAsc();
    Optional<Category> findBySlug(String slug);
}
