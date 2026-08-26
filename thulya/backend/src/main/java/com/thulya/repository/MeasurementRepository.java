package com.thulya.repository;

import com.thulya.domain.Measurement;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface MeasurementRepository extends MongoRepository<Measurement, String> {
    List<Measurement> findByUserIdAndActiveTrue(String userId);
}
