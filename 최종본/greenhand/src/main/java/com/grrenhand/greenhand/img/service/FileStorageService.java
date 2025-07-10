// src/main/java/com/grrenhand/greenhand/img/service/FileStorageService.java

package com.grrenhand.greenhand.img.service; // 패키지명 변경: img.service

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

@Service
public class FileStorageService {

    @Value("${file.upload-dir}")
    private String uploadDir;

    public String storeFile(MultipartFile file, String subDirectory) throws IOException {
        Path uploadPath = Paths.get(uploadDir, subDirectory).toAbsolutePath().normalize();
        Files.createDirectories(uploadPath);

        String fileExtension = "";
        String originalFileName = file.getOriginalFilename();
        if (originalFileName != null && originalFileName.contains(".")) {
            fileExtension = originalFileName.substring(originalFileName.lastIndexOf("."));
        }
        String fileName = UUID.randomUUID().toString() + fileExtension;
        Path targetLocation = uploadPath.resolve(fileName);

        Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);

        return "/uploads/" + subDirectory + "/" + fileName;
    }

    public void deleteFile(String filePath) throws IOException {
        if (filePath == null || filePath.isEmpty()) {
            return;
        }
        String relativePath = filePath.replaceFirst("/uploads/", "");
        Path targetLocation = Paths.get(uploadDir, relativePath).toAbsolutePath().normalize();
        if (Files.exists(targetLocation)) {
            Files.delete(targetLocation);
            System.out.println("DEBUG: 파일 삭제됨: " + targetLocation);
        } else {
            System.out.println("DEBUG: 삭제할 파일을 찾을 수 없음: " + targetLocation);
        }
    }
}
