# DDL 기반 Domain(Entity) 및 Repository 생성을 위한 프롬프트

다음 DDL 정보를 기반으로 Java(Spring Boot, JPA) 환경에서 사용할 수 있는 **Domain(Entity) 클래스**와 **Repository 인터페이스**를 생성해줘.

- **JPA 어노테이션**을 사용해 테이블과 컬럼 매핑을 정확하게 지정하고, **기본키(primary key)**, **제약 조건(nullable, unique 등)**, **데이터 타입** 등을 정확히 반영해.
- 클래스 이름은 **테이블 이름을 카멜 케이스**로 변환하여 작성해.
- 컬럼 이름은 자바 스타일로 **카멜 케이스**로 변환하고, `@Column(name = "원래 컬럼명")` 어노테이션으로 원래 DB 컬럼명을 명시해.
- 날짜/시간 타입은 **`LocalDateTime` 또는 `LocalDate`**로 변환해.
- 제약 조건 (`NOT NULL`, `UNIQUE`) 등은 가능한 한 Entity에 반영해.
- Repository는 `JpaRepository<엔티티명, ID타입>`을 상속하는 interface로 생성해.

## DDL 예시

```sql
CREATE TABLE user_account (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 요구되는 출력 형식

1. Java Entity 클래스 (`package com.example.domain`)
2. Java Repository 인터페이스 (`package com.example.repository`)
