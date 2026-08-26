package com.thulya.repository;

import com.thulya.domain.Order;
import com.thulya.domain.OrderStage;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface OrderRepository extends MongoRepository<Order, String> {
    Optional<Order> findByOrderNo(String orderNo);
    List<Order> findByUserIdOrderByCreatedAtDesc(String userId);
    List<Order> findByStage(OrderStage stage);
    List<Order> findByAssignedTailorId(String tailorId);
    long countByStage(OrderStage stage);
}
