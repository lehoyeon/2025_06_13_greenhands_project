// src/main/java/com/grrenhand/greenhand/login/controller/FindAccountController.java
package com.grrenhand.greenhand.login.controller;

import com.grrenhand.greenhand.login.service.UserService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/user")
public class FindAccountController {

    private final UserService userService;

    public FindAccountController(UserService userService) {
        this.userService = userService;
    }

}
