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

    // 전화번호 하이픈 제거 유틸리티 메서드
    private String normalizePhoneNumber(String phoneNumber) {
        if (phoneNumber == null) return null;
        return phoneNumber.replaceAll("-", "").trim();
    }

    @Transactional
    public User registerNewUser(UserDTO userDTO) {
        // 1. 비밀번호 확인 필드 일치 여부 검사
        if (!userDTO.getPassword().equals(userDTO.getConfirmPassword())) {
            throw new IllegalArgumentException("비밀번호와 확인이 일치하지 않습니다.");
        }
        // 2. 아이디 중복 검사
        if (userRepository.existsByUsername(userDTO.getUsername())) {
            throw new IllegalArgumentException("이미 존재하는 아이디입니다.");
        }
        // 3. 이메일 중복 검사 (이메일이 입력되었고 비어있지 않을 경우에만 검사)
        if (userDTO.getEmail() != null
                && !userDTO.getEmail().isEmpty()
                && userRepository.existsByEmail(userDTO.getEmail())) {
            throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
        }
        // 4. 닉네임 중복 검사 (닉네임이 입력되었고 비어있지 않을 경우에만 검사)
        if (userDTO.getNickname() != null
                && !userDTO.getNickname().isEmpty()
                && userRepository.existsByNickname(userDTO.getNickname())) {
            throw new IllegalArgumentException("이미 사용 중인 닉네임입니다.");
        }

        // 5. 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(userDTO.getPassword());

        // 6. User 엔티티 생성 및 데이터 설정
        User user = new User();
        user.setUsername(userDTO.getUsername());
        user.setPasswordHash(encodedPassword); // 암호화된 비밀번호 저장
        user.setNickname(userDTO.getNickname());
        user.setName(userDTO.getName());
        user.setEmail(userDTO.getEmail());
        user.setAddress(userDTO.getAddress());
        user.setPhoneNumber(normalizePhoneNumber(userDTO.getPhoneNumber())); // 정규화된 전화번호 저장
        return userRepository.save(user);
    }

    @Transactional(readOnly = true)
    public Optional<User> findByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    // =========================================================================
    // 아이디/비밀번호 찾기 관련 로직 추가
    // =========================================================================

    // 이메일과 전화번호로 사용자 아이디 찾기
    @Transactional(readOnly = true)
    public String findUserIdByEmailAndPhoneNumber(String email, String phoneNumber) {
        String normalizedPhoneNumber = normalizePhoneNumber(phoneNumber);
        return userRepository.findByEmailAndPhoneNumber(email, normalizedPhoneNumber)
                .map(User::getUsername)
                .orElse(null); // 없으면 null 반환
    }

    // 사용자 아이디와 전화번호가 일치하는지 확인 (비밀번호 재설정 전 확인용)
    @Transactional(readOnly = true)
    public boolean validateUserCredentials(String username, String phoneNumber) {
        String normalizedPhoneNumber = normalizePhoneNumber(phoneNumber);
        return userRepository.findByUsernameAndPhoneNumber(username, normalizedPhoneNumber)
                .isPresent(); // 사용자가 존재하면 true
    }
}