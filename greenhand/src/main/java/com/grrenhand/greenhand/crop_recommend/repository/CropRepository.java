package com.grrenhand.greenhand.crop_recommend.repository;

import com.grrenhand.greenhand.crop_recommend.domain.Crop;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CropRepository extends JpaRepository<Crop, Long> {
    List<Crop> findByUserId(String userId);
    boolean existsByUserIdAndName(String userId, String name);
    void deleteByUserIdAndName(String userId, String name);
}
