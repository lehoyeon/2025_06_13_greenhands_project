//// src/main/java/com/grrenhand/greenhand/login/config/JwtConstants.java
//
//package com.grrenhand.greenhand.login.config;
//
//public class JwtConstants {
//    // 경고: 이 키는 실제 배포 환경에서는 환경 변수나 안전한 외부 설정으로 관리해야 합니다!
//    // 아래 문자열은 Base64로 인코딩된 64바이트(512비트) 길이의 무작위 키 예시입니다.
//    // 직접 생성할 때는 https://www.javainuse.com/online/jwtSecretKey 같은 도구 사용 가능
//    // 또는 `Keys.secretKeyFor(SignatureAlgorithm.HS512).getEncoded()` 후 Base64 인코딩
//    public static final String JWT_SECRET = "YzQzZDAwMjAzZDg4YzM0YzUzZDZlNDVmNjEzZjc1NTczMzRiNThjMjgwM2IwMjQ1ZDNlOTZmMzY1MzY4NDU5MA=="; // <--- 이 부분을 복사해서 붙여넣으세요!
//
//    // 토큰 만료 시간 (예: 24시간) - 밀리초 단위
//    public static final long JWT_EXPIRATION_MS = 24 * 60 * 60 * 1000L; // 24 hours
//
//    public static final String JWT_HEADER_STRING = "Authorization";
//    public static final String JWT_TOKEN_PREFIX = "Bearer "; // 토큰 타입 접두사
//}