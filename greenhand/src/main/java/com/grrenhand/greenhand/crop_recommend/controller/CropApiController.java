package com.grrenhand.greenhand.crop_recommend.controller;

import com.grrenhand.greenhand.crop_recommend.domain.Crop;
import com.grrenhand.greenhand.crop_recommend.service.CropService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/crop")
public class CropApiController {

    private final CropService cropService;

    public CropApiController(CropService cropService) {
        this.cropService = cropService;
    }

    @PostMapping("/add")
    public ResponseEntity<Crop> addCrop(@RequestBody Crop crop) {
        Crop savedCrop = cropService.save(crop);
        return ResponseEntity.ok(savedCrop);
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Crop>> getUserCrops(@PathVariable String userId) {
        List<Crop> crops = cropService.findByUserId(userId);
        return ResponseEntity.ok(crops);
    }

    @DeleteMapping("/user/{userId}/{cropName}")
    public ResponseEntity<Void> deleteUserCrop(@PathVariable String userId, @PathVariable String cropName) {
        boolean deleted = cropService.deleteByUserIdAndCropName(userId, cropName);
        return deleted ? ResponseEntity.ok().build() : ResponseEntity.notFound().build();
    }
}
