---
id: R06
title: Graphify: biến thư mục mã và tài liệu thành đồ thị tri thức để agent truy vấn
topic: ky-thuat
date: 2026-10-30
---
# Graphify: biến thư mục mã và tài liệu thành đồ thị tri thức để agent truy vấn

## Tóm tắt

Graphify là gì, tiết kiệm được bao nhiêu cho agent lập trình, và con số nào đáng tin? Câu trả lời ngắn: đây là một **kỹ năng (skill) cho trợ lý lập trình AI** kèm thư viện Python. Gõ `/graphify .` trong Claude Code, Codex, Cursor hay Gemini CLI, nó đọc cả thư mục (mã, tài liệu, PDF, ảnh, video) rồi dựng một **đồ thị tri thức** để hỏi đáp thay vì lục từng tệp bằng grep [S1]. Phần mã được phân tích cục bộ bằng cây cú pháp tree-sitter, tất định, không gọi mô hình; chỉ tài liệu, PDF và ảnh mới cần một lượt "ngữ nghĩa" qua mô hình của bạn [S1] [S4].

Bài đọc repo theo ba tầng. Tầng một là bản đồ: Graphify làm gì, cài thế nào, ba tệp đầu ra, đường ống bảy bước [S1] [S2]. Tầng hai là cơ chế làm nên khác biệt: nhãn tin cậy trên từng cạnh (`EXTRACTED`, `INFERRED`, `AMBIGUOUS`), không dùng embedding, nhận diện cộng đồng bằng Leiden, và cách đồ thị được đưa vào agent qua hook, tệp chỉ dẫn và máy chủ MCP [S1] [S2] [S4] [S10]. Tầng ba là phản biện: các số đo, chỗ tài liệu tự mâu thuẫn, an toàn, và đường dẫn từ công cụ miễn phí sang sản phẩm trả tiền [S3] [S5] [S1].

Mỗi khẳng định mang một trong bốn nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ tệp của repo ở commit `0a8cd4e` (27/10/2026, nhánh `v8`). **Người viết đếm** là con số tính bằng lệnh trên bản đã tải, bạn tự kiểm lại được. **Dữ liệu radar** là số đọc từ `state/stars.json` của repo GitHub Radar, không ghim được vào commit. **Phản biện** là nhận định của người viết, không phải điều repo tuyên bố. Người viết **không chạy** Graphify: việc cài gói ngoài bị chặn trong phiên làm bài này, nên mọi mô tả hành vi đều là từ tài liệu và mã, chưa phải từ lần chạy thật.

Ba ý đáng mang theo. Thứ nhất, Graphify đặt cược vào **đồ thị có kiểm soát độ tin cậy thay cho vector**: mỗi cạnh nói rõ là đọc thẳng từ nguồn hay suy ra, và phần mã không tốn token để dựng [S1] [S2]. Thứ hai, các số đo công khai là **thật nhưng nhỏ và do chính dự án đo**: 6 câu hỏi trên ERPNext, 50 câu LongMemEval, 12 cạnh được kiểm tay; con số "giảm 80% token" nổi bật nhất không có bảng đo nào đỡ trong BENCHMARKS và gắn với sản phẩm Cloud [S3] [S1]. Thứ ba, dự án **đổi cực nhanh** (hai bản phát hành trong hai ngày, 240 mục phiên bản từ 3/4/2026) nên cần ghim phiên bản và đọc changelog trước khi nâng [S7].

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Skill cho trợ lý lập trình AI + thư viện Python + CLI `graphify`; gói PyPI tên `graphifyy` (hai chữ y) | Nguồn: repo [S1] [S8] |
| Bản hiện tại | 0.9.97, ngày 27/10/2026; Python 3.10 trở lên | Nguồn: repo [S7] [S8] |
| Giấy phép | Apache-2.0; phần đóng góp trước khi đổi giấy phép vẫn theo MIT, giữ trong `LICENSE-MIT` | Nguồn: repo [S8] |
| Số sao | 137.165 (28/10/2026); 127.752 ngày 17/10, tức thêm 9.413 sao trong 11 ngày | Dữ liệu radar [S11] |
| Quy mô | 1.118 tệp; 96 tệp Python trong `graphify/` với 90.797 dòng; tests 143.000 dòng, 7.155 hàm `test_` | Người viết đếm |
| Đầu ra | `graph.html`, `GRAPH_REPORT.md`, `graph.json` trong `graphify-out/` | Nguồn: repo [S1] |
| Tích hợp | 16 tệp skill sinh sẵn; máy chủ MCP có 10 công cụ và 6 tài nguyên | Người viết đếm [S10] |
| Thương mại | Graphify Cloud, dùng thử 14 ngày; huy hiệu Y Combinator S26 | Nguồn: repo [S1] |

## Repo này là gì

Graphify nhắm vào một nỗi đau cụ thể: trợ lý lập trình đọc lại gần như cả repo mỗi phiên, tốn token và vẫn hay trả lời thiếu quan hệ giữa các phần. README mô tả lời giải bằng ba ý [S1]:

- **Mã dựng miễn phí, cục bộ.** Mã được phân tích bằng cây cú pháp tree-sitter, tất định, không mô hình, không gửi gì ra ngoài [S1].
- **Mỗi cạnh có giải thích.** Cạnh gắn nhãn `EXTRACTED` (nói thẳng trong nguồn) hoặc `INFERRED` (do Graphify suy ra), nên biết cái nào đọc trực tiếp, cái nào suy đoán [S1].
- **Không phải chỉ mục vector.** Không embedding, không kho vector; là một đồ thị thật để duyệt: hỏi một câu, lần đường giữa hai thứ, hoặc giải thích một khái niệm [S1].

Bảng "Graphify làm được gì" trong README liệt kê: nút thần (god nodes, các khái niệm nhiều kết nối nhất), cộng đồng (chia đồ thị thành hệ con bằng Leiden, nhãn không cần mô hình), liên kết chéo tệp (`calls`, `imports`, `inherits`, `mixes_in`), truy vấn/đường đi/giải thích, ghi chú lý do (`# NOTE:`, `# WHY:`, trích dẫn ADR/RFC thành nút), và hỗ trợ ngoài mã (tài liệu, PDF, ảnh, âm thanh, video) [S1].

Về giới hạn, README tự nói các cạnh `INFERRED` là suy ra, không phải đọc thẳng [S1]. Chính `AGENTS.md` của repo dặn không dùng đồ thị làm bằng chứng khi việc đang kiểm tra tính đúng của chính đồ thị [S6].

## Bắt đầu nhanh

Cài hai lệnh, rồi gõ một lệnh trong trợ lý [S1]:

```bash
uv tool install graphifyy      # install the CLI (or: pipx install graphifyy)
graphify install               # detects your assistant and registers the skill
```

Rồi trong trợ lý gõ `/graphify .` (Codex dùng `$graphify`) [S1]. README cảnh báo gói chính thức là `graphifyy`, các gói `graphify*` khác trên PyPI không liên quan [S1]. `graphify install --project` ghi skill vào thư mục dự án để commit [S1].

Có 16 tệp skill sinh sẵn cho các nền tảng khác nhau (người viết đếm); README kể hơn hai chục trợ lý, từ Claude Code, Codex, Cursor, Gemini CLI đến Kiro, Pi, Devin CLI, Antigravity [S1]. Các tính năng tuỳ chọn cài bằng "extras" như `pdf`, `video`, `mcp`, `watch`, `leiden`, `neo4j`, `all` [S1].

## Đường ống từ thư mục đến đồ thị

Kiến trúc là một đường ống bảy bước, mỗi bước một module, trao đổi bằng dict thuần và đồ thị NetworkX [S2]:

`detect()` → `extract()` → `build()` → `cluster()` → phân tích → `report.generate()` → `export.to_*()` [S2].

| Module | Việc | Nhãn |
|---|---|---|
| `detect.py` | Quét thư mục, gom tệp theo loại, đếm từ | Nguồn: repo [S2] |
| `extract.py` | Danh sách tệp → `{nodes, edges}`; `collect_files` mở rộng thư mục | Nguồn: repo [S2] |
| `build.py` | Gộp các kết quả thành `nx.Graph` | Nguồn: repo [S2] |
| `cluster.py` | Chia cộng đồng, không sửa đồ thị | Nguồn: repo [S2] |
| `analyze.py` | `god_nodes`, `surprising_connections`, `suggest_questions`, `find_import_cycles`, `graph_diff` | Nguồn: repo [S2] |
| `export.py` | `to_json`, `to_html`, `to_obsidian`, `to_svg`, `to_graphml`, `to_canvas`, `to_cypher` | Nguồn: repo [S2] |

Giải thích ba lượt xử lý theo `docs/how-it-works.md` [S4]: lượt 1 là cấu trúc mã (miễn phí, không gọi API); lượt 2 là video và âm thanh (phiên âm cục bộ bằng faster-whisper, câu mồi lấy từ các nút thần); lượt 3 là tài liệu, PDF, ảnh (các tác tử con của mô hình chạy song song, mỗi tác tử trả một mảnh JSON rồi gộp). Nếu thư mục chỉ có mã thì lượt 3 bị bỏ hẳn [S4].

Hai chi tiết kỹ thuật đáng chú ý. Một: kết quả mã được trích song song bằng `ProcessPoolExecutor`, và mỗi tệp được băm SHA256 để lần chạy sau bỏ qua tệp không đổi, cache nằm ở `graphify-out/cache/` [S4]. Hai: `ARCHITECTURE.md` dặn luôn truyền `root` khi gọi `extract()` từ mã riêng, vì nếu bỏ, mã nút sinh từ thư mục cha chung của danh sách tệp và có thể mang đường dẫn của máy khác [S2].

## Độ tin cậy của từng cạnh

Đây là ý tưởng khác biệt nhất. Mỗi quan hệ mang một trong ba nhãn [S2] [S4]:

| Nhãn | Nghĩa | Điểm tin cậy |
|---|---|---|
| `EXTRACTED` | Nói thẳng trong nguồn (câu import, lời gọi trực tiếp) | Luôn 1,0 [S4] |
| `INFERRED` | Suy luận hợp lý | 0,95 / 0,85 / 0,75 / 0,65 / 0,55 theo thang rời rạc [S4] |
| `AMBIGUOUS` | Không chắc, đánh dấu để người xem lại trong `GRAPH_REPORT.md` | Tài liệu không nêu điểm [S2] |

`CONTRIBUTING.md` biến nguyên tắc này thành luật cho người đóng góp: giữ suy luận tách khỏi sự thật đã trích, ưu tiên "đóng khi nghi ngờ" hơn đoán quan hệ, và một bản ghi có nguồn thật không được thua một nút giả giàu thông tin nhưng không có nguồn [S6]. Phần changelog cho thấy luật này thật sự đi vào mã: ví dụ bản 0.9.96 sửa để `run()` không còn nối nhầm vào `_run()`, hoặc một nút có nhãn `extracted` viết thường vẫn bị kiểm bằng chứng trước khi gộp thành `EXTRACTED` [S7].

Về phát hiện cộng đồng: dùng thuật toán Leiden, không cần embedding, vì cạnh tương đồng ngữ nghĩa đã nằm trong đồ thị và tự định hình cộng đồng [S4]. Lưu ý thực tế: không cài extra `leiden` thì hệ thống lặng lẽ dùng Louvain của networkx, và đổi qua lại sẽ xáo toàn bộ cộng đồng, phải gắn nhãn lại [S1].

## Dùng đồ thị: truy vấn, MCP, luôn bật

Sau khi có `graph.json`, truy vấn không cần trợ lý [S1]:

```bash
/graphify query "what connects auth to the database?"
/graphify path "UserService" "DatabasePool"
/graphify explain "RateLimiter"
```

Tên khớp nhiều nút bị từ chối kèm danh sách ứng viên thay vì đoán; mã thoát `0` là có đáp án, `3` là tên mơ hồ, `4` là không có nút khớp [S1]. README mẫu cho thấy `graphify path "FastAPI" "ModelField"` ra đường 3 bước [S1].

Để agent thật sự dùng đồ thị, `graphify <nền tảng> install` ghi tệp chỉ dẫn. Trên nền tảng có hook (Claude Code, Gemini CLI), một hook chạy trước các lệnh tìm kiếm để hướng agent về đồ thị; trên nền tảng dùng tệp chỉ dẫn (Codex, OpenCode, Cursor) thì có `AGENTS.md` hoặc `.cursor/rules/` [S1]. Máy chủ MCP trong `serve.py` mở 10 công cụ: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`, `list_prs`, `get_pr_impact`, `triage_prs` (người viết đếm) [S10]. Nhóm `prs` là phần thú vị: bảng điều khiển PR với trạng thái CI, review, và các PR dùng chung cộng đồng đồ thị (nguy cơ thứ tự gộp) [S1].

## Mã nguồn nằm ở đâu

| Thư mục | Nội dung | Nhãn |
|---|---|---|
| `graphify/` | Gói chính: 96 tệp `.py`, 90.797 dòng; 234 tệp được git theo dõi | Người viết đếm |
| `graphify/extractors/` | 37 tệp `.py`, mỗi ngôn ngữ hoặc định dạng một module (cobol, rust, terraform, sql, markdown…) | Người viết đếm |
| `tests/` | 595 tệp được theo dõi; 468 tệp `test_*.py`; 143.000 dòng Python; 7.155 hàm `test_` | Người viết đếm |
| `tools/skillgen/` | Phân mảnh nguồn của các tệp skill; `ARCHITECTURE`/`CONTRIBUTING` gọi đây là nguồn chính thức | Nguồn: repo [S6] |
| `worked/` | 5 ví dụ có sẵn đầu vào và đầu ra (httpx, mixed-corpus, karpathy-repos…) | Người viết đếm |

Ba tệp lớn nhất theo số dòng: `extract.py` 11.513, `cli.py` 5.480, `serve.py` 3.136 (người viết đếm). Tests nhiều hơn mã chạy khoảng 1,6 lần (143.000 so với 90.797 dòng) [người viết đếm]. Các tệp skill ở `graphify/` là **sinh ra**, không sửa tay; CI có job `skillgen-check` thất bại nếu ai sửa tay hoặc quên chạy bộ sinh [S6] [S9].

## Đo hiệu quả: các bộ benchmark

`BENCHMARKS.md` tự mô tả là chạy trên một harness mở: các hệ đối thủ (mem0, supermemory) chạy như adapter bên trong cùng một harness, cùng mô hình Kimi K2.6, cùng ngân sách, cùng người chấm [S3]. Bảng chính:

| Bộ | Chỉ số | Graphify | Đối chiếu | Nhãn |
|---|---|---|---|---|
| LOCOMO (n=300) | recall@10 | 0,497 | BM25 0,362; mem0 0,048; supermemory 0,149 | Nguồn: repo [S3] |
| LOCOMO (n=300) | Độ chính xác QA | 45,3% | supermemory 49,7%; BM25 31,3%; mem0 27,3% | Nguồn: repo [S3] |
| LongMemEval-S (n=50) | Độ chính xác QA | 76% | Ngang RAG vector dày 76% | Nguồn: repo [S3] |
| ERPNext cross-tool (n=6) | Độ phủ dữ kiện chính | 82,0% | Cơ sở grep/đọc 70,8% | Nguồn: repo [S3] |
| Chi phí nạp LOCOMO | USD | khoảng 1,40 | supermemory 15,67; mem0 3,48 | Nguồn: repo [S3] |
| Dựng đồ thị | Tín dụng LLM | 0 | | Nguồn: repo [S3] |

Người chấm là Kimi K2.6, được kiểm mù với một người chấm thứ hai: đồng thuận 90,6%, Cohen's kappa 0,81 [S3]. Một thí nghiệm theo thời gian dựng 689 điểm kiểm tra hằng tuần của ERPNext từ 2011 đến 2026; số nút tăng từ 3.069 lên 22.620 và cạnh từ 2.900 lên 48.710 [S3].

Con số "giảm token" riêng nằm ở `how-it-works.md`: trên một kho hỗn hợp 52 tệp, **71,5 lần** ít token mỗi truy vấn; trên 4 tệp là 5,4 lần; trên 6 tệp (httpx) chỉ khoảng 1 lần, và tài liệu tự nói "6 tệp đã nằm gọn trong cửa sổ ngữ cảnh" [S4].

## An toàn và quyền riêng tư

`SECURITY.md` mô tả Graphify là công cụ phát triển cục bộ, và ghi một bảng bề mặt tấn công kèm biện pháp [S5]:

| Vector | Biện pháp |
|---|---|
| SSRF khi tải URL | Chỉ http/https, chặn IP riêng/loopback/link-local và địa chỉ metadata đám mây, kiểm lại địa chỉ chuyển hướng [S5] |
| Tải quá lớn | Dừng ở 50 MB (`safe_fetch`) và 10 MB (`safe_fetch_text`) [S5] |
| Duyệt đường dẫn ở máy chủ MCP | `validate_graph_path()` bắt buộc đường dẫn nằm trong `graphify-out/` [S5] |
| Prompt injection từ tệp nguồn | Mỗi tệp được bọc trong khối `<untrusted_source path=... sha256=...>`, prompt dặn mô hình coi là dữ liệu [S5] |
| Lộ khoá trong đồ thị | `redact_secrets()` che chuỗi giống thông tin đăng nhập trước khi ghi `graph.json` [S5] |

Những điều nó nói là **không** làm: không mở cổng mạng mặc định (stdio; HTTP chỉ khi chọn và gắn `127.0.0.1`), không thực thi mã trong nguồn, không dùng `shell=True`, không lưu khoá API [S5]. CI chạy `bandit` và `pip-audit --strict` [S9]. Về riêng tư, README nói: mã xử lý cục bộ; video/âm thanh phiên âm cục bộ; tài liệu, PDF, ảnh gửi cho mô hình của trợ lý; không có telemetry; nhưng **mọi truy vấn được ghi** vào `~/.cache/graphify-queries.log` (thời gian, câu hỏi, số nút trả về), tắt bằng `GRAPHIFY_QUERY_LOG_DISABLE=1` [S1].

## Dự án được làm như thế nào

Nhịp phát hành rất dày: `CHANGELOG.md` có 240 mục phiên bản từ `0.1.0` (3/4/2026) đến `0.9.97` (27/10/2026); ba bản liên tiếp ra ngày 23, 25 và 27/10 (người viết đếm) [S7]. Bản 0.9.97 gồm cả hai thay đổi bảo mật (cưỡng chế che thông tin đăng nhập ở một điểm duy nhất trước cache, nâng sàn `anyio` lên 4.14.2 để tránh một lỗ hổng được ghi là CVSS 9.3) lẫn hàng chục sửa lỗi theo từng ngôn ngữ, nhiều dòng ghi công người đóng góp bên ngoài [S7].

CI có hai nhóm việc [S9]: `skillgen-check` (đảm bảo tệp sinh còn khớp phân mảnh nguồn, kiểm lược đồ `file_type`, vòng lặp khứ hồi với `v8`) và `test` chạy `pytest` trên Python 3.10, 3.12, 3.13, 3.14, cùng một job riêng cho bộ bảo vệ Pi dùng `bun`. `CONTRIBUTING.md` nêu 15 giá trị, trong đó đáng chú ý: sửa lỗi phải chứng minh được lỗi cũ bằng test hồi quy, PR nhỏ và dễ duyệt, không sửa tay tệp sinh, coi đường dẫn, văn bản nguồn, đầu ra mô hình và URL là không đáng tin [S6].

## Giấy phép, thương hiệu và sản phẩm trả tiền

Giấy phép là Apache-2.0; `NOTICE` ghi rằng các phần đóng góp trước khi chuyển giấy phép vẫn có thể dùng theo MIT, giữ nguyên trong `LICENSE-MIT` [S8]. README yêu cầu dự án phái sinh có chữ "graphify" trong tên phải ghi rõ là cộng đồng làm và không liên kết với Graphify Labs; tên và logo là nhãn hiệu [S1].

Mô hình thương mại hiện ngay ở đầu README: dòng đầu tiên sau huy hiệu là lời mời dùng thử Graphify Cloud 14 ngày, nhắc lại ở khung ghi chú, khung mẹo và cuối trang [S1]. Cloud được mô tả là lớp "luôn bật" trên Graphify: đồ thị sống xuyên nhiều repo, kiểm chứng hình thức, review code với cái nhìn tổng thể, và đầu nối với Sentry, Jira [S1]. Phần lõi chạy cục bộ miễn phí; không có điều khoản nào trong README ép phải dùng Cloud [S1].

## Phản biện

Phần này là nhận định của người viết, kiểm tra từng điểm với tệp nguồn. Chưa có vòng phản biện của team VPS (xem Lưu ý).

1. **"Giảm 80% token" không có bảng đo.** Cụm này xuất hiện ba lần trong README và đều gắn với Graphify Cloud (dòng đầu trang, khung mẹo, mục Cloud); tìm "80%" trong `BENCHMARKS.md` và `how-it-works.md` không thấy gì (người viết đếm) [S1] [S3] [S4]. Con số có đo là 71,5 lần trên 52 tệp, và chính tài liệu nói lợi ích biến mất ở kho nhỏ (khoảng 1 lần trên 6 tệp) [S4]. Đọc: lợi ích thật nhưng phụ thuộc quy mô, còn 80% là tuyên bố tiếp thị.
2. **Số đo nhỏ và do chính dự án chạy.** 6 câu hỏi cho ERPNext, 50 cho LongMemEval-S, 12 cạnh được kiểm tay trên FastAPI; đối thủ chạy như adapter trong harness của Graphify [S3]. LOCOMO QA thì supermemory cao hơn (49,7% so với 45,3%) và dự án có nói thẳng, kèm lưu ý recall của supermemory bị nhiễu do embedder khác [S3]. Đây là phép đo trung thực nhưng chưa phải đánh giá độc lập.
3. **Tài liệu tự mâu thuẫn.** README nói khoảng 40 ngôn ngữ, `how-it-works.md` nói 25 ngôn ngữ [S1] [S4]; `BENCHMARKS.md` ghi "Last updated: 2026-07-05" nhưng chứa phép kiểm ngày 2026-10-05 [S3]. `how-it-works.md` mô tả lượt 3 chạy bằng "Claude subagents" trong khi README nói dùng mô hình của trợ lý hoặc khoá API cấu hình [S4] [S1]. Đây là lệch tài liệu, không phải lỗi mã, nhưng làm người mới khó biết con số nào còn đúng.
4. **Dự án trước 1.0 đổi rất nhanh.** `SECURITY.md` chỉ hỗ trợ "Latest 0.9.x" [S5]; ba bản trong bốn ngày (23, 25, 27/10) và hàng chục sửa lỗi mỗi bản [S7]. Ghim phiên bản (`graphifyy==0.9.97`) và đọc changelog trước khi nâng.
5. **Cạnh `INFERRED` cần thận trọng ngoài mã sản xuất.** Dự án tự nêu bộ test có hàm trùng tên làm cạnh `calls` nhiễu hơn, nhãn đáng tin nhất ở lời gọi chéo tệp trong mã sản xuất [S3].
6. **Hook đặt chữ vào ngữ cảnh agent.** Bản 0.9.96 sửa lời nhắc của hook PreToolUse để viết như sự kiện thay vì mệnh lệnh, vì trước đó agent coi chúng là prompt injection và bỏ qua [S7]. Là chi tiết hay: công cụ ảnh hưởng agent qua văn bản, nên cần kiểm tra xem agent của bạn xử lý thế nào.
7. **Thứ tự ưu tiên khi vừa có CLI vừa có MCP.** README tự nói không có quy tắc ưu tiên chung; nếu dùng cả hai thì phải chọn một đường truy vấn chính và không dán hai khối chỉ dẫn vô điều kiện [S1].

## Điểm yếu và có nên dùng không

Nên thử nếu bạn làm việc với repo vừa và lớn (từ vài chục tệp trở lên) cùng một trợ lý lập trình, muốn hỏi quan hệ giữa các phần thay vì đọc tay, và chấp nhận một công cụ còn trước 1.0. Phần mã dựng cục bộ nên rủi ro riêng tư thấp [S1] [S5].

Cẩn thận nếu bạn cần: số đo độc lập (chưa có), hành vi ổn định giữa các bản (đang đổi hằng ngày), hay đồ thị luôn tươi xuyên nhiều repo (đó là chỗ Cloud bán) [S3] [S7] [S1]. Với kho rất nhỏ, tự tài liệu của dự án nói lợi ích gần như bằng không [S4]. Với tài liệu và PDF, hãy nhớ nội dung đi qua mô hình bạn cấu hình [S1].

## Cách học trong một buổi

1. **(15 phút) Đọc phần đầu README và bảng "Graphify làm được gì".** Tự trả lời: một câu hỏi nào của bạn mà grep không trả lời được?
2. **(20 phút) Đọc `ARCHITECTURE.md`.** Vẽ lại đường ống bảy bước, ghi đầu vào và đầu ra của từng bước.
3. **(15 phút) Đọc `docs/how-it-works.md` và bảng nhãn tin cậy.** Phân biệt `EXTRACTED`, `INFERRED`, `AMBIGUOUS` bằng ví dụ từ đoạn mã của bạn.
4. **(20 phút) Đọc `BENCHMARKS.md` có chủ đích phản biện.** Với mỗi bảng, ghi kích thước mẫu và ai chạy phép đo.
5. **(30 phút) Cài ghim phiên bản vào một repo nhỏ**, chạy `/graphify .`, xem `GRAPH_REPORT.md`, rồi tự kiểm ba cạnh `INFERRED` so với mã.
6. **(tuỳ chọn) Mở `worked/httpx/review.md`** để xem một kiểm định có sẵn của chính dự án.

## Điều cần nhớ

Một: Graphify dựng đồ thị tri thức từ mã bằng tree-sitter (tất định, miễn phí) và từ tài liệu bằng mô hình của bạn, rồi để agent truy vấn thay vì grep [S1] [S4]. Hai: giá trị khác biệt là nhãn tin cậy trên từng cạnh và luật đóng góp "đóng khi nghi ngờ" [S2] [S6]. Ba: số đo công khai thật nhưng nhỏ và tự đo; con số 80% không có bảng đỡ [S3] [S1]. Bốn: ghim phiên bản, tắt log truy vấn nếu cần, và nhớ gói tên `graphifyy` [S1] [S7].

## Lưu ý

Giới hạn nguồn: bài đọc bản sao nông (độ sâu 1) của repo `Graphify-Labs/graphify` tại commit `0a8cd4e1e342235fe53e881fb5d591bf0460071f` (27/10/2026), nhánh `v8`; vì nông nên không đếm được commit, tác giả hay tag. Mọi con số "người viết đếm" là lệnh `find`, `wc`, `grep` trên bản đó. Người viết **không cài và không chạy Graphify**: lệnh cài gói ngoài bị chặn trong phiên làm bài, nên chưa có "người viết chạy thử". Số sao lấy từ dữ liệu của GitHub Radar, không phải trang GitHub.

Về quy trình: yêu cầu là để team VPS phản biện nội dung trước khi dựng slide. Phiên này chạy trong container đám mây, không có lệnh `team`, không có `/srv/team` và không có đường SSH tới VPS, nên **vòng phản biện của team VPS chưa được thực hiện**; mục Phản biện ở trên là của người viết. Bản này cần được team VPS (hoặc người có quyền) duyệt trước khi coi là cuối cùng.

## Nguồn tham khảo

- [S1] Graphify Labs, README.md: giới thiệu, cài đặt, nền tảng, benchmark tóm tắt, quyền riêng tư, Cloud, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/README.md
- [S2] Graphify Labs, ARCHITECTURE.md: đường ống, trách nhiệm module, nhãn tin cậy, bảo mật, kiểm thử, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/ARCHITECTURE.md
- [S3] Graphify Labs, BENCHMARKS.md: harness, LOCOMO, LongMemEval-S, ERPNext, chi phí, kiểm cạnh INFERRED, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/BENCHMARKS.md
- [S4] Graphify Labs, docs/how-it-works.md: ba lượt xử lý, cộng đồng Leiden, nhãn tin cậy, benchmark token, cache, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/docs/how-it-works.md
- [S5] Graphify Labs, SECURITY.md: mô hình an toàn, bảng bề mặt tấn công, những điều không làm, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/SECURITY.md
- [S6] Graphify Labs, CONTRIBUTING.md và AGENTS.md: 15 giá trị đóng góp, tệp sinh và nguồn chính thức, quy tắc cho agent, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/CONTRIBUTING.md, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/AGENTS.md
- [S7] Graphify Labs, CHANGELOG.md: các bản 0.9.95 đến 0.9.97, sửa lỗi bảo mật và theo ngôn ngữ, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/CHANGELOG.md
- [S8] Graphify Labs, pyproject.toml, NOTICE, LICENSE-MIT: tên gói, phiên bản, phụ thuộc, giấy phép, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/pyproject.toml, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/NOTICE
- [S9] Graphify Labs, .github/workflows/ci.yml: skillgen-check, ma trận Python, bộ bảo vệ Pi, bandit, pip-audit, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/.github/workflows/ci.yml
- [S10] Graphify Labs, graphify/serve.py: máy chủ MCP, 10 công cụ và 6 tài nguyên, 2026, https://github.com/Graphify-Labs/graphify/blob/0a8cd4e1e342235fe53e881fb5d591bf0460071f/graphify/serve.py
- [S11] GitHub Radar, state/stars.json: số sao của Graphify-Labs/graphify ngày 17/10, 21/10, 24/10 và 28/10/2026 (không ghim được vào commit của repo được đọc), https://github.com/vohoailinh90/github-radar/blob/main/state/stars.json
