package com.thulya.repository;

import com.thulya.domain.TailoringService;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface TailoringServiceRepository extends MongoRepository<TailoringService, String> {
    List<TailoringService> findByActiveTrue();
}
