package kr.ntoday.adminsystem.domain.system;

import jakarta.persistence.*;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Getter
@NoArgsConstructor
@Entity
@Table(name = "tbl_position_info")
public class PositionInfo {
    @Id
    @Column(name = "pst_code")
    private String pstCode;

    @Column(name = "pst_nm")
    private String pstNm;

    @Column(name = "sno")
    private Integer sno;

    @Column(name = "reg_ps_id")
    private String regPsId;

    @Column(name = "reg_dtm")
    private LocalDateTime regDtm;

    @Column(name = "upd_ps_id")
    private String updPsId;

    @Column(name = "upd_dtm")
    private LocalDateTime updDtm;

    @Column(name = "del_at")
    private String delAt;

    @Builder
    public PositionInfo(String pstCode, String pstNm, Integer sno, String regPsId, LocalDateTime regDtm,
                        String updPsId, LocalDateTime updDtm, String delAt) {
        this.pstCode = pstCode;
        this.pstNm = pstNm;
        this.sno = sno;
        this.regPsId = regPsId;
        this.regDtm = regDtm;
        this.updPsId = updPsId;
        this.updDtm = updDtm;
        this.delAt = delAt;
    }
}