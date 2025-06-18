// src/main/java/com/grrenhand/greenhand/login/service/UserService.java
package com.grrenhand.greenhand.login.service;

import com.grrenhand.greenhand.login.domain.User;
import com.grrenhand.greenhand.login.dto.UserDTO;
import com.grrenhand.greenhand.login.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder
    ) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public User registerNewUser(UserDTO userDTO) {
        if (!userDTO.getPassword().equals(userDTO.getConfirmPassword())) {
            throw new IllegalArgumentException("비밀번호와 확인이 일치하지 않습니다.");
        }
        if (userRepository.existsByUsername(userDTO.getUsername())) {
            throw new IllegalArgumentException("이미 존재하는 아이디입니다.");
        }
        if (userDTO.getEmail() != null
                && !userDTO.getEmail().isEmpty()
                && userRepository.existsByEmail(userDTO.getEmail())) {
            throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
        }
        String encoded = passwordEncoder.encode(userDTO.getPassword());
        User user = new User();
        user.setUsername(userDTO.getUsername());
        user.setPasswordHash(encoded);
        user.setNickname(userDTO.getNickname());
        user.setName(userDTO.getName());
        user.setEmail(userDTO.getEmail());
        user.setAddress(userDTO.getAddress());
        user.setPhoneNumber(userDTO.getPhoneNumber());
        return userRepository.save(user);
    }

    @Transactional(readOnly = true)
    public Optional<User> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    @Transactional(readOnly = true)
    public String findUserIdByEmail(String email) {
        return userRepository.findByEmail(email)
                .map(User::getUsername)
                .orElse(null);
    }

    @Transactional(readOnly = true)
    public boolean validateUserEmail(String userId, String email) {
        return userRepository.findByUsername(userId)
                .map(u -> u.getEmail().equals(email))
                .orElse(false);
    }
}
