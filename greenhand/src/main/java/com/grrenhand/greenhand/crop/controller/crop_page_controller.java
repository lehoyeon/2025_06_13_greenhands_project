package com.grrenhand.greenhand.crop.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class crop_page_controller {

    @GetMapping("/crop-plus")
    public String cropPlusPage() {
        return "crop_plus.html"; // templates/crop_plus.html 사용 시 확장자 생략
    }
}