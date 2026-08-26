package com.thulya.service;

import com.thulya.common.ApiException;
import com.thulya.common.Money;
import com.thulya.domain.TailoringService;
import com.thulya.dto.TailoringDtos.GroupView;
import com.thulya.dto.TailoringDtos.ItemView;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

/** Reads the tailoring price catalogue and applies Admin edits. */
@Service
public class TailoringPricingService {

    private final com.thulya.repository.TailoringServiceRepository repo;

    public TailoringPricingService(com.thulya.repository.TailoringServiceRepository repo) {
        this.repo = repo;
    }

    public List<GroupView> groups() {
        return repo.findByActiveTrue().stream()
                .map(g -> new GroupView(g.getId(), g.getGroup(), g.getIcon(),
                        g.getItems().stream()
                                .map(i -> new ItemView(i.getCode(), i.getName(),
                                        Money.paiseToRupees(i.getPrice()), i.isFromPrice()))
                                .toList()))
                .toList();
    }

    /** Admin updates the price (rupees) of a single service item by its code. */
    public ItemView updatePrice(String itemCode, long rupees) {
        for (TailoringService group : repo.findByActiveTrue()) {
            for (TailoringService.Item item : group.getItems()) {
                if (item.getCode().equals(itemCode)) {
                    item.setPrice(Money.rupeesToPaise(rupees));
                    group.setUpdatedAt(Instant.now());
                    repo.save(group);
                    return new ItemView(item.getCode(), item.getName(),
                            Money.paiseToRupees(item.getPrice()), item.isFromPrice());
                }
            }
        }
        throw ApiException.notFound("TAILORING_ITEM_NOT_FOUND");
    }
}
