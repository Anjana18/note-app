package com.thulya.service;

import com.thulya.common.ApiException;
import com.thulya.domain.Appointment;
import com.thulya.domain.AppointmentMode;
import com.thulya.domain.CalendarConfig;
import com.thulya.dto.AppointmentDtos.*;
import com.thulya.repository.AppointmentRepository;
import com.thulya.repository.CalendarConfigRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class AppointmentService {

    private final AppointmentRepository appointments;
    private final CalendarConfigRepository calendarConfigs;
    private final NotificationService notifications;

    public AppointmentService(AppointmentRepository appointments,
                              CalendarConfigRepository calendarConfigs,
                              NotificationService notifications) {
        this.appointments = appointments;
        this.calendarConfigs = calendarConfigs;
        this.notifications = notifications;
    }

    private CalendarConfig config() {
        return calendarConfigs.findAll().stream().findFirst().orElseGet(() -> {
            CalendarConfig c = new CalendarConfig();
            for (String d : List.of("mon", "tue", "wed", "thu", "fri", "sat")) {
                c.getWorkingHours().put(d, List.of("10:00", "19:00"));
            }
            return c;
        });
    }

    /** Available slots for a date, respecting working hours, holidays and per-slot caps. */
    public List<SlotView> slots(String date) {
        CalendarConfig cfg = config();
        List<SlotView> out = new ArrayList<>();
        LocalDate day = LocalDate.parse(date);
        String dow = day.getDayOfWeek().getDisplayName(TextStyle.SHORT, Locale.ENGLISH).toLowerCase();

        boolean closed = cfg.getHolidays().contains(date)
                || cfg.getBlockedDates().contains(date)
                || !cfg.getWorkingHours().containsKey(dow);
        if (closed) return out;

        List<String> hours = cfg.getWorkingHours().get(dow);
        LocalTime start = LocalTime.parse(hours.get(0));
        LocalTime end = LocalTime.parse(hours.get(1));

        Map<String, Long> booked = new java.util.HashMap<>();
        for (Appointment a : appointments.findBySlotDate(date)) {
            booked.merge(a.getSlot().getStart(), 1L, Long::sum);
        }

        for (LocalTime t = start; t.plusMinutes(cfg.getSlotMinutes()).compareTo(end) <= 0;
             t = t.plusMinutes(cfg.getSlotMinutes())) {
            String s = t.toString();
            String e = t.plusMinutes(cfg.getSlotMinutes()).toString();
            int used = booked.getOrDefault(s, 0L).intValue();
            int remaining = Math.max(0, cfg.getMaxPerSlot() - used);
            out.add(new SlotView(date, s, e, remaining > 0, remaining));
        }
        return out;
    }

    public AppointmentView create(String userId, CreateAppointmentRequest req) {
        CalendarConfig cfg = config();
        long booked = appointments.findBySlotDate(req.date()).stream()
                .filter(a -> a.getSlot().getStart().equals(req.start())).count();
        if (booked >= cfg.getMaxPerSlot()) throw ApiException.conflict("SLOT_UNAVAILABLE");

        Appointment a = new Appointment();
        a.setUserId(userId);
        try {
            a.setMode(AppointmentMode.valueOf(req.mode().toUpperCase()));
        } catch (IllegalArgumentException e) {
            throw ApiException.badRequest("INVALID_MODE");
        }
        a.setDressType(req.dressType());
        a.setService(req.service());
        a.getSlot().setDate(req.date());
        a.getSlot().setStart(req.start());
        a.getSlot().setEnd(req.end());
        a.setAddressId(req.addressId());
        a.setNotes(req.notes());
        a.getRemindersSent().add("confirmation");
        Appointment saved = appointments.save(a);

        notifications.send(userId, "whatsapp", "booking_confirmation",
                "Measurement booked for " + req.date() + " at " + req.start() + ".");
        return view(saved);
    }

    public List<AppointmentView> myAppointments(String userId) {
        return appointments.findByUserIdOrderByCreatedAtDesc(userId).stream().map(this::view).toList();
    }

    private AppointmentView view(Appointment a) {
        return new AppointmentView(a.getId(), a.getMode().name(), a.getDressType(), a.getService(),
                a.getSlot().getDate(), a.getSlot().getStart(), a.getSlot().getEnd(),
                a.getStatus().name(), a.getCreatedAt());
    }
}
