# Các dự án quét repo GitHub: họ làm thế nào, Radar học được gì

Nghiên cứu ngày 16/10/2026. Câu hỏi: đã có repo/công cụ nào chuyên đi quét repo khác trên GitHub chưa, và họ làm ra sao.
**Có, khá nhiều**, nhưng hầu hết chỉ làm *một* trong ba việc: xếp hạng xu hướng, chấm điểm repo, hoặc tóm tắt bằng LLM. Radar làm cả ba nối
nhau (tìm, viết bài học có kiểm chứng, chuyển sang studio), nên điểm đáng học nằm ở *khâu tìm và xếp hạng*, không phải ở khâu viết.

## Mức tin cậy của từng nguồn

Môi trường dựng repo này chặn một số tên miền (`ossinsight.io`, `arxiv.org`, `docs.github.com` không mở được), nên:

- **Đã đọc trực tiếp trang gốc**: StarVelocity, best-of-generator, OpenSSF criticality_score, OpenSSF Scorecard, github-trending-digest, ai-trending-hub.
- **Chỉ thấy qua đoạn trích của công cụ tìm kiếm** (đừng coi là đã kiểm): OSSInsight, nghiên cứu sao giả StarScout, các actor Apify, starred/stargazed.
- Các trang bán hàng (Apify, Pagecrawl) là lời quảng cáo của chính họ.

## Những gì tìm thấy

| Nhóm | Ví dụ | Lấy dữ liệu từ đâu | Xếp hạng bằng gì |
|---|---|---|---|
| Theo dõi tốc độ tăng sao | [StarVelocity](https://github.com/mittohoa/starvelocity), các actor "star velocity" trên Apify | GitHub Search API để tìm, **GraphQL gộp 50 repo/lượt** để chụp số sao mỗi ngày | Sao tăng mỗi ngày trên cửa sổ 1, 7, 30 ngày, chia cho khoảng cách thật giữa hai lần chụp |
| Bảng xu hướng | Trang Trending của GitHub (nhiều actor Apify cào lại), OSSInsight (số liệu từ GH Archive, API `GET /v1/trends/repos/` theo `past_24_hours`…`past_3_months`) | Trang Trending, hoặc luồng sự kiện công khai GH Archive | Tăng sao/fork/PR trong khoảng thời gian, không công bố công thức đầy đủ |
| Danh sách tự cập nhật + điểm chất lượng | [best-of-generator](https://github.com/best-of-lists/best-of-generator) (họ `best-of-*`), `starred`, `stargazed`, `create-my-awesome` | `projects.yaml` do người chọn tay + GitHub, PyPI, npm, Libraries.io…; chạy bằng GitHub Actions rồi commit lại | `projectrank` = tổng điểm: 9 kiểm tra có/không (có license, có release, cập nhật trong 3 tháng…) cộng log của sao, fork, contributor, commit, issue đã đóng… |
| Chấm điểm sức khỏe/độ quan trọng/bảo mật | [OpenSSF criticality_score](https://github.com/ossf/criticality_score), [OpenSSF Scorecard](https://github.com/ossf/scorecard) | GitHub API quy mô lớn; Scorecard quét hơn 1,3 triệu repo mỗi tuần | Criticality: 10 tín hiệu, mỗi tín hiệu có **trọng số và ngưỡng trần** (contributor ×2, dependents ×2, `updated_since` ×−1…); Scorecard: 19 kiểm tra, gộp theo mức rủi ro Critical 10 / High 7,5 / Medium 5 / Low 2,5 |
| Bản tin tóm tắt bằng LLM | [github-trending-digest](https://github.com/andyxu1234/github-trending-digest), [ai-trending-hub](https://github.com/huiyishalou/ai-trending-hub) | Cào trang Trending (+ Hacker News) | Do GitHub Trending quyết; ai-trending-hub lọc theo từ khóa và có tham số ngưỡng "liên quan AI" (mặc định 0,7) |
| Nghiên cứu độ tin của sao | StarScout (CMU, bản 2: 6,0 triệu sao nghi giả trong 18.617 repo, 2019–2024) | Lịch sử stargazer và hoạt động của tài khoản | Hai dấu hiệu: tài khoản **ít hoạt động** và **đồng loạt** (lockstep) |

## Bảy bài học chung

1. **Search API chỉ trả tối đa 1.000 kết quả mỗi truy vấn**, nên một truy vấn "xếp theo sao" luôn trả đúng những repo kỳ cựu. StarVelocity cắt lát theo
   khoảng sao, ngày tạo, ngôn ngữ và chia ngân sách cho ba lượt: `new` 45%, `top` 35%, `active` 20%. Truy vấn nào chạm trần thì ghi là "phủ chưa đủ".
2. **Tổng sao không nói repo nào đang lên.** Chính StarVelocity viết: xếp theo tổng sao thì những repo cũ cả thập kỷ vẫn ở trên cùng; xếp theo sao/ngày mới lộ ra
   cái đang tăng. Muốn có tốc độ thì phải **tự chụp số sao mỗi lần quét** (GitHub không có API trả sẵn "sao tăng bao nhiêu"; dựng lại từ danh sách stargazer thì tốn rất nhiều lượt gọi).
3. **Cách tính tốc độ có quy tắc**: lấy lần chụp gần cửa sổ nhất, chia cho *số ngày thật* giữa hai lần chụp (lịch chạy không đều thì kết quả không lệch),
   và **"chưa biết" khác "bằng 0"**: lần chụp đầu tiên không được coi là "không tăng".
4. **Mỗi repo một điểm chụp mỗi ngày (khóa theo ngày UTC)**: chạy lại hay chạy trễ đều không làm hỏng dữ liệu.
5. **Điểm chất lượng là tổng điểm chọn theo kinh nghiệm**, hầu hết dùng log để một con số khổng lồ không át hết. best-of-generator tự nhận công thức "chọn theo kinh nghiệm,
   không có chứng minh khoa học"; criticality_score thêm trần cho từng tín hiệu. Bài học: dùng được, nhưng đừng coi là chân lý, và phải giải thích được vì sao một repo đứng đầu.
6. **Sao có thể mua, và tăng đột biến không phân biệt được thật hay giả.** StarVelocity không có cơ chế chống sao giả (chỉ có "cổng chất lượng" theo mô tả,
   tỉ lệ fork/sao, topic, license, độ mới); nghiên cứu StarScout cần dữ liệu tài khoản rất nặng. Hợp lý nhất cho công cụ nhỏ: **báo cờ, không tự quyết**.
7. **Đừng dựa vào dữ liệu công khai do bên thứ ba lưu**: dataset BigQuery của OpenSSF Scorecard đã không còn, và hạ tầng Google Cloud của criticality_score
   thông báo ngừng sau 29/08/2026. Phần còn lại của họ là các tệp CSV/JSON trong repo. Radar lấy mọi thứ trực tiếp từ GitHub và tự lưu lịch sử trong `state/`.

Ngoài ra, hai bản tin LLM cho thấy mẫu **chỉ gửi repo mới cho model, lưu lại bản tóm tắt để mỗi repo chỉ tóm một lần, khi LLM lỗi thì lùi về `description` của repo,
và dừng hẳn nếu bước quét trả về rỗng để khỏi ghi đè dữ liệu cũ**. Radar đã có sẵn các ý này theo cách riêng: `state/seen.json`, cổng kiểm tra, "giữ bài lỗi", dừng sớm khi mọi model hỏng.

## Radar trước và sau khi đọc nghiên cứu

| | Trước | Sau |
|---|---|---|
| Tìm | Mỗi topic một truy vấn xếp theo sao, 15 kết quả đầu, sàn 1500 sao: chỉ thấy các repo đã nổi | Thêm lượt `rising` mỗi topic: repo tạo trong 120 ngày gần nhất, sàn 300 sao. Trang kết quả xếp theo sao, nên ở topic nóng nó đầy repo đã trên 1500 sao: khi đó (và chỉ khi đó) hỏi thêm một lượt đúng dải 300–1499 sao |
| Tốc độ tăng | `sao / tuổi` (trung bình cả đời, không cần lịch sử) | Đo thật từ `state/stars.json` (mỗi lần quét chụp số sao); chưa có lịch sử thì lùi về `sao / tuổi`. Sau lần quét thứ hai (cách nhau 3–4 ngày) là đã đo được |
| Chọn | Tốt nhất mỗi nhóm, xoay vòng | Như cũ, nhưng **1 suất** dành cho repo đang lên (tối đa một nửa số bài, tắt được) |
| Chống số sao đáng ngờ | Không có | Hai **cờ chỉ để báo**: `few-forks` (dưới 10 fork trên 1.000 sao), `star-spike` (tăng từ 25% tổng sao trong một cửa sổ đo) |
| Gọi Search API | 16 truy vấn liên tiếp, 403 là bỏ | Cách nhau 2,1 giây (hạn mức 30 lượt/phút); gặp 403/429 kèm `Retry-After` ≤ 60 giây thì chờ đúng số giây đó cộng 1 giây rồi thử lại |
| Báo cáo | Chỉ các repo được chọn | Thêm `shortlist` (5 repo đứng ngay sau), `rising`, `stars_per_30d`, `velocity` (`measured`/`lifetime`), `flags`, `history.measured` |

Điểm số vẫn là `ln(sao) + 0,5·ln(1 + sao tăng/30 ngày) + 1 nếu có commit trong 30 ngày`. Chỉ đổi *nguồn* của số "sao tăng/30 ngày".
Cờ không đổi điểm và không loại repo. Nội dung bài không đổi: tốc độ tăng không đưa vào dữ kiện (`radar/facts.py`) nên model không viết về nó.

## Cố ý chưa làm, và vì sao

- **GraphQL gộp 50 repo/lượt.** StarVelocity cần nó vì theo dõi hàng nghìn repo. Radar chỉ theo dõi vài trăm repo mà Search API đã trả sẵn số sao, nên không tốn thêm lượt gọi nào.
  Cân nhắc lại nếu `history.tracked` vượt vài nghìn.
- **Điểm sức khỏe kiểu criticality/projectrank** (contributor, release, issue đã đóng…). Cần thêm vài lượt gọi API cho *mỗi* ứng viên, và chưa có bằng chứng nó giúp chọn bài hay hơn
  số sao + độ mới + tốc độ. Nên thêm khi đã có vài chục bài để so xem điểm có khớp với cảm nhận của chủ repo.
- **Phát hiện sao giả kiểu StarScout.** Cần lịch sử stargazer (có `starred_at`) và hoạt động từng tài khoản: hàng trăm lượt gọi mỗi repo. Hai cờ ở trên là phần rẻ nhất có thể làm bằng dữ liệu đã có.
- **Gia tốc** (`vel_7d − vel_30d` của StarVelocity). Cần cửa sổ 30 ngày, tức khoảng 8 lần quét. Làm sau khi `state/stars.json` đã dài đủ.
- **Dùng OSSInsight/GitHub Trending làm nguồn tìm.** Thêm một phụ thuộc ngoài GitHub, môi trường dựng repo không kiểm chứng được, và trang Trending không có API chính thức (các công cụ trên phải cào HTML).

## Cách đọc kết quả mới

```bash
python3 radar.py scan        # '*' sau cột stars/30d = đo từ lịch sử; [rising] = trong suất repo đang lên; [!few-forks] [!star-spike] = cờ
```

Trong `state/runs/<ngày>.json`: `history.measured` cho biết bao nhiêu ứng viên đã có tốc độ đo thật (0 ở lần quét đầu là bình thường);
`shortlist` là các repo suýt được chọn. Tắt lượt `rising`: `rising: {slots: 0}` trong `radar.yaml`.

## Nguồn

- [mittohoa/starvelocity](https://github.com/mittohoa/starvelocity), [best-of-lists/best-of-generator](https://github.com/best-of-lists/best-of-generator),
  [ossf/criticality_score](https://github.com/ossf/criticality_score), [ossf/scorecard](https://github.com/ossf/scorecard),
  [andyxu1234/github-trending-digest](https://github.com/andyxu1234/github-trending-digest), [huiyishalou/ai-trending-hub](https://github.com/huiyishalou/ai-trending-hub) (đã đọc trực tiếp).
- [OSSInsight: List trending repos](https://ossinsight.io/docs/api/list-trending-repos), [Six Million (Suspected) Fake Stars in GitHub](https://arxiv.org/abs/2412.13459),
  [Apify: GitHub Trending Tracker](https://apify.com/gochujang/github-trending-tracker), [Pagecrawl: star velocity alerts](https://pagecrawl.io/blog/github-trending-repository-star-velocity-alerts),
  [starred](https://pypi.org/project/starred/4.2.0) (chỉ qua kết quả tìm kiếm, chưa mở được trang gốc).
