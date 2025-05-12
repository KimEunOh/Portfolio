package com.example;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;
import org.json.JSONArray;
import java.io.FileWriter;

public class ApiClient {
    public static void main(String[] args) {
        try {
            String apiUrl = "http://192.168.10.118:5000/api/data";
            URL url = new URL(apiUrl);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            
            conn.setRequestMethod("GET");
            conn.setRequestProperty("User-Agent", "Mozilla/5.0");
            conn.setRequestProperty("Accept", "application/json");
            conn.setRequestProperty("Content-Type", "application/json");
            
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String inputLine;
            StringBuilder response = new StringBuilder();
            
            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine);
            }
            in.close();
            
            // JSON 배열인 경우
            JSONArray jsonArray = new JSONArray(response.toString());
            try (FileWriter file = new FileWriter("data.json")) {
                file.write(jsonArray.toString(4));
                System.out.println("JSON 파일이 성공적으로 저장되었습니다.");
            }
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}