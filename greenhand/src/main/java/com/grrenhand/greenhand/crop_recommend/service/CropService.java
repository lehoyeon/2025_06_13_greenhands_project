package com.grrenhand.greenhand.crop_recommend.service;

import com.grrenhand.greenhand.crop_recommend.domain.Crop;
import com.grrenhand.greenhand.crop_recommend.repository.CropRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CropService {

    private final CropRepository cropRepository;

    public CropService(CropRepository cropRepository) {
        this.cropRepository = cropRepository;
    }

    public Crop save(Crop crop) {
        return cropRepository.save(crop);
    }

    public List<Crop> findByUserId(String userId) {
        return cropRepository.findByUserId(userId);
    }

    public boolean deleteByUserIdAndCropName(String userId, String name) {
        if (cropRepository.existsByUserIdAndName(userId, name)) {
            cropRepository.deleteByUserIdAndName(userId, name);
            return true;
        }
        return false;
    }
}
