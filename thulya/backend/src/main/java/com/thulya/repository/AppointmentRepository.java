package com.thulya.repository;

import com.thulya.domain.Appointment;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;

public interface AppointmentRepository extends MongoRepository<Appointment, String> {
    List<Appointment> findByUserIdOrderByCreatedAtDesc(String userId);
    List<Appointment> findBySlotDate(String date);
}
