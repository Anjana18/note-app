package com.thulya.repository;

import com.thulya.domain.CalendarConfig;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface CalendarConfigRepository extends MongoRepository<CalendarConfig, String> {
}
