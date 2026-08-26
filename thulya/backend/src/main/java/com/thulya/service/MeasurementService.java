package com.thulya.service;

import com.thulya.domain.Measurement;
import com.thulya.dto.MeasurementDtos.CreateMeasurementRequest;
import com.thulya.dto.MeasurementDtos.MeasurementView;
import com.thulya.repository.MeasurementRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class MeasurementService {

    private final MeasurementRepository repo;

    public MeasurementService(MeasurementRepository repo) {
        this.repo = repo;
    }

    public List<MeasurementView> list(String userId) {
        return repo.findByUserIdAndActiveTrue(userId).stream().map(this::view).toList();
    }

    public MeasurementView create(String userId, CreateMeasurementRequest req) {
        Measurement m = new Measurement();
        m.setUserId(userId);
        m.setDressType(req.dressType());
        if (req.values() != null) m.setValues(req.values());
        m.setTakenBy(req.takenBy() != null ? req.takenBy() : "self");
        return view(repo.save(m));
    }

    private MeasurementView view(Measurement m) {
        return new MeasurementView(m.getId(), m.getDressType(), m.getValues(),
                m.getTakenBy(), m.getTakenAt());
    }
}
