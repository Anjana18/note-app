package com.thulya.service;

import com.thulya.common.Money;
import com.thulya.domain.Order;
import com.thulya.domain.OrderStage;
import com.thulya.domain.Role;
import com.thulya.dto.AdminDtos.*;
import com.thulya.repository.AppointmentRepository;
import com.thulya.repository.OrderRepository;
import com.thulya.repository.ProductRepository;
import com.thulya.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;

@Service
public class AdminAnalyticsService {

    private final OrderRepository orders;
    private final ProductRepository products;
    private final UserRepository users;
    private final AppointmentRepository appointments;

    public AdminAnalyticsService(OrderRepository orders, ProductRepository products,
                                 UserRepository users, AppointmentRepository appointments) {
        this.orders = orders;
        this.products = products;
        this.users = users;
        this.appointments = appointments;
    }

    public AnalyticsView analytics() {
        LocalDate today = LocalDate.now();
        ZoneId zone = ZoneId.systemDefault();

        List<Order> all = orders.findAll();
        List<Order> todays = all.stream()
                .filter(o -> o.getCreatedAt() != null
                        && o.getCreatedAt().atZone(zone).toLocalDate().isEqual(today))
                .toList();

        long revenueToday = todays.stream().mapToLong(o -> o.getPricing().getTotal()).sum();
        long bookingsToday = appointments.findBySlotDate(today.toString()).size();

        long pendingStitching = all.stream()
                .filter(o -> o.getStage().index() >= OrderStage.CUTTING.index()
                        && o.getStage().index() < OrderStage.READY.index())
                .count();
        long completed = orders.countByStage(OrderStage.DELIVERED);
        long customers = users.countByRole(Role.CUSTOMER);

        List<PopularProductView> popular = products.findByActiveTrue(
                        org.springframework.data.domain.PageRequest.of(0, 5,
                                org.springframework.data.domain.Sort.by(
                                        org.springframework.data.domain.Sort.Direction.DESC, "ratingCount")))
                .stream()
                .map(p -> new PopularProductView(Mappers.card(p), p.getRatingCount()))
                .toList();

        List<LowStockView> lowStock = products.findByStockLessThanEqual(7).stream()
                .map(p -> new LowStockView(p.getId(), p.getSku(), p.getName(), p.getStock()))
                .toList();

        return new AnalyticsView(
                todays.size(), Money.paiseToRupees(revenueToday), bookingsToday,
                pendingStitching, completed, customers, popular, lowStock);
    }
}
