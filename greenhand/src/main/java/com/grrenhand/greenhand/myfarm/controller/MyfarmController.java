package com.grrenhand.greenhand.myfarm.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/myfarm")
public class MyfarmController {

    @GetMapping
    public String showMyFarmPage() {
        return "myfarm.html";
    }
}