package com.thulya.repository;

import com.thulya.domain.Coupon;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface CouponRepository extends MongoRepository<Coupon, String> {
    Optional<Coupon> findByCodeAndActiveTrue(String code);
}
