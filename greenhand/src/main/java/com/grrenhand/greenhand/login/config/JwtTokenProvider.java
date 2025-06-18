//package com.grrenhand.greenhand.login.config;
//
//import io.jsonwebtoken.*; // Jwts, Claims, JwtException 등 포함
//import io.jsonwebtoken.io.Decoders; // Base64 디코딩
//import io.jsonwebtoken.security.Keys; // 키 생성
//import io.jsonwebtoken.security.SignatureException; // 서명 예외
//// 다른 예외 클래스들은 io.jsonwebtoken.* 에 포함되거나,
//// 위 Jwts 임포트만으로도 해결될 수 있습니다.
//
//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;
//import org.springframework.security.core.Authentication;
//import org.springframework.security.core.userdetails.UserDetails;
//import org.springframework.stereotype.Component;
//
//import java.security.Key;
//import java.util.Date;
//
//@Component
//public class JwtTokenProvider {
//
//    private static final Logger logger = LoggerFactory.getLogger(JwtTokenProvider.class);
//
//    // JWT_SECRET을 Base64 디코딩하여 Key 객체로 만듭니다.
//    private Key key() {
//        return Keys.hmacShaKeyFor(Decoders.BASE64.decode(JwtConstants.JWT_SECRET));
//    }
//
//    // JWT 토큰 생성
//    public String generateToken(Authentication authentication) {
//        UserDetails userPrincipal = (UserDetails) authentication.getPrincipal();
//
//        Date now = new Date();
//        Date expiryDate = new Date(now.getTime() + JwtConstants.JWT_EXPIRATION_MS);
//
//        return Jwts.builder()
//                .setSubject(userPrincipal.getUsername()) // 사용자 아이디
//                .setIssuedAt(new Date()) // 생성 시간
//                .setExpiration(expiryDate) // 만료 시간
//                .signWith(key(), SignatureAlgorithm.HS512) // 서명 (비밀 키와 알고리즘)
//                .compact();
//    }
//
//    // JWT 토큰에서 사용자 아이디 추출
//    public String getUsernameFromJwtToken(String token) {
//        return Jwts.parserBuilder().setSigningKey(key()).build()
//                .parseClaimsJws(token)
//                .getBody().getSubject();
//    }
//
//    // JWT 토큰 유효성 검사
//    public boolean validateToken(String authToken) {
//        try {
//            Jwts.parserBuilder().setSigningKey(key()).build().parseClaimsJws(authToken);
//            return true;
//        } catch (SignatureException ex) {
//            logger.error("Invalid JWT signature: {}", ex.getMessage());
//        } catch (MalformedJwtException ex) {
//            logger.error("Invalid JWT token: {}", ex.getMessage());
//        } catch (ExpiredJwtException ex) {
//            logger.error("JWT token is expired: {}", ex.getMessage());
//        } catch (UnsupportedJwtException ex) {
//            logger.error("JWT token is unsupported: {}", ex.getMessage());
//        } catch (IllegalArgumentException ex) {
//            logger.error("JWT claims string is empty: {}", ex.getMessage());
//        }
//        return false;
//    }
//}