package com.grrenhand.greenhand.chatbot.resource;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;

public class CustomByteArrayResource extends ByteArrayResource {

    private String filename;
    private MediaType contentType; // MediaType 객체를 직접 저장 (오버라이드는 안 함)

    public CustomByteArrayResource(byte[] byteArray, String filename, MediaType contentType) {
        super(byteArray);
        this.filename = filename;
        this.contentType = contentType;
    }

    @Override
    public String getFilename() {
        return filename;
    }

    // Spring의 Resource 인터페이스에는 getContentType() 메서드가 없습니다.
    // 따라서 이 메서드를 오버라이드할 수 없습니다. 컴파일 오류가 나는 이유입니다.
    // 이 메서드를 제거합니다.
    /*
    @Override
    public String getContentType() { // 이 오버라이드 메서드 때문에 오류 발생
        return contentType != null ? contentType.toString() : super.getContentType();
    }
    */

    // 추가: RestTemplate이 ContentType을 알 수 있도록 Resource 구현체 내에 노출 (선택 사항, RestTemplate 버전에 따라 다름)
    // Spring 5.x 이상에서는 Resource의 Content-Type 추론 로직이 개선되었습니다.
    // getContentType()을 오버라이드하는 대신, getDescription()이나 다른 정보성 메서드에 포함시키거나
    // RestTemplate에서 HttpHeaders를 통해 명시적으로 Content-Type을 설정하는 것이 더 일반적입니다.
    // 여기서는 일단 오류를 해결하기 위해 제거합니다.

    // 만약 이 contentType 정보가 필요하다면, getter를 추가하여 다른 곳에서 사용할 수 있습니다.
    public MediaType getCustomContentType() {
        return contentType;
    }
}