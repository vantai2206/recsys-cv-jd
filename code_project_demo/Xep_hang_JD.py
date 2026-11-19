"""Gợi ý tin tuyển dụng (JD) phù hợp với một CV.

Đầu vào : 1 file CV + kho tin tuyển dụng gộp từ nhiều nền tảng.
Đầu ra  : danh sách tin xếp theo mức độ đáp ứng (%), kèm kỹ năng còn thiếu.

Dùng lại nguyên bộ chuẩn hóa kỹ năng 3 tầng ở Chuan_hoa_ngon_ngu.py.
"""

from pathlib import Path
import json

from Chuan_hoa_ngon_ngu import (
    alias_theo_do_dai_giam,
    doc_tu_dien_nguoc,
    trich_xuat_ky_nang,
)

THU_MUC_DATA = Path(__file__).parent / "data"
DUONG_DAN_KY_NANG = THU_MUC_DATA / "ky_nang.json"
DUONG_DAN_TIN = THU_MUC_DATA / "tin_tuyen_dung.json"

# Kỹ năng bắt buộc quan trọng hơn kỹ năng ưu tiên. Hai số này phải cộng lại bằng 1.
TRONG_SO_BAT_BUOC = 0.8
TRONG_SO_UU_TIEN = 0.2
assert TRONG_SO_BAT_BUOC + TRONG_SO_UU_TIEN == 1, "Hai trong so phai cong lai bang 1"


def doc_kho_tin(duong_dan=DUONG_DAN_TIN) -> list[dict]:
    """Đọc kho tin tuyển dụng.

    File JSON có dạng {"_ghi_chu": ..., "tin": [...]} nên chỉ lấy khóa "tin";
    dòng ghi chú tự khắc nằm ngoài.
    """
    with open(duong_dan, encoding="utf-8") as f:
        data = json.load(f)
    return data["tin"]


def ky_nang_cua_cv(duong_dan_cv, tu_dien_nguoc: dict[str, str]) -> list[str]:
    """Trích xuất kỹ năng từ một file CV dạng văn bản."""
    van_ban = Path(duong_dan_cv).read_text(encoding="utf-8")
    return trich_xuat_ky_nang(van_ban, tu_dien_nguoc)


def phan_tich_tin(
    tin: dict,
    tu_dien_nguoc: dict[str, str],
    danh_sach_alias: list[str] | None = None,
) -> dict:
    """Thêm hai trường kỹ năng đã chuẩn hóa vào một tin tuyển dụng.

    Mục 'YÊU CẦU BẮT BUỘC' và 'YÊU CẦU ƯU TIÊN' được trích xuất RIÊNG,
    vì thiếu một kỹ năng bắt buộc nặng hơn hẳn thiếu một kỹ năng ưu tiên.

    Trường 'ngoai_tu_dien' phân biệt hai chuyện rất khác nhau mà cùng cho ra
    danh sách kỹ năng rỗng:
      - tin KHÔNG đòi gì  -> rỗng là đúng, ai cũng đáp ứng được
      - tin CÓ đòi nhưng từ điển không hiểu chữ nào -> rỗng là do TA mù,
        không phải do đề dễ. Không được chấm điểm cho trường hợp này.
    """
    tin = dict(tin)  # sao chép, không sửa dữ liệu gốc
    van_ban_bat_buoc = " ".join(tin["yeu_cau_bat_buoc"]).strip()
    van_ban_uu_tien = " ".join(tin["yeu_cau_uu_tien"]).strip()

    tin["ky_nang_bat_buoc"] = trich_xuat_ky_nang(
        van_ban_bat_buoc, tu_dien_nguoc, danh_sach_alias
    )
    tin["ky_nang_uu_tien"] = trich_xuat_ky_nang(
        van_ban_uu_tien, tu_dien_nguoc, danh_sach_alias
    )
    tin["ngoai_tu_dien"] = bool(van_ban_bat_buoc) and not tin["ky_nang_bat_buoc"]
    return tin


def ty_le_dap_ung(ky_nang_cv: list[str], ky_nang_yeu_cau: list[str]) -> float:
    """Công thức của bài báo (bản đã sửa lỗi in): 1 - #(S̃ - S) / #S̃

    S  = kỹ năng ứng viên có, S̃ = kỹ năng tin tuyển dụng đòi.
    Đếm phần tin ĐÒI mà ứng viên KHÔNG có, chia cho tổng số tin đòi.

    Danh sách yêu cầu rỗng thì trả 1.0 (không đòi gì thì coi như đáp ứng đủ,
    và cũng để không chia cho 0). Việc canh xem cái rỗng đó có ĐÁNG TIN không
    là của phan_tich_tin / cham_diem, không phải của hàm này.
    """
    if not ky_nang_yeu_cau:
        return 1.0
    thieu = [k for k in ky_nang_yeu_cau if k not in ky_nang_cv]
    return 1 - len(thieu) / len(ky_nang_yeu_cau)


def cham_diem(ky_nang_cv: list[str], tin_da_phan_tich: dict) -> dict:
    """Chấm một tin: trả về bản sao có điểm, phần trăm và kỹ năng thiếu."""
    bat_buoc = tin_da_phan_tich["ky_nang_bat_buoc"]
    uu_tien = tin_da_phan_tich["ky_nang_uu_tien"]

    ty_le_bb = ty_le_dap_ung(ky_nang_cv, bat_buoc)
    ty_le_ut = ty_le_dap_ung(ky_nang_cv, uu_tien)
    diem = TRONG_SO_BAT_BUOC * ty_le_bb + TRONG_SO_UU_TIEN * ty_le_ut

    ket_qua = dict(tin_da_phan_tich)
    ket_qua["thieu_bat_buoc"] = [k for k in bat_buoc if k not in ky_nang_cv]
    ket_qua["thieu_uu_tien"] = [k for k in uu_tien if k not in ky_nang_cv]
    ket_qua["co_san"] = [k for k in bat_buoc if k in ky_nang_cv]

    if ket_qua["ngoai_tu_dien"]:
        # Tin đòi những thứ từ điển chưa biết (vd "Spring Boot, Hibernate, Kafka").
        # Không có cơ sở nào để nói ứng viên đáp ứng bao nhiêu phần trăm -> cho 0
        # và gắn cờ, thay vì để nó trèo lên đầu bảng với 100%.
        ket_qua["diem"] = 0.0
        ket_qua["phan_tram"] = 0
        ket_qua["phan_tram_bat_buoc"] = 0
        ket_qua["du_dieu_kien"] = False
        return ket_qua

    ket_qua["diem"] = diem
    ket_qua["phan_tram"] = round(diem * 100)
    ket_qua["phan_tram_bat_buoc"] = round(ty_le_bb * 100)
    ket_qua["du_dieu_kien"] = not ket_qua["thieu_bat_buoc"]
    return ket_qua


def xep_hang(
    ky_nang_cv: list[str],
    kho_tin: list[dict],
    tu_dien_nguoc: dict[str, str],
    k: int | None = None,
    nguon: str | None = None,
    giu_tin_ngoai_tu_dien: bool = False,
) -> list[dict]:
    """Chấm điểm toàn bộ kho tin rồi sắp xếp giảm dần.

    nguon : lọc theo nền tảng ("ITviec", "TopCV"...), None là lấy hết.
    k     : lấy K tin đầu, None là lấy hết.
    giu_tin_ngoai_tu_dien : mặc định LOẠI các tin mà từ điển không đọc nổi
            yêu cầu bắt buộc. Bật True khi muốn soi xem từ điển đang hụt ở đâu.
    """
    # Sắp xếp 93 alias theo độ dài một lần duy nhất rồi truyền xuống, thay vì
    # để mỗi tin tự sort lại (1000 tin sẽ là 2000 lần sort thừa).
    danh_sach_alias = alias_theo_do_dai_giam(tu_dien_nguoc)

    da_cham = [
        cham_diem(ky_nang_cv, phan_tich_tin(tin, tu_dien_nguoc, danh_sach_alias))
        for tin in kho_tin
        if nguon is None or tin["nguon"] == nguon
    ]

    if not giu_tin_ngoai_tu_dien:
        da_cham = [t for t in da_cham if not t["ngoai_tu_dien"]]

    # Sắp giảm dần theo điểm; cùng điểm thì tin nào thiếu ít kỹ năng bắt buộc
    # hơn đứng trước; vẫn bằng nhau thì theo mã cho kết quả ổn định.
    da_cham.sort(key=lambda t: (-t["diem"], len(t["thieu_bat_buoc"]), t["ma"]))

    return da_cham if k is None else da_cham[:k]


def tin_ngoai_tu_dien(
    kho_tin: list[dict], tu_dien_nguoc: dict[str, str]
) -> list[dict]:
    """Các tin mà từ điển không đọc nổi yêu cầu bắt buộc.

    Đây là danh sách việc cần làm cho từ điển (hoặc cho bước trích xuất bằng
    LLM sau này), không phải kết quả gợi ý cho người dùng.
    """
    danh_sach_alias = alias_theo_do_dai_giam(tu_dien_nguoc)
    da_phan_tich = [
        phan_tich_tin(tin, tu_dien_nguoc, danh_sach_alias) for tin in kho_tin
    ]
    return [t for t in da_phan_tich if t["ngoai_tu_dien"]]


def thanh_do(phan_tram: int, do_rong: int = 20) -> str:
    """Vẽ thanh tiến độ bằng ký tự cho dễ nhìn trên terminal."""
    so_o_day = round(phan_tram / 100 * do_rong)
    return "#" * so_o_day + "." * (do_rong - so_o_day)


def in_bang_xep_hang(
    ket_qua: list[dict], ky_nang_cv: list[str], so_tin_bi_loai: int = 0
) -> None:
    print()
    print("KY NANG DOC DUOC TU CV:", ", ".join(sorted(ky_nang_cv)))
    if so_tin_bi_loai:
        print(f"(Da loai {so_tin_bi_loai} tin vi tu dien khong doc noi yeu cau)")
    print("=" * 78)
    for thu_tu, tin in enumerate(ket_qua, start=1):
        nhan = "DU DIEU KIEN" if tin["du_dieu_kien"] else "CON THIEU"
        print()
        print(f"{thu_tu}. {tin['tieu_de']} - {tin['cong_ty']}")
        print(f"   {thanh_do(tin['phan_tram'])}  {tin['phan_tram']}%  [{nhan}]")
        print(f"   Nguon: {tin['nguon']}  |  {tin['dia_diem']}  |  {tin['muc_luong']}")
        print(f"   {tin['link']}")
        print(f"   Bat buoc: dap ung {tin['phan_tram_bat_buoc']}%", end="")
        if tin["thieu_bat_buoc"]:
            print(" - thieu: " + ", ".join(tin["thieu_bat_buoc"]))
        else:
            print(" - du het")
        if tin["co_san"]:
            print("   Ban da co: " + ", ".join(tin["co_san"]))
        if tin["thieu_uu_tien"]:
            print("   Uu tien con thieu: " + ", ".join(tin["thieu_uu_tien"]))


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")

    td = doc_tu_dien_nguoc(DUONG_DAN_KY_NANG)
    kho = doc_kho_tin()
    cv = ky_nang_cua_cv(THU_MUC_DATA / "cv_mau.txt", td)

    # --- Kiểm tra công thức tính tỷ lệ ---
    assert ty_le_dap_ung(["python", "sql"], ["python", "sql"]) == 1.0
    assert ty_le_dap_ung(["python"], ["python", "sql"]) == 0.5
    assert ty_le_dap_ung([], ["python", "sql"]) == 0.0
    assert ty_le_dap_ung(["python", "sql"], []) == 1.0
    # Biet THUA ky nang khong bi tru diem (loi in trong bai bao se cho 0.0 o day)
    assert ty_le_dap_ung(["python", "sql", "git", "aws"], ["python", "sql"]) == 1.0
    print("Cong thuc ty le dap ung: tat ca assert deu qua!")

    # --- Kiểm tra việc đọc kho tin ---
    assert len(kho) == 12
    assert {t["nguon"] for t in kho} == {"ITviec", "TopCV", "VietnamWorks", "LinkedIn"}
    assert all(t["link"].startswith("https://") for t in kho)
    print("Kho tin: tat ca assert deu qua!")

    # --- Kiểm tra trích xuất kỹ năng từ tin ---
    tin_devops = phan_tich_tin(kho[1], td)  # ITV002 DevOps Engineer
    assert set(tin_devops["ky_nang_bat_buoc"]) == {
        "python", "docker", "kubernetes", "ci/cd",
        "terraform", "aws", "linux", "git", "sql",
    }
    assert set(tin_devops["ky_nang_uu_tien"]) == {"monitoring", "agile"}
    tin_mobile = phan_tich_tin(kho[11], td)  # LKD002 React Native
    assert "react native" in tin_mobile["ky_nang_bat_buoc"]
    assert "react" not in tin_mobile["ky_nang_bat_buoc"]  # khong bi nuot nham
    print("Phan tich tin: tat ca assert deu qua!")

    # --- LOI 1 (ra soat 18/09): tin khong rut duoc ky nang nao -> cham 100% ---
    # Tin duoi doi Spring Boot / Hibernate / Kafka - khong co trong tu dien 23
    # ky nang. Truoc khi sua: ky_nang_bat_buoc = [] -> ty le 100% -> dung HANG 2
    # ca bang. Khi crawl tin that, tin nao he thong hieu it nhat se treo len dau.
    tin_la = {
        "ma": "TEST999",
        "tieu_de": "Java Backend (Spring)",
        "cong_ty": "Cong ty Test",
        "nguon": "TopCV",
        "link": "https://www.topcv.vn/viec-lam/vi-du-test999",
        "dia_diem": "Ha Noi",
        "muc_luong": "25 - 35 trieu",
        "ngay_dang": "2026-09-20",
        "yeu_cau_bat_buoc": ["5 nam kinh nghiem Spring Boot, Hibernate, Kafka."],
        "yeu_cau_uu_tien": [],
    }
    da_phan_tich = phan_tich_tin(tin_la, td)
    assert da_phan_tich["ky_nang_bat_buoc"] == []  # tu dien that su khong hieu
    assert da_phan_tich["ngoai_tu_dien"] is True  # ...va ta BIET la minh khong hieu
    cham_tin_la = cham_diem(cv, da_phan_tich)
    assert cham_tin_la["phan_tram"] == 0  # khong con 100%
    assert cham_tin_la["du_dieu_kien"] is False

    # Tin that su KHONG doi gi thi van la 100% - hai truong hop phai khac nhau
    tin_rong = dict(tin_la, ma="TEST998", yeu_cau_bat_buoc=[])
    cham_tin_rong = cham_diem(cv, phan_tich_tin(tin_rong, td))
    assert cham_tin_rong["ngoai_tu_dien"] is False
    assert cham_tin_rong["phan_tram"] == 100

    kho_co_tin_la = kho + [tin_la]
    bang_loc = xep_hang(cv, kho_co_tin_la, td)
    assert len(bang_loc) == 12  # tin la bi loai khoi bang goi y
    assert "TEST999" not in [t["ma"] for t in bang_loc]

    bang_giu = xep_hang(cv, kho_co_tin_la, td, giu_tin_ngoai_tu_dien=True)
    assert len(bang_giu) == 13
    assert bang_giu[-1]["ma"] == "TEST999"  # giu lai thi nam duoi cung, khong phai hang 2

    assert [t["ma"] for t in tin_ngoai_tu_dien(kho_co_tin_la, td)] == ["TEST999"]
    assert tin_ngoai_tu_dien(kho, td) == []  # 12 tin mau deu doc duoc
    print("Tin ngoai tu dien (loi 1): tat ca assert deu qua!")

    # --- Kiểm tra xếp hạng ---
    bang = xep_hang(cv, kho, td)
    assert len(bang) == 12
    assert all(bang[i]["diem"] >= bang[i + 1]["diem"] for i in range(len(bang) - 1))
    assert bang[0]["ma"] == "TCV001"  # Python Junior: An du het yeu cau bat buoc
    assert bang[0]["du_dieu_kien"] is True
    assert bang[0]["phan_tram"] == 100
    assert [t["ma"] for t in bang[:3]] == ["TCV001", "ITV003", "TCV003"]
    assert sum(1 for t in bang if t["du_dieu_kien"]) == 3

    assert bang[-1]["ma"] == "VNW003"  # SRE: xa nhat voi ho so cua An

    # Diem uu tien co the DAO thu tu: ITV002 dap ung it yeu cau bat buoc hon
    # VNW001 (44% so voi 50%) nhung van xep tren, vi no co mot ky nang uu tien
    # (agile) ma An co. Day la ly do bang ket qua phai hien ca hai con so.
    vi_tri = {t["ma"]: i for i, t in enumerate(bang)}
    itv002 = next(t for t in bang if t["ma"] == "ITV002")
    vnw001 = next(t for t in bang if t["ma"] == "VNW001")
    assert itv002["phan_tram_bat_buoc"] < vnw001["phan_tram_bat_buoc"]
    assert vi_tri["ITV002"] < vi_tri["VNW001"]

    chi_topcv = xep_hang(cv, kho, td, nguon="TopCV")
    assert len(chi_topcv) == 4
    assert all(t["nguon"] == "TopCV" for t in chi_topcv)

    top3 = xep_hang(cv, kho, td, k=3)
    assert len(top3) == 3
    print("Xep hang: tat ca assert deu qua!")

    in_bang_xep_hang(
        xep_hang(cv, kho_co_tin_la, td, k=5),
        cv,
        so_tin_bi_loai=len(tin_ngoai_tu_dien(kho_co_tin_la, td)),
    )
