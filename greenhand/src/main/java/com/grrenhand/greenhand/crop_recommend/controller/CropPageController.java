package com.grrenhand.greenhand.crop_recommend.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/crop")
public class CropPageController {

    @GetMapping
    public String showCropPage() {
        return "crop.html"; // ✅ 확장자 제거
    }

    @GetMapping("/guide")
    public String showGuidePage() {
        return "guide";
    }

}
