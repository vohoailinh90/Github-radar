---
id: R05
title: Archify: kỹ năng agent vẽ sơ đồ HTML có kiểm chứng
topic: ky-thuat
date: 2026-10-25
---
# Archify: kỹ năng agent vẽ sơ đồ HTML có kiểm chứng

## Tóm tắt

Archify là gì, có đáng tin để dùng không, và cần cẩn thận chỗ nào? Câu trả lời ngắn: đây là một **kỹ năng (skill) cho agent lập trình**, không phải thư viện để import và cũng không phải ứng dụng vẽ. Nó gồm một tệp hướng dẫn `SKILL.md` dành cho agent và một công cụ dòng lệnh Node.js không cần gói ngoài khi chạy; công cụ nhận một bản mô tả hệ thống dạng JSON có kiểu (typed JSON IR) và trả về **một tệp HTML đứng riêng** chứa sơ đồ tương tác được [S1] [S2] [S17]. Có mười loại sơ đồ (kiến trúc, quy trình, tuần tự, luồng dữ liệu, vòng đời, ERD, lớp, cây, dòng thời gian, thác thời gian) và từ bản 3.2.0 có thêm "trang trả lời một trang" (explainer) [S2] [S5].

Bài này đọc repo theo ba tầng. Tầng một là bản đồ: Archify làm gì, cài thế nào, một sơ đồ ra đời qua những bước nào, mã nguồn nằm ở đâu [S1] [S2] [S17]. Tầng hai là cơ chế làm nên khác biệt: để agent tự đặt tọa độ thay vì dùng bố cục tự động, kiểm tra cơ học trước khi giao, bằng chứng nguồn ghim theo commit, trình xem tương tác và trang trả lời một trang [S4] [S8] [S9] [S10]. Tầng ba là điều ít người đọc: các bộ đo chất lượng thật sự chứng minh được gì, mạng và quyền riêng tư, giấy phép vừa đổi từ MIT sang Apache-2.0 vào đúng ngày 25/10/2026, quảng cáo trong README, và những chỗ tài liệu lệch nhau [S11] [S13] [S14] [S1] [S17].

Mỗi khẳng định mang một trong năm nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ tệp của repo ở commit 51a2917 (25/10/2026). **Người viết đếm** là con số tính bằng script trên bản đã tải, bạn tự kiểm lại được. **Người viết chạy thử** là điều người viết tự chạy bằng chính công cụ của repo trong một thư mục cô lập. **Trang GitHub** là số liệu đọc từ trang công khai của repo, không ghim được vào commit. **Suy luận** là nhận xét của người viết, không phải lời của tác giả repo.

Ba ý đáng mang theo. Thứ nhất, Archify đặt cược vào việc **agent quyết định bố cục và ngữ nghĩa, công cụ chỉ kiểm tra và vẽ**: tác giả đã thử bố cục tự động rồi bỏ, vì thí nghiệm của chính họ cho kết quả kém [S4]. Thứ hai, "hợp lệ" là chuyện cơ học còn "đẹp và đúng" thì chưa: trong bộ đo duy nhất có kết quả, chỉ 8 trên 15 lượt agent tạo ra sơ đồ dùng được ngay [S11], và bộ đo trên repo thật thì chính README của nó ghi là chưa có kết quả nào [S12]. Thứ ba, trước khi đưa vào công việc có thu tiền hoặc môi trường nhạy cảm, hãy xem giấy phép của đúng bản bạn lấy, tắt kiểm tra cập nhật nếu cần, và hiểu rằng dự án đang đổi rất nhanh: 842 commit chỉ trong 25 ngày đầu tháng 10 (người viết đếm bằng `git log`).

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Agent skill (`archify/SKILL.md`) kèm CLI Node.js `archify/bin/archify.mjs` | Nguồn: repo [S2] [S17] |
| Người duy trì chính | tt-a1i; mã gốc kế thừa từ Cocoon-AI/architecture-diagram-generator | Nguồn: repo [S14] |
| Bản ổn định | 3.2.0, ngày 18/10/2026 | Nguồn: repo [S5] |
| Giấy phép | Apache-2.0 từ commit 25/10/2026; trước đó MIT, các bản đã phát hành giữ giấy phép cũ | Nguồn: repo [S14] [S1] |
| Chạy trên | Node.js 18 trở lên; thử trên Node 18, 20, 22, 24 trong CI | Nguồn: repo [S17] [S15] |
| Agent hỗ trợ | Claude Code, Codex CLI, Cursor, OpenCode; thêm GitHub Copilot trong trang chọn agent; Hermes và DeepSeek Harness là tích hợp cộng đồng | Nguồn: repo [S1] [S5] [S16] |
| Sao / fork | 88,9 nghìn sao, 6,0 nghìn fork, 224 người theo dõi, 117 issue mở, 118 pull request mở (đọc ngày 25/10/2026) | Trang GitHub [S18] |
| Lịch sử | 1.744 commit từ 15/4/2026, 551 commit gộp, 104 tên tác giả, 24 tag | Người viết đếm bằng `git log` |
| Quy mô | 1.180 tệp được theo dõi; khoảng 52 nghìn dòng mã chạy và công cụ trong `archify/`, 84 nghìn dòng mã kiểm thử | Người viết đếm |
| Ngôn ngữ README | Anh, Trung giản thể, Nhật, Hàn | Nguồn: repo [S1] |

## Repo này là gì

**Mục tiêu (nguồn: repo).** README tự giới thiệu bằng một câu: biến bất cứ thứ gì bạn muốn hiểu, lập kế hoạch hay chia sẻ thành một hình ảnh tương tác. Người dùng mô tả ý tưởng cho agent, Archify dựng thành HTML để khám phá, tùy biến và gửi đi; ví dụ trải từ lịch trình du lịch và bản đồ học tập đến hệ thống phức tạp [S1]. PRODUCT.md nói rõ hơn: đối tượng cốt lõi là kỹ sư, kiến trúc sư, trưởng nhóm kỹ thuật, người rà soát và chính các agent lập trình khi giải thích một codebase hay một luồng yêu cầu; đối tượng mở rộng là người ngoài ngành cần vẽ kế hoạch nghỉ phép, quy trình duyệt hồ sơ, đường đi của tiền hay giấy tờ [S3].

**Cái nó không làm (nguồn: repo).** Có hai lớp. Lớp thứ nhất là tuyên bố ngay trong README: không phải trình vẽ đa dụng, không phải một theme cho Mermaid, và ngoài phạm vi hiện tại là phân tích cú pháp Mermaid tự động, bố cục tự động đa dụng, chia sẻ lưu trữ trên máy chủ và trình soạn WYSIWYG [S1]. Lớp thứ hai là danh sách "Not planned" trong ROADMAP, ghi lý do từng mục bị từ chối: tham số `?exportScale=N`, bảng màu cho người mù màu, liên kết chia sẻ nén gzip+base64 (vì nguy cơ XSS), dagre/elk-js, YAML làm định dạng trung gian, trình phân tích Mermaid, trình soạn chú thích, giao diện so sánh sơ đồ, nút xuất PDF và giao diện di động riêng [S4]. Việc ghi sẵn "đã cân nhắc và từ chối" giúp người đề xuất tìm lại bối cảnh quyết định (suy luận).

**Tính cách và nguyên tắc thiết kế (nguồn: repo).** PRODUCT.md mô tả giọng điệu "chính xác, điềm tĩnh, sống động" và liệt kê những thứ bị coi là phản mẫu: công cụ làm đẹp Mermaid chỉ đổi theme, bộ vẽ WYSIWYG, demo đồ thị thiên về chuyển động ngụ ý quan hệ không có trong nguồn, giao diện bảng điều khiển dày đặc và các biểu tượng thương hiệu được đoán theo tên sản phẩm [S3]. Sáu nguyên tắc đáng nhớ: sự thật đứng trước màn trình diễn; một câu chuyện không gian đọc trước; tiết lộ dần thay vì thêm khung điều khiển; chuyển động chỉ có một "chủ" và hữu hạn; kết quả mang theo được và không cần máy chủ; nhận diện thương hiệu không làm lệch ngữ nghĩa [S3]. DESIGN.md cụ thể hóa thành một hệ màu ngữ nghĩa cố định (bảy tín hiệu: frontend, backend, database, cloud, security, messagebus, external) và một họ phông đơn là JetBrains Mono [S3].

## Bắt đầu nhanh

**Cài (nguồn: repo).** Lệnh duy nhất README đưa ra cho đa số người dùng: `npx skills add tt-a1i/archify -g`. Sau đó bạn nói với agent bằng ngôn ngữ thường, ví dụ mô tả một yêu cầu web đi qua Redis rồi PostgreSQL, rồi tiếp tục "thêm xác thực", "làm nổi đường cache miss" hay "chuyển sang giao diện sáng" [S1]. Không cần có repo: có thể bắt đầu từ một đoạn mô tả, hoặc nhờ agent đọc một repo để vẽ kiến trúc có dẫn chứng nguồn [S1].

**Các bề mặt cài đặt (nguồn: repo).** Claude Code đặt tại `~/.claude/skills/` hoặc `.claude/skills/`; Codex CLI tại `~/.agents/skills/`; OpenCode tại `~/.config/opencode/skills/`; Claude.ai nhận tệp `archify.zip` qua Settings, Capabilities, Skills (phụ thuộc việc sandbox có Node.js); Project Knowledge nhận cùng tệp ở chế độ dự phòng chỉ dựa vào prompt; Hermes Agent và DeepSeek Harness là hai tích hợp cộng đồng [S1]. Một lệnh cài tường minh cho Cursor cũng được ghi sẵn trong README [S1].

**Lệnh nên biết (nguồn: repo).** Các lệnh dưới đây chạy từ thư mục `archify`; README ghi nguyên văn [S1]:

```bash
cd archify
node bin/archify.mjs doctor
node bin/archify.mjs demo /tmp/archify-demo
node bin/archify.mjs guide "Show CI/CD checks, approval, deploy, and rollback"
node bin/archify.mjs validate workflow examples/agent-tool-call.workflow.json --quality showcase --json
```

CLI có mười bảy lệnh con: `render`, `compare`, `deliver`, `patch`, `finalize`, `preview`, `validate`, `migrate`, `inspect`, `check`, `visual-check`, `browser-check`, `guide`, `brands`, `examples`, `doctor`, `demo`, cộng `help` (người viết đếm các nhánh `case` trong `bin/archify.mjs`) [S17]. Agent chỉ cần thuộc `finalize`: SKILL.md bảo agent chạy đúng một lệnh này cho mỗi bản nháp rồi đọc biên nhận [S2].

## Một sơ đồ ra đời như thế nào

Luồng chuẩn trong SKILL.md và README gồm năm bước: sinh JSON, kiểm tra, xem thử (tùy chọn), giao và lặp [S1] [S2]. Hình dưới là bản tóm tắt của người viết (suy luận từ hai tài liệu trên):

```text
Mô tả / mã nguồn / Mermaid
        │  agent đọc nguồn, chọn loại sơ đồ, tự đặt tọa độ
        ▼
candidate.json  (typed JSON IR, schema_version, additionalProperties: false)
        │  finalize  = chạy liên tiếp bốn cổng, dừng ở cổng đầu tiên không đạt
        ▼
 [1] validate       schema + bố cục + định tuyến + khoảng cách nhãn
 [2] deliver        dựng HTML trong cùng thư mục, thay tệp cũ bằng thao tác nguyên tử
 [3] check          kiểm tra nghiêm ngặt chính tệp HTML vừa giao
 [4] browser-check  mở bằng Chrome thật, đo tràn khung và cỡ chữ
        │ đạt
        ▼
 <tên>.html  +  <tên>.delivery.json  (biên nhận)
        │ không đạt: stdout/biên nhận nêu mã lỗi, đối tượng, số đo, cách sửa được hỗ trợ
        ▼
agent sửa đúng vùng lân cận rồi chạy lại (hai vòng sửa tập trung cho cùng một lỗi)
```

**Chi tiết từng cổng (nguồn: repo).** Biên nhận `validate --json` và `deliver --json` trả về mã quy tắc ổn định, đối tượng bị lỗi, số đo và chỉ những cách sửa được hỗ trợ (`supportedFixes`), thay cho dấu vết Node hay lời đoán [S1]. `finalize` báo bốn cổng riêng biệt (validate, deliver, check, browser-check) và dừng ở cổng đầu tiên không đạt; "một biên nhận chỉ có bốn kiểm tra tệp là kiểm tra cơ bản, chưa phải nghiệm thu showcase, cần đủ chín kiểm tra, không lỗi bố cục và không cảnh báo" [S8]. Chế độ chất lượng `showcase` là mặc định cho bản mới; `standard` giữ cho ERD dày đặc ở lượt đầu [S2] [S8].

**Giao hàng nguyên tử (nguồn: repo).** Tệp đích chỉ bị thay khi bản mới đã qua mọi cổng, nên một lần lưu dở hay một bản hỏng không làm mất bản tốt gần nhất. Mỗi tệp giao có hai tệp phụ: `<tên>.delivery.json` ghi lần thử hoàn tất gần nhất và `<tên>.delivery-pending.json` là nhật ký phục hồi của lần đang chạy; một khóa cấp thư mục `.archify-delivery-lock.json` làm các lần giao vào cùng thư mục vật lý chạy tuần tự, kể cả khi tên khác nhau do hoa thường, chuẩn hóa Unicode, tên ngắn Windows hay liên kết mềm [S8]. Chi phí được tài liệu thừa nhận: các lần giao khác tên vào cùng thư mục cũng phải xếp hàng [S8].

**Nhập từ Mermaid (nguồn: repo).** Archify không phân tích cú pháp Mermaid. SKILL.md bảo agent đọc Mermaid để lấy cấu trúc và ý nghĩa rồi viết JSON mới từ đầu: `flowchart` thành quy trình hoặc kiến trúc, `sequenceDiagram` thành tuần tự, `stateDiagram` thành vòng đời, `erDiagram` thành ERD, `classDiagram` thành lớp [S2].

## Mười loại sơ đồ và trang trả lời một trang

| Loại | Dùng để | Mảng cấu trúc chính trong JSON | Nguồn |
|---|---|---|---|
| `architecture` | Thành phần, dịch vụ, kho lưu trữ, ranh giới | `components`, `boundaries`, `connections` | [S2] [S7] |
| `workflow` | CI/CD, cổng duyệt, gọi công cụ, runbook | `lanes`, `phases`, `groups`, `mainPath`, `nodes`, `edges` | [S2] [S7] |
| `sequence` | Chuỗi gọi API, bất đồng bộ, trả về | `participants`, `segments`, `messages`, `activations` | [S2] [S7] |
| `dataflow` | Pipeline, ETL, truy vết dữ liệu, PII | `stages`, `nodes`, `flows` | [S2] [S7] |
| `lifecycle` | Trạng thái, thử lại, trạng thái kết thúc | `mainPath`, `states`, `transitions` | [S2] [S7] |
| `erd` | Bảng, cột, khóa, bản số quan hệ | `entities`, `relationships` | [S2] [S7] |
| `class` | Lớp, giao diện, thành viên chọn lọc, quan hệ kiểu | `types`, `relationships` | [S2] [S7] |
| `tree` | Phân cấp một cha: cây thư mục, phân rã năng lực | `nodes` (mỗi nút một `parent`) | [S2] [S7] |
| `timeline` | Sự kiện theo mốc thời gian, làn theo nguồn | `events` | [S2] [S7] |
| `waterfall` | Thời gian đi đâu trong một yêu cầu hay lượt chạy agent | `spans` (mỗi span có thể có `parent`) | [S2] [S7] |

**Ghi chú theo bản (nguồn: repo).** ERD, lớp, cây, dòng thời gian và thác thời gian là năm loại thêm ở bản 3.1.0 (14/10/2026), nâng tổng từ năm lên mười [S5]. Dòng thời gian và thác thời gian dùng dữ liệu minh họa trong ví dụ; README dặn chỉ coi mốc giờ hay thời lượng là thật khi chúng đến từ log hoặc trace [S1]. Kiểu `architecture` có hồ sơ `deployment-ownership` tùy chọn: nó từ chối (fail closed) nếu thiếu chủ sở hữu, vùng đặt, phạm vi cơ sở dữ liệu riêng hay các giao điểm có tên, và không kiểm tra hạ tầng thật [S1].

**Hợp đồng schema (nguồn: repo).** Mọi schema đòi `schema_version`, `diagram_type`, `meta` (có `title` và `output` di động) cùng các mảng cấu trúc của loại đó, đặt `additionalProperties: false` ở mọi cấp nên trường lạ bị từ chối chứ không bị lờ đi [S7]. `meta` còn nhận `locale` (mẫu `^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$`), `translations`, bốn bộ giao diện `classic`, `signal-flow`, `blueprint`, `editorial` (chỉ đổi kiểu trình bày, không đổi ID hay hình học) và `legend` [S7]. Sáu ngôn ngữ giao diện có sẵn: `en`, `zh-CN`, `zh-TW`, `es`, `ko`, `ar`; ngôn ngữ khác phải cấp `meta.translations` hoặc rơi về tiếng Anh và có công bố [S1] [S7].

**So sánh Before/After (nguồn: repo).** Lệnh `compare architecture base.json head.json out.html --json` dựng "Architecture Delta": đặt hai ảnh chụp đã kiểm chứng cạnh nhau với biên nhận máy đọc được, phân loại thành phần thêm, bỏ, đổi, di chuyển, và README nhấn mạnh nó không suy ra tác động, rủi ro hay độ an toàn khi gộp [S1].

## Mã nguồn nằm ở đâu

| Thư mục | Nội dung | Số tệp theo dõi |
|---|---|---|
| `archify/` | Gói kỹ năng: `SKILL.md`, `bin/`, `renderers/`, `schemas/`, `explainer/`, `references/`, `locales/`, `examples/` | 206 |
| `viewer/` | Mã nguồn trình xem (JS/CSS); `archify/assets/template.html` được sinh ra từ đây | 18 |
| `test/` | Bộ kiểm thử Node (`*.test.mjs`) cùng dữ liệu golden | 314 |
| `docs/` | Thư viện mẫu (Proof Lab), các ca thật, bằng chứng đọc, thiết kế | 203 |
| `website/` | Trang web Astro + React + TypeScript, xuất tĩnh lên GitHub Pages | 108 |
| `experiments/`, `journal/` | Thí nghiệm và 62 ghi chép nghiên cứu (48 vòng "visual evolution") | 77, 62 |
| `benchmarks/` | Ba bộ đo: ordinary-model-floor, repair-rounds, real-repo-generation | 27 |
| `integrations/` | DeepSeek Harness (24), Hermes Agent (5) | 29 |
| `community/`, `tools/`, `scripts/`, `.agents/`, `.github/` | Danh mục gói cộng đồng, thẻ người đóng góp, công cụ build/CI, kỹ năng rà soát nội bộ, workflow | 4, 17, 28, 24, 11 |

Số tệp theo `git ls-files`, người viết đếm. Gói kỹ năng chạy với **số phụ thuộc ngoài bằng không**: các lệnh `import` trong `archify/` chỉ trỏ vào module có sẵn của Node, ngoại lệ duy nhất là hai script sinh mã lúc phát triển (`generate-validators.mjs` dùng `ajv`, `generate-brand-marks.mjs` dùng `simple-icons`); trình kiểm tra schema và dữ liệu biểu tượng được sinh sẵn và commit kèm [S17] [S4] (người viết đếm các câu import; xác nhận qua việc `doctor` và `finalize` chạy được trên bản sao chưa cài gói nào).

**Quy mô mã (người viết đếm, dòng của .mjs/.js/.css/.astro/.ts, không tính thư mục vendor).** CLI `bin/` 12.373 dòng trong 7 tệp, riêng `bin/archify.mjs` đã 7.289 dòng; `renderers/` 30.189 dòng trong 49 tệp, trong đó phần dùng chung 12.680 dòng (28 tệp), quy trình 6.222, kiến trúc 2.737, luồng dữ liệu 1.874, ERD 1.738, vòng đời 1.134, tuần tự 1.105, lớp 1.095, dòng thời gian 576, cây 573, thác thời gian 413; `explainer/` 3.817; `delta/` 1.318; mã nguồn `viewer/` 15.061; `test/` 84.260 dòng trong 246 tệp. Cộng `bin`, `renderers`, `explainer`, `delta`, `scripts`, `recipes`, `migrations` trong `archify/` được khoảng 52 nghìn dòng, vậy mã kiểm thử nhiều hơn mã chạy khoảng 1,6 lần (suy luận; có lẫn vài nghìn dòng tệp sinh tự động như dữ liệu biểu tượng). Một tệp CLI bảy nghìn dòng là điểm cần lưu ý nếu bạn định đọc hoặc sửa nó (suy luận).

## Triết lý: để agent đặt tọa độ

Đây là quyết định cốt lõi, và ROADMAP trình bày nó kèm bằng chứng của chính dự án.

**Tại sao không dùng bố cục tự động (nguồn: repo).** Ba lần rà soát độc lập đều chỉ ra bố cục tự động (dagre, elk-js) là rủi ro chính cho nét riêng của Archify: ba mươi phần trăm quãng đường từ "Mermaid thường" đến "Archify đặt tay" mới đạt được bằng cách bọc CSS lên kết quả dagre. Luận điểm là thẩm mỹ chính là các quyết định bố cục (nhà cung cấp xác thực nằm ngoài vùng AWS, S3 nằm dưới CloudFront để ngụ ý quan hệ phục vụ, ranh giới nhóm bảo mật đúng lề 30/50) nên loại bỏ người hay agent khỏi việc bố cục là loại bỏ chính điểm khác biệt [S4]. Việc agent giữ vai trò đặt tọa độ được diễn đạt trong tài liệu hướng dẫn: "bộ định tuyến không thể sắp xếp lại các ô, nên vị trí đặt quyết định đường nối có thẳng hay không" [S9].

**Thí nghiệm kiểm chứng (nguồn: repo).** Ngày 16/4/2026 dự án dựng năm sơ đồ Mermaid thật ở ba phiên bản (A Mermaid thường, B dagre cộng CSS Archify, C Archify đặt tay), xáo thứ tự và để chủ dự án chấm mù. Kết quả ghi trong ROADMAP: C được chấm đẹp; A và B cùng không đẹp, B không tốt hơn A đáng kể; cả hai tiêu chí đạt đều trượt. Hệ quả: các giai đoạn P1 (trình phân tích flowchart Mermaid), P3 (đường ống trọn vẹn) và P4 (xuất ngược sang Mermaid, nhập C4) bị hủy [S4]. Hai cảnh báo dành cho người đọc: thí nghiệm chỉ có một người chấm, và ngày 1/9/2026 hai trong năm đầu vào bị gỡ vì repo nguồn không có giấy phép phân phối lại kiểm chứng được, nên ROADMAP tự ghi rằng lần chạy năm đầu vào không còn tái hiện đầy đủ từ HEAD [S4]. Theo người viết, đây là một lý do để coi kết luận như một quan điểm thiết kế có dữ liệu minh họa, không phải kết quả thống kê (suy luận).

**JSON thay vì YAML (nguồn: repo).** YAML do mô hình sinh ra hay "trông đúng nhưng phân tích sai" vì nhạy với khoảng trắng và các cú pháp `pos: [40, 80]`; JSON phân tích không nhập nhằng, có `JSON.parse` sẵn trong trình duyệt, có JSON Schema trưởng thành và đủ dễ đọc trong `git diff` [S4].

**Các mặc định bố cục cho kiến trúc (nguồn: repo).** Tài liệu chỉ cho agent phân loại từng quan hệ trước khi đặt: đường chính, nhánh hoặc kho lưu trữ (đặt ngay trên hoặc dưới nút sở hữu, căn giữa để cạnh là một đoạn thẳng), đường trả về (nguồn nằm phía không có nhánh), lối vào thứ hai, và tỏa nhánh (một cạnh có k quan hệ cần ít nhất `32 + 14 × (k − 1)` px; bốn quan hệ cần 74 px). Nhãn giữa hai ô cạnh nhau cần khoảng trống `6,5 px × số đơn vị ASCII + 21 px`; khung kiến trúc nên ≤ 1240 px rộng, hoặc 1790 px khi rộng gấp 1,55 lần cao trở lên; sau đó chữ nhãn rơi xuống dưới ngưỡng đọc được trên máy tính [S9]. Không có hạn ngạch số nút hay số cạnh [S2].

## Kiểm chứng trước khi giao

**Chín kiểm tra tệp (người viết chạy thử).** Với ví dụ `web-app.architecture.json` đi kèm, `validate --quality showcase --json` trả `ok: true` và đủ chín kiểm tra: `single_svg`, `finite_svg`, `orthogonal_arrows`, `label_route_clearance`, `relationship_crossings`, `relationship_corridors`, `container_border_runs`, `route_rhythm`, `legend_clearance`.

**Lỗi cố ý (người viết chạy thử).** Người viết sửa một cạnh trỏ tới nút không tồn tại (`ghost-node`). Lệnh thoát với mã 1, biên nhận nêu `architecture/unknown-endpoint` kèm `subject.path` là `/connections/0/to`, danh sách các ID nút có thật và ba cách sửa dạng "đặt `/connections/0/to` thành ID đã kiểm chứng `api`" (và `auth`, `cache`). Biên nhận còn một chẩn đoán thứ hai, `layout/constraint`, với `supportedFixes` rỗng, nghĩa là không phải mọi chẩn đoán đều có cách sửa kèm. Đây đúng là hình dạng "repair receipt" mà README tuyên bố [S1].

**Bốn cổng với Chrome thật (người viết chạy thử).** `finalize architecture` trên cùng ví dụ, có `ARCHIFY_CHROME` trỏ vào Chromium cài sẵn, báo `validate`, `deliver`, `check`, `browser-check` đều `pass` sau 6,56 giây, và `visualReview` là `not-requested`. Cùng biên nhận kèm khuyến nghị `inspect-route-readability` với tín hiệu `routesOverSuggestedBends: 1` và lý do "các cổng tự động đã đạt, nhưng giao điểm hoặc đường vòng vẫn cần xem bằng mắt trước khi tuyên bố chất lượng thị giác". Nói cách khác, ngay trên ví dụ do tác giả làm, công cụ tự nói rằng cổng tự động không thay được việc nhìn [S2] [S8].

**Điều tệp HTML đầu ra có và không có (người viết đếm trên bản `deliver`).** Một sơ đồ kiến trúc 10 nút ra tệp 845.929 byte, gồm 4 thẻ `<script>` (khối lớn nhất khoảng 451 nghìn ký tự, nhiều khả năng là trình xem) và 3 khối `<style>`; không có thẻ `<link rel="stylesheet">`, không có lời gọi `fetch(`, `XMLHttpRequest`, `WebSocket` hay `sendBeacon`; chỉ có một thuộc tính `href` ngoài, trỏ về GitHub của dự án. Các chuỗi `http(s)://` khác trong tệp nằm trong văn bản giấy phép nhúng sẵn và khai báo namespace SVG. Mã tham chiếu `localStorage` 11 lần; người viết chưa kiểm xem nó lưu gì (có thể là tùy chọn của người xem, suy luận). Điều này khớp với tuyên bố "một tệp HTML đứng riêng, không cần Archify để mở" [S1].

**Hai nhãn dễ bị hiểu nhầm (nguồn: repo).** SKILL.md dặn agent phân biệt "kiểm tra tệp", "bằng chứng trình duyệt", "ảnh chụp" và "đánh giá bằng mắt thật", và chỉ nói đã xem khi thật sự xem; câu trả lời cho "đã kiểm chưa" nên là "Các kiểm tra tự động đạt; chưa xem bằng mắt" [S2].

## Bằng chứng nguồn: sơ đồ trỏ về dòng mã

Đây là tính năng đáng giá nhất cho ai dùng Archify để hiểu một repo.

**Quy trình đọc mã (nguồn: repo).** Tài liệu "Repository authoring" bắt agent đóng băng danh tính repo (`git rev-parse HEAD`, URL gốc đã gỡ thông tin đăng nhập, trạng thái làm việc), vạch một lát cắt nhỏ từ điểm vào, theo dõi quyền sở hữu qua vị trí gọi thật của hành động, ghi dòng bằng chứng ngay khi đọc, và ghi lại điều chưa biết cạnh khẳng định bị ảnh hưởng thay vì biến nhãn hay mô tả gói thành sự thật. Một hàm xuất ra nhưng không được đường chính gọi chỉ là "khả năng tùy chọn", không phải cạnh bắt buộc; "một lời gọi phía trên không chứng minh điều kiện cho phép" thay đổi trạng thái [S9].

**Cách công cụ xác minh (nguồn: repo).** Mã đọc đối tượng git đã ghim bằng `git --no-replace-objects ... cat-file`, đặt `GIT_NO_LAZY_FETCH=1` và `GIT_ALLOW_PROTOCOL` rỗng (không cần đường truyền nào cho thao tác đọc cục bộ), giới hạn mỗi nguồn ở 16 MiB, và kiểm: thư mục gốc Git, nguồn gốc khớp, commit, blob, đường dẫn không thoát khỏi repo, số dòng trong biên [S13] [S5]. Bằng chứng được đọc từ **byte đã commit** ở bản ghim, không phải bản sửa chưa commit; chế độ `link_mode: "local-only"` giữ ghim nhưng bỏ liên kết web cho nguồn SSH hay nền tảng chưa hỗ trợ [S9]. Liên kết web hỗ trợ GitHub, Gitee, gitlab.com và máy chủ GitLab tự quản khai báo `provider: "gitlab"` [S5] [S9].

**Giới hạn (suy luận).** Cơ chế chứng minh rằng trích dẫn khớp với tệp và dòng ở commit đã ghim, nhưng không chứng minh rằng agent hiểu đúng đoạn mã đó: tài liệu tự viết "mỗi tham chiếu chỉ chứng minh sự thật nhìn thấy ở vị trí đó" [S9]. Đúng-đủ vẫn phụ thuộc người đọc kiểm lại những cạnh quan trọng.

## Trình xem: đọc, tìm, lần vết, chia sẻ

**Phím tắt và hành động (nguồn: repo).** Bảng trong README: `?` mở hướng dẫn sơ đồ; `/` tìm và tập trung một nút; chọn nút rồi bấm `Upstream` hoặc `Downstream` để lần các quan hệ đã khai báo; `R` hoặc `PATH` dò đường có hướng; `L` hoặc `LENS` so sánh một hay hai vai ngữ nghĩa; `M` hoặc `MAP` mở radar tổng quan; `F` vào chế độ trình chiếu; `S` đổi kiểu, `T` đổi sáng/tối, `E` mở xuất; `+`, `-`, `0` thu phóng [S1]. Các liên kết ổn định khôi phục `#focus=<id>`, `#focus=<id>&reach=upstream|downstream`, `#relation=<id>`, `#route=<nguồn>~<đích>` và `#lens=<loại>~<loại>`; chuyển động tôn trọng `prefers-reduced-motion` và không bao giờ có trong bản xuất chuẩn [S1].

**Nguyên tắc "trung thực về tương tác" (nguồn: repo).** Tiêu điểm, phạm vi thượng/hạ nguồn, tuyến đường, so sánh vai trò và câu chuyện đều dùng lại các nút và quan hệ do tác giả khai báo, không bịa topo và không tuyên bố tác động lúc chạy; thẻ chia sẻ Route/Reach nêu rõ phạm vi của mình thay vì giả làm bản chuẩn [S1] [S3].

**Xuất bản (nguồn: repo).** Menu Export sao chép PNG vào clipboard và tải các định dạng tĩnh hoặc chuyển động; Route Share Card xuất đường đi đã vạch thành PNG 1200×630 giữ toàn sơ đồ làm ngữ cảnh; Reach Share Card chụp đúng phạm vi thượng/hạ nguồn; trang trả lời xuất ảnh dài PNG, WebP hoặc JPG hay in ra PDF [S1] [S5]. Việc kiểm tra giải mã WebM nằm trong CI: nó giải mã một tệp xuất chuyển động thật và từ chối các khung tĩnh [S15].

**Phạm vi thiết bị (nguồn: repo).** Máy tính là bề mặt chính; màn hình hẹp chỉ được "chứa an toàn" và không có sản phẩm di động riêng; khả năng truy cập gồm điều hướng bàn phím, tiêu điểm nhìn thấy, nhãn ngữ nghĩa, giao diện sáng/tối, tín hiệu không chỉ bằng màu và độ tương phản đọc được [S3] [S4].

## Trang trả lời một trang (explainer)

**Là gì (nguồn: repo).** Khi bạn yêu cầu "trả lời bằng một trang", Archify dựng một trang có kết luận ở đầu, rồi mỗi bảng (panel) trả lời một câu hỏi bằng văn xuôi, bảng so sánh, các bước, danh sách kiểm, biểu đồ, mã và sơ đồ bản địa đã kiểm; trích dẫn đánh số, các đoạn mã của repo được ghim theo commit và mở thành thẻ nguồn; có bốn kiểu trình bày (clean, editorial, product, Swiss) với giao diện sáng và tối [S1] [S5]. Tính năng này vào bản 3.2.0 qua pull request #993 và có bốn trang ví dụ trong `docs/cases/explainer/` [S5].

**Ngôn ngữ bản nháp (nguồn: repo).** Bản nháp là một tệp Markdown `candidate.archify.md`: đoạn đầu sau tiêu đề là kết luận, một danh sách phẳng ngay sau đó đưa tối đa bốn lý do, mỗi tiêu đề `##` mở một panel. Các chỉ thị như `@answer`, `@meta`, `@source`, `@sequence`, `@steps`, `@workflow`, `@architecture`, `@tree`, `@timeline`, `@erd` là các dòng dạng bảng; ID duy nhất trong cả tài liệu; HTML thô và danh sách lồng nhau bị từ chối kèm chẩn đoán ghi rõ dòng và ví dụ sửa [S10]. Lệnh `finalize explainer` kiểm tra, giao nguyên tử và kiểm tra trang; `patch explainer` thay đúng một panel theo ID [S2] [S5].

**Chạy thử (người viết chạy thử).** Người viết trích đúng ví dụ TLS trong tài liệu (hai panel, một sơ đồ tuần tự, một danh sách bước, một bảng so sánh) và chạy `finalize explainer`: kết quả `ok`, ba cổng validate, deliver, check đạt, cổng `browser-check` ghi `not-run`, tổng 1,33 giây, ra tệp 505.526 byte. Nghĩa là với trang trả lời, cổng trình duyệt không chạy trong lần gọi mặc định này; việc `explainer/browser-check.mjs` tồn tại gợi ý có đường chạy riêng, nhưng người viết chưa thử.

**Khi nào nên dùng (nguồn: repo).** SKILL.md chỉ cho dùng trang khi người dùng xin "một trang" hoặc khi dòng quy tắc `[archify explainer: proactive]` hay `always-on` được bật trong tệp quy tắc toàn cục của agent; không có yêu cầu thì trả lời bằng văn bản hoặc vẽ sơ đồ đã xin. Sau một trang tạo theo yêu cầu, agent được dặn cuối câu trả lời hỏi một lần có muốn bật chế độ chủ động không, và chỉ ghi vào tệp toàn cục khi người dùng đồng ý [S2]. Bạn nên biết cơ chế này vì nó là một cách kỹ năng ảnh hưởng đến hành vi mặc định của agent (suy luận).

## Đo chất lượng: ba bộ benchmark

Đây là phần dễ bị bỏ qua nhưng cho biết rõ nhất các tuyên bố chất lượng dựa vào đâu.

**Ordinary-Model-Floor v1 (nguồn: repo).** Câu hỏi: một agent lập trình "bình thường" có tạo được sơ đồ dùng được ngay ở lần thử đầu, không cần người sửa JSON không? Một lượt đạt `firstPassUsable` chỉ khi qua ba cổng: ngữ nghĩa đúng và nối đúng; CLI thật đạt `validate --quality showcase --json`; một người rà soát có danh tính xem sản phẩm đã dựng, ghi `passed` và không báo lỗi. README ghi rõ đây là cổng giao hàng, không phải bảng xếp hạng mô hình, và "một lượt thiếu đánh giá thị giác không bao giờ được nâng thành đạt" [S11].

**Kết quả đã ghi (nguồn: repo).** Bản ghi `2026-07-26-pi-three-models-quality-first.json` có 15 lượt: tác nhân `pi`, ba mô hình, năm tác vụ (kiến trúc, quy trình, tuần tự, luồng dữ liệu, vòng đời). Tổng 8 trên 15 lượt dùng được ngay (53,3%). Theo mô hình: minimax-m3 3/5, qwen3.7-plus 3/5, deepseek-v4-flash 2/5. Theo tác vụ: tuần tự 3/3, kiến trúc 3/3, vòng đời 1/3, quy trình 1/3, luồng dữ liệu 0/3. Cụm lỗi harness đếm: ngữ nghĩa 2, kiểm tra 5, đánh giá thị giác 7; tổng 14 lớn hơn 7 lượt hỏng vì mỗi cổng không đạt đều tính một lần (người viết đọc `benchmark.mjs`). Kết luận chính của bản ghi: **không đo được mức cải thiện tổng thể** giữa ba cấu hình (cơ sở, sau sửa, ưu tiên chất lượng đều đạt 8/15), trong đó vòng đời và kiến trúc tốt lên còn quy trình và luồng dữ liệu kém đi trên mẫu này [S11].

**Điều bộ này chưa nói (suy luận).** Mẫu nhỏ (15 lượt, một tác nhân là `pi`, ba mô hình minimax-m3, qwen3.7-plus và deepseek-v4-flash), bản ghi không có lượt nào của mô hình Claude hay GPT, và không có chạy lặp để ước lượng độ biến thiên. Con số 53% là mức sàn của "agent thường" trong một ma trận, không phải xác suất bạn nhận sơ đồ tốt từ agent của bạn. Cũng cần nhớ "dùng được ngay" ở đây tính cho cả lượt gọi agent, trong đó agent được phép tự chạy CLI để sửa, nên đây không phải tỉ lệ đúng ở bản nháp đầu [S11]. Về vòng sửa: tài liệu giới hạn hai vòng sửa tập trung cho cùng một lỗi trước khi phải xem số đo hình học và báo khoảng trống cụ thể [S1] [S8].

**Repair Rounds v1 (nguồn: repo).** Đo hiệu quả của biên nhận: bao nhiêu vòng để chạm đạt, tỉ lệ khuyết điểm lộ ra ở vòng một, cổng nào phát hiện đầu tiên, tỉ lệ phát hiện muộn ở `check` hay `browser-check`, mức "có thể sửa theo biên nhận" và chi phí token ước lượng bằng bộ đếm từ vựng cố định. Có tám lớp lỗi tiêm tự động (`meta-missing-output`, `node-invalid-type`, `node-long-label`, `node-duplicate-id`, `edge-dangling-target`, `viewbox-oversized`, `title-overflow`, `subtitle-overflow`). README tự nhận đây là "kiểm tra hồi quy chẩn đoán tổng hợp", người sửa là bộ luật chứ không phải agent thật, nên không dùng để kết luận về chất lượng soạn thảo hay tốc độ đầu-cuối [S12].

**Real Repository Generation v1 (nguồn: repo).** Bộ này có năm dự án công khai ghim commit (OpenPI, Hive, MCO, Squad, SkillRoster), giao thức chạy sạch (thời gian 20 phút mỗi phiên theo mặc định thí điểm, bản nháp đầu và mọi bản sửa phải được ghi lại, ảnh chụp 1440×900) và mẫu báo cáo. Dòng trạng thái ở đầu README ghi: "giao thức thí điểm và tập tác vụ; chưa có lượt chạy hay kết quả chất lượng nào" [S12]. Nghĩa là **tuyên bố "ít làm lại hơn trên repo thật" chưa được đo bằng chính bộ này** ở commit đang đọc; CONTRIBUTING và REVIEWING cũng ghi một lợi ích chưa kiểm chứng phải được coi là tuyên bố chưa xác minh [S6] [S12].

## Dự án được làm như thế nào

**Nhịp độ (người viết đếm bằng `git log`).** 1.744 commit từ 15/4/2026 đến 25/10/2026, chia theo tháng: tháng 4 có 34, tháng 5 có 1, tháng 6 có 7, tháng 7 có 82, tháng 8 có 104, tháng 9 có 674, tháng 10 (đến ngày 25) có 842. Chia đều thì gần 34 commit mỗi ngày trong 25 ngày đầu tháng 10. tt-a1i đứng tên 1.130 commit (khoảng 65%); 104 tên tác giả khác nhau; 551 commit gộp. Dòng cuối là commit gộp PR #1099 chuyển giấy phép. Các tag: 22 tag phiên bản từ v2.0.0 (15/4/2026) đến v3.2.0 (18/10/2026), cộng 2 tag của bản bọc DSH [S5].

**Có dấu vết dùng AI (người viết đếm).** Trong lời nhắn commit có 132 dòng `Co-Authored-By` tên Devin, vài chục dòng tên các mô hình Claude (Opus 5.5, Fable 5, Opus 5...), 10 dòng Cursor; trong các commit gộp có 132 nhánh bắt đầu bằng `codex/`. Con số này chỉ là số dòng ghi công đồng tác giả và tên nhánh, không đo tỉ lệ mã do AI viết. CONTRIBUTING có hẳn mục "AI assistance and contributor responsibility": mọi PR phải khai báo có dùng AI hay không, nêu công cụ, mô hình nếu biết và phần việc nào; một người thật chịu trách nhiệm phải rà soát, hiểu và giải thích được; mô tả do AI sinh ra phải kiểm tra tính chính xác; và "không đoán việc dùng AI từ văn phong" [S6].

**Quy trình đóng góp (nguồn: repo).** Thay đổi về sinh sơ đồ, bố cục, kiểm tra, tương tác, hiệu năng, phụ thuộc hay kiểm thử cần một issue và sự đồng ý của người duy trì về phạm vi trước khi làm; chỉ sửa lỗi chính tả cơ học thì đi thẳng PR. `dev` là nhánh tích hợp và dùng thử, `main` là nhánh ổn định; lô đã dùng thử trên tác vụ thật được đưa từ `dev` lên `main` qua PR riêng, và "CI xanh một mình không chứng minh dùng thử đạt" [S6]. REVIEWING.md quy định cách xem xét: nêu rõ chặn, cần bằng chứng, gợi ý hay sẵn sàng; kiểm tra tín hiệu từ bot trước khi chuyển tiếp [S6]. CodeRabbit cho phản hồi tham khảo, không phải chấp thuận của người [S6].

**CI theo phạm vi tác động (nguồn: repo).** Một job `scope` phân loại đường dẫn thay đổi bằng `scripts/ci-scope.mjs`; đường dẫn lạ, so sánh rỗng hay không có nhánh gốc thì chọn kiểm tra đầy đủ; các tên job bắt buộc luôn hiện diện nên phân loại hỏng không thể biến thành "bỏ qua thành công" [S6] [S15]. Các job: hồi quy đầy đủ chia hai mảnh trên Node 22; tương thích Node 18, 20 và 24; "canonical-test (22)"; hồi quy trình duyệt hai mảnh với Chrome được cấp riêng cho job; giải mã WebM; **kiểm tra ZIP**: dựng lại `archify.zip` và so từng byte; manifest cập nhật công khai phải trỏ tới một bản phát hành ổn định có thật; khói đóng gói trên ubuntu, macOS và Windows; dựng và kiểm kiểu trang web. Cả 60 dòng `uses:` trong các workflow đều ghim bằng mã SHA 40 ký tự (người viết đếm). Workflow phát hành chạy thêm hợp đồng đường dẫn Windows trên Node 22 và 24 [S15].

**Phát hành đóng gói tái lập được (nguồn: repo).** `archify.zip` (5,4 MB, 203 mục, 18,1 MB sau giải nén, người viết đếm) được commit sẵn trong repo; ZIP "chuẩn" chỉ tạo đúng byte với Node 22 chính thức có zlib `1.3.1-e00f703`, trình dựng từ chối các phiên bản khác; xuất bản là hành động có ủy quyền riêng, không ghi đè phiên bản hay tag đã có [S6]. Bản cài sống trên máy người dùng được bảo vệ bằng một quy tắc trong AGENTS.md: chỉ cài, cập nhật hay gỡ khi người dùng yêu cầu rõ; sửa, kiểm thử hay xuất bản repo không ngầm cho phép việc đó [S6].

**Quản trị (nguồn: repo).** `CODEOWNERS` dành các thư mục workflow, hành động và SECURITY.md cho tt-a1i, tức tự động hóa và chính sách nằm dưới sự xem xét của chủ dự án [S15]. SECURITY.md hướng dẫn báo lỗ hổng qua kênh riêng tư của GitHub nếu có, chỉ nhận lỗi ở bản ổn định mới nhất hoặc `main`, và không hứa duy trì bản cũ [S14].

## Hệ sinh thái xung quanh

**DeepSeek Harness (nguồn: repo).** Gói npm `@tt-a1i/archify-dsh@1.0.0` (xuất bản 4/10/2026) là bản đóng gói chỉ chứa kỹ năng, bọc Archify **3.0.1**, hỗ trợ đúng bản host `@deepseek-ai/dsh@0.1.2-rc.1` và Node `^22.19.0 || >=24.0.0`; nó không phải sản phẩm chính thức của DeepSeek. Hai điểm cần biết. Một: bản bọc chậm hơn bản ổn định (3.0.1 so với 3.2.0) vì có chủ ý tách phiên bản và quy trình phát hành riêng [S16] [S5]. Hai: tệp `cordis.patch.yml` dùng biểu thức `!!js` do host nạp để tìm thư mục kỹ năng; tài liệu thừa nhận nó chạy trong tiến trình host, ngoài sandbox của agent, và giới hạn ở các hàm của `path` và `module`, không truy cập mạng hay thông tin xác thực [S16]. Ngoài ra có lỗi đã biết: bản 1.0.0 đặt `includeDefaultRoots: false` có thể làm biến mất các kỹ năng cá nhân và dự án (issue #906); bản sửa chưa phát hành [S16].

**Hermes Agent (nguồn: repo).** Tích hợp cộng đồng chỉ có kỹ năng, không đăng ký công cụ gốc, không đo từ xa, không MCP, không xử lý thông tin xác thực; cài bằng `hermes skills install skills-sh/tt-a1i/archify/archify -y`; vẫn cần Node.js 18+ và chạy `node bin/archify.mjs` [S16].

**Danh mục gói cộng đồng (nguồn: repo).** `community/` là sổ đăng ký các gói độc lập xây trên Archify (kỹ năng, công thức, bộ biểu tượng, ngôn ngữ, bộ bọc), mỗi gói một tệp metadata PR vào nhánh `dev`; hiện có hai mục là DSH và Hermes. Tài liệu nêu rõ không có API plugin chạy trong tiến trình và không dự định có: mã bên thứ ba không bao giờ chạy trong đường ống vẽ, CI hay mô hình tin cậy của việc giao [S16].

**Trang web (nguồn: repo).** Trang công khai là dự án Astro + React + TypeScript riêng, xuất tĩnh lên GitHub Pages tại `/archify/`, không thêm phụ thuộc vào gói kỹ năng; kèm cổng "Proof Lab" (thư viện mẫu), hướng dẫn chọn kịch bản, trang bắt đầu có công cụ chọn agent và hai ngôn ngữ [S1] [S5]. Kênh chính thức do README liệt kê là archify.si và GitHub; "tên hay tên miền giống nhau không chứng minh có liên kết chính thức" [S1].

## Mạng, quyền riêng tư và an toàn

**Kiểm tra cập nhật (nguồn: repo).** `finalize` và `deliver` kèm một kiểm tra cập nhật có giới hạn. Nó chỉ GET một manifest ổn định cố định (mã từ chối mọi URL khác), thành công thì chờ khoảng 24 giờ (±20%), thất bại thì thử lại sau 6 rồi 24 giờ; máy chủ chỉ thấy siêu dữ liệu HTTP bình thường (IP, thời gian), không nhận phiên bản, agent, dữ liệu dự án, nội dung prompt, ID tài khoản hay thiết bị. Nó không bao giờ tự tải hay cài. Đặt `ARCHIFY_UPDATE_CHECK_DISABLED=1` để tắt cả mạng lẫn việc ghi trạng thái nhắc [S1] [S13]. Phía agent, SKILL.md yêu cầu giữ lại một thông báo cập nhật gọn ở câu trả lời cuối khi có bản mới, cho đến khi người dùng hoãn hoặc bỏ qua rõ ràng (hoãn 7 ngày hoặc bỏ qua đúng bản đó) [S2] [S5].

**Bắt biểu tượng thương hiệu (nguồn: repo).** Chỉ chạy khi có thành phần khai báo `brand` tường minh hoặc URL do người dùng cấp. Mã chặn địa chỉ riêng tư (IPv4/IPv6 nội bộ, `localhost`, `.local`), chặn thông tin đăng nhập trong URL và cổng không chuẩn, ghim địa chỉ IP đã kiểm để chống tấn công DNS rebinding, ép mã hóa `identity`, giới hạn thời gian chờ; cờ `ARCHIFY_BRAND_ALLOW_PRIVATE=1` mở lối thoát [S13] [S5]. Danh mục dựng sẵn có 107 biểu tượng (người viết đếm trong `catalog.json`) [S17].

**Xem thử cục bộ (nguồn: repo).** `preview` là chế độ máy tính để bàn, chỉ nghe trên `127.0.0.1` ở cổng ngẫu nhiên, theo dõi một tệp JSON, giữ bản đã kiểm chứng gần nhất khi lưu dở và dừng bằng Ctrl-C [S1] [S17].

**Rủi ro khi đọc mã không tin cậy (suy luận).** Quy trình bảo agent đọc repo, rồi viết JSON và chạy `node bin/archify.mjs`. Nghĩa là nó chạy trong môi trường mà agent đã có shell và quyền; Archify không thêm sandbox riêng, và tài liệu cũng không hứa vậy. Với repo lạ, các rủi ro thông thường của "agent đọc mã không tin cậy" vẫn áp dụng. Bản thân bản HTML đầu ra không gọi mạng trong ví dụ người viết đã kiểm.

## Giấy phép, thương hiệu và tài trợ

**Giấy phép đổi vào hôm nay (nguồn: repo).** NOTICE ghi: Archify phân phối theo Apache License 2.0 trừ khi một tệp, tệp kê khai hay thông báo bên thứ ba nói khác; mã và đóng góp nhận theo MIT đến hết commit trước chuyển đổi `25cf3708` (19/10/2026) vẫn giữ nguyên điều khoản gốc; các bản đã phát hành giữ giấy phép cũ; chuyển đổi này không thu hồi các quyền MIT đã cấp và không tuyên bố một cấp phép bằng sáng chế mới thay cho cộng tác viên lịch sử. Bản quyền ghi tt-a1i năm 2026 và Cocoon AI năm 2025, vì Archify khởi nguồn từ repo Cocoon-AI/architecture-diagram-generator [S14]. Commit `9c306ee8` "license: adopt Apache-2.0 while preserving historical MIT grants" mang ngày 25/10/2026 (người viết đếm bằng `git log -S`). Hệ quả thực tế (suy luận): bản v3.2.0 phát hành 18/10/2026 và các bản trước đó nhiều khả năng đang ở giấy phép MIT, còn Apache-2.0 áp dụng cho nguồn hiện tại; nếu giấy phép là điều kiện bắt buộc, hãy đọc LICENSE đúng bản bạn lấy, không dựa vào huy hiệu README.

**Phần mềm không cấp quyền thương hiệu hay sở hữu nội dung (nguồn: repo).** Giấy phép phần mềm chỉ bao trùm thời gian chạy và mẫu nhúng, không phải quyền sở hữu nội dung tác giả, dữ liệu kinh doanh hay repo nguồn của người dùng, và không cấp quyền dùng thương hiệu Archify [S14].

**Biểu tượng bên thứ ba (nguồn: repo).** Phần lớn đường vẽ biểu tượng sinh từ Simple Icons 16.28.0 (CC0 cho bộ sưu tập, nhưng nhắc rằng không có nghĩa từng biểu tượng đều CC0). Bảng liệt kê các giấy phép riêng: Angular CC-BY-4.0, Apache Airflow và Kafka Apache-2.0, .NET CC0, JavaScript MIT, Jenkins CC-BY-SA-3.0, Rust CC-BY-SA-4.0, **Vue.js CC-BY-NC-SA-4.0** với điều kiện phi thương mại và chia sẻ tương tự vẫn áp dụng. Người dùng tự chịu trách nhiệm xác nhận cách dùng của mình [S14]. Nếu bạn xuất sơ đồ có logo Vue vào tài liệu thương mại, đây là mục đáng đọc (suy luận).

**Quảng cáo và tài trợ trong README (nguồn: repo).** Mục "Sponsors" liệt kê Kimi Work, Supercode, OpenLux, PackyCode, AICodeMirror, Infistar.cc và EverMind (Raven). Phần lớn liên kết mang tham số giới thiệu (`aff=`, `invitecode=`, `channel=`, `utm_source=`) và nêu giá khuyến mãi do nhà tài trợ tự công bố, ví dụ giá nền bằng 8,82%, 4% và 8% giá chính thức của một dịch vụ API; báo cáo này không đánh giá các mức giá đó. README cũng nói rõ phần mềm miễn phí, các dịch vụ trả phí của bên thứ ba do bên đó vận hành và không đại diện cho Archify, đồng thời có mục ủng hộ qua WeChat Pay và Alipay và địa chỉ email nhận tài trợ [S1]. Các liên kết giới thiệu không được trích lại trong bài này.

**Những tuyên bố chưa kiểm chứng được từ repo (nguồn: repo, suy luận).** README có huy hiệu "130K+ installs on skills.sh" nhưng đó là huy hiệu tĩnh viết tay (đường dẫn dạng `badge/installs-130K%2B`), không phải số đếm sống [S1]. Mục "Community and recognition" nêu hạng nhất của bảng xu hướng tuần trên GitHub, bài đăng của QbitAI và bài của midudev, tất cả bằng liên kết ngoài mà người viết chưa mở [S1]. Số sao 88,9 nghìn người viết đọc từ trang GitHub, không từ mã [S18].

## Người viết đã chạy gì

Tất cả trong một thư mục cô lập: bản sao của gói `archify/` và một bản sao repo (qua `git archive`) trong thư mục tạm của phiên, môi trường sạch (`env -i`), `ARCHIFY_UPDATE_CHECK_DISABLED=1`, Node v22.22.0, Chromium của Playwright thay cho Chrome ghim trong CI. Không cài gì lên máy ngoài các gói đã khóa của repo (`npm ci --ignore-scripts`). Không chạy tác nhân nào, nên chưa có lượt "agent thật vẽ sơ đồ" nào từ phía người viết.

| Lệnh | Kết quả |
|---|---|
| `doctor` | 27 mục `[ok]`, kết thúc "Archify is ready." |
| `guide "Show an API request with Redis cache miss"` | Đề xuất `sequence`, độ tin cậy cao, kèm prompt mẫu |
| `validate architecture web-app.architecture.json --quality showcase --json` | `ok: true`, 9 kiểm tra đạt |
| Cùng lệnh sau khi trỏ một cạnh vào nút không tồn tại | Thoát mã 1, `architecture/unknown-endpoint`, có `supportedFixes` |
| `deliver ... --quality showcase --json` | `ok: true`, tệp HTML 845.929 byte, không gọi mạng trong mã |
| `finalize architecture ...` với Chromium | 4 cổng đạt trong 6,56 giây, kèm khuyến nghị xem tuyến đường bằng mắt |
| `finalize explainer` trên ví dụ TLS | `ok`, 1,33 giây, tệp 505.526 byte, `browser-check` là `not-run` |
| `compare architecture base head ... --json` | `ok: true`, thành phần: thêm 1, đổi 1, bỏ 1, di chuyển 1; kết nối: thêm 1, đổi 2, bỏ 1, đổi tuyến 1 |
| `node scripts/run-tests.mjs test/core-smoke.test.mjs` | 19 trên 19 đạt, 15,6 giây (cần `npm ci` ở thư mục gốc trước; chưa cài thì lỗi `ERR_MODULE_NOT_FOUND: parse5`) |
| `npm run test:generated` | "all checks passed" (khung kiểm schema, độ mới của mẫu, đồng bộ phiên bản README/SKILL/package) |
| Bộ kiểm thử đầy đủ (`node scripts/run-tests.mjs`, 234 tệp) | **Chưa có kết luận.** Lượt chạy duy nhất diễn ra trong môi trường không tương đương CI: bản sao không có `.git`, đặt `ARCHIFY_UPDATE_CHECK_DISABLED=1`, dùng Chromium của Playwright thay cho Chrome của CI. Log ghi nhiều test trượt, thuộc các nhóm: trình duyệt thật, kiểm tra cập nhật, đóng gói. Người viết chỉ xác định nguyên nhân cho một mẫu: test "package smoke rejects a missing or modified distribution license" dừng với lỗi `not a git repository`. Phần còn lại chưa phân tích. Lượt chạy lại trong môi trường sạch không được cấp quyền thực thi nên bị bỏ; vì vậy bài này không khẳng định bộ kiểm thử đầy đủ đạt hay trượt ở commit 51a2917 |

## Điểm yếu và có nên dùng không

**Điểm mạnh (suy luận từ các bằng chứng trên).** Một: ý tưởng "agent quyết định, máy kiểm" được làm đến nơi, có biên nhận lỗi máy đọc được, đặt sẵn giới hạn hai vòng sửa và giao hàng nguyên tử, nên giảm cảnh sơ đồ hỏng nằm lại ở chỗ cũ. Hai: kết quả là một tệp HTML đứng riêng không gọi mạng, dễ lưu và dễ gửi. Ba: bằng chứng nguồn ghim commit là cách hiếm thấy để buộc sơ đồ kiến trúc phải trỏ về dòng mã. Bốn: tài liệu tự ghi cả những thứ đã từ chối và thí nghiệm thất bại, tức tác giả để lại dấu vết lý do thiết kế. Năm: bộ kiểm thử lớn, CI phân tầng và có kiểm tra ZIP đúng từng byte.

**Điểm yếu và rủi ro (suy luận, kèm bằng chứng).**

- **Chất lượng phụ thuộc agent.** Mức sàn đo được là 8/15 lượt dùng ngay; luồng dữ liệu 0/3 và quy trình 1/3 [S11]. Nên chuẩn bị cho một đến hai vòng sửa và tự xem kết quả.
- **Cổng tự động không thay mắt.** Ngay ví dụ tác giả làm ra vẫn nhận khuyến nghị xem tuyến đường [S8] (người viết chạy thử). Bản 3.1.0 cũng thừa nhận trong "Known limitations" rằng sơ đồ tuần tự lớn có thể cần cuộn trang và một số đầu vào luồng dữ liệu dùng chung hành lang hình ảnh [S5].
- **Đo trên repo thật chưa có số.** Bộ benchmark này mới là giao thức [S12].
- **Giấy phép vừa đổi, biểu tượng có điều kiện riêng.** Xem mục trên [S14].
- **Tài liệu lệch nhau ở vài con số.** README ghi "11 kịch bản đã commit" trong Proof Lab, còn manifest thư viện mẫu có 12 mục với 108 lượt kiểm (12 × 9) ở phiên bản 3.2.0; thư viện mẫu chỉ có 6 trong 10 loại (quy trình 3, kiến trúc 2, tuần tự 2, luồng dữ liệu 2, vòng đời 2, ERD 1), còn cây, lớp, dòng thời gian và thác thời gian chỉ có ở thư mục `archify/examples/` [S1] [S17]. README tiếng Hàn dài 232 dòng (13,9 KB so với 36,9 KB của bản tiếng Anh), ngắn hơn rõ rệt; CHANGELOG nhắc việc kiểm tra đồng bộ README cho các bản Anh, Trung, Nhật, còn `grep` không thấy `README_KO` ở `test/` hay `scripts/` [S5] (người viết đếm; suy luận rằng bản Hàn không nằm trong cùng kiểm tra).
- **Nhịp thay đổi rất cao.** 842 commit trong 25 ngày [người viết đếm] nghĩa là bản bạn đọc hôm nay sẽ khác bản tuần sau. Nên ghim phiên bản hoặc commit; bản bọc DSH đã chậm hai phiên bản [S16].
- **Một tệp CLI rất lớn.** `bin/archify.mjs` dài 7.289 dòng; đọc hay sửa tốn công (người viết đếm).
- **Phạm vi chủ ý hẹp.** Không dùng cho biểu đồ số liệu hay bảng điều khiển, không có trình soạn, không có chia sẻ lưu trữ máy chủ, giao diện chính cho máy tính để bàn [S2] [S1] [S3].
- **Quảng cáo trong README.** Có nhiều liên kết giới thiệu; nó không ảnh hưởng đến mã nhưng làm README khó đọc hơn đối với người chỉ cần cài đặt [S1].
- **Hạn chế của chính bài này.** Người viết chưa chạy agent, chưa chạy các lệnh `preview`, `visual-check`, WebM, chưa xem bằng mắt các tệp HTML dựng ra, và chưa xác nhận bộ kiểm thử đầy đủ đạt ở commit này; chỉ bộ khói lõi (19/19) và kiểm tra tệp sinh (đạt) được xác nhận.

**Nên dùng khi nào (suy luận).**

| Tình huống | Nhận xét |
|---|---|
| Cần hiểu hoặc trình bày kiến trúc của một repo có sẵn, chấp nhận kiểm lại các cạnh quan trọng | Phù hợp nhất; bằng chứng nguồn ghim commit giúp bạn kiểm nhanh |
| Cần tài liệu thiết kế, runbook, lược đồ dữ liệu dạng tệp HTML gửi được | Phù hợp; xuất PNG/PDF có sẵn |
| Cần sơ đồ chính xác theo từng pixel hoặc theo chuẩn mô hình hóa (UML/C4 đầy đủ) | Không phù hợp: công cụ không phải trình soạn và không phân tích Mermaid |
| Môi trường cách ly mạng hoặc quy định chặt về lưu lượng ra | Dùng được nếu đặt `ARCHIFY_UPDATE_CHECK_DISABLED=1` và không dùng chụp biểu tượng từ URL |
| Dự án có điều kiện giấy phép | Kiểm tra giấy phép của đúng bản và các biểu tượng bên thứ ba |
| Cần chất lượng đồng đều từ một mô hình nhỏ | Cẩn thận: mức sàn đo được thấp, nên có người rà soát bằng mắt |

## Cách học trong một buổi

Mỗi bước dưới đây lấy lệnh từ README hoặc SKILL.md [S1] [S2]. Thời lượng là ước tính của người viết.

1. **(10 phút) Đọc hai tệp.** Mở `README.md` đến hết phần "Choose the right diagram", rồi `archify/SKILL.md`; ghi lại câu trả lời cho "agent được dặn làm gì khi gặp một yêu cầu vẽ sơ đồ?".
2. **(10 phút) Chạy ba lệnh không cần agent.** `cd archify`, `node bin/archify.mjs doctor`, `node bin/archify.mjs guide "Show an API request with Redis cache miss"`, `node bin/archify.mjs validate workflow examples/agent-tool-call.workflow.json --quality showcase --json`. Mục tiêu: nhìn tận mắt biên nhận JSON.
3. **(10 phút) Phá một tệp ví dụ.** Sao chép một ví dụ ra ngoài repo, đổi `to` của một cạnh thành tên không có, chạy lại `validate`, đọc `diagnostics[]` và `supportedFixes`.
4. **(15 phút) Giao một sơ đồ.** Dùng `deliver` như README, mở tệp HTML, thử `/`, `R`, `L`, `M`, `T`, `E`; đổi sang chế độ Still để thấy khác biệt chuyển động.
5. **(15 phút) Đọc phần ROADMAP "Not planned" và thí nghiệm bị loại.** Với mỗi mục, tự trả lời: bạn đồng ý với lý do chưa?
6. **(30 phút) Cài vào agent của bạn và thử một repo nhỏ.** Dùng `npx skills add tt-a1i/archify -g`, yêu cầu vẽ kiến trúc runtime 8 đến 12 thành phần có bằng chứng nguồn như prompt mẫu trong README. Sau đó tự kiểm ba cạnh bất kỳ so với mã và ghi lại số vòng sửa.
7. **(tuỳ chọn) Thử trang trả lời một trang.** Yêu cầu agent trả lời một câu hỏi kỹ thuật dưới dạng một trang rồi so với câu trả lời bằng văn bản.

## Điều cần nhớ

Một: Archify là kỹ năng và công cụ dòng lệnh cho agent, biến JSON có kiểu thành HTML đứng riêng; agent đặt bố cục, công cụ kiểm tra và vẽ [S2] [S4]. Hai: giá trị lớn nhất là cổng kiểm tra và biên nhận lỗi máy đọc được, cùng bằng chứng nguồn ghim commit; giá trị này chưa đồng nghĩa với "sơ đồ nào cũng đẹp và đúng" vì mức sàn đo được là 8/15 và có khuyến nghị xem bằng mắt [S11] [S8] [S9]. Ba: giấy phép đổi sang Apache-2.0 ngày 25/10/2026, biểu tượng bên thứ ba có điều kiện riêng và README có quảng cáo; đọc LICENSE của đúng bản bạn dùng [S14] [S1]. Bốn: nếu cần tắt mạng, đặt `ARCHIFY_UPDATE_CHECK_DISABLED=1` [S13]. Năm: dự án đổi cực nhanh; hãy ghim phiên bản hoặc commit khi dựa vào nó [S5].

## Lưu ý

Giới hạn nguồn: bài đọc bản sao đầy đủ lịch sử của repo `tt-a1i/archify` tại commit 51a291770851ad27a400cca73c753c166b5e0c65 (25/10/2026), nhánh mặc định. Lịch sử Git được tải đủ để đếm commit, tác giả, tag và ngày; mọi con số "người viết đếm" lấy từ bản đó bằng `git`, `wc` và script, dễ kiểm lại, và sẽ đổi khi repo cập nhật. Số sao, fork, người theo dõi, issue và pull request mở lấy từ trang GitHub công khai ngày 25/10/2026 qua một công cụ đọc web có tóm tắt, nên là số xấp xỉ theo cách hiển thị rút gọn của trang [S18]; người viết không dùng API GitHub, vì xin quyền ghi chỉ để đọc số sao là không cần thiết. Người viết đọc README, SKILL.md, PRODUCT.md, DESIGN.md, ROADMAP.md, CHANGELOG (các bản 3.2.0 đến 3.0.0), CONTRIBUTING.md, REVIEWING.md, SECURITY.md, NOTICE, THIRD_PARTY_NOTICES.md, các tài liệu tham chiếu chính trong `archify/references/`, README của ba bộ benchmark, workflow CI, README của hai tích hợp, danh mục cộng đồng và các đoạn mã liên quan đến mạng, cập nhật và bằng chứng nguồn; không đọc toàn bộ 52 nghìn dòng mã chạy, 84 nghìn dòng mã kiểm thử, các tệp `docs/` và `journal/`. Người viết chưa dùng Archify qua một agent thật, chưa chạy `preview`, `visual-check`, kiểm thử WebM, kiểm thử trang web, DSH hay Hermes, chưa có kết quả đáng tin cho bộ kiểm thử đầy đủ (xem bảng "Người viết đã chạy gì"), và chưa mở các liên kết ngoài (X, QbitAI, skills.sh). Các câu về hành vi của agent trong SKILL.md là chỉ dẫn viết cho agent, không phải kết quả đã tái lập. Phần giấy phép chỉ là tóm tắt, không phải tư vấn pháp lý. Repo đang được cập nhật thường xuyên nên có thể đã khác khi bạn đọc.

## Nguồn tham khảo

- [S1] tt-a1i, README.md: giới thiệu, cài đặt, mười loại sơ đồ, trình xem, tài trợ, giấy phép, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/README.md
- [S2] tt-a1i, archify/SKILL.md: định nghĩa kỹ năng, bộ định tuyến loại sơ đồ, finalize, quy tắc trả lời, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/SKILL.md
- [S3] tt-a1i, PRODUCT.md và DESIGN.md: người dùng, mục đích, nguyên tắc thiết kế, hệ màu và kiểu chữ, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/PRODUCT.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/DESIGN.md
- [S4] tt-a1i, ROADMAP.md: JSON IR, thí nghiệm kiểm chứng thất bại, các giai đoạn, danh sách không thực hiện, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/ROADMAP.md
- [S5] tt-a1i, CHANGELOG.md: các bản 3.0.0, 3.0.1, 3.1.0, 3.2.0 và hạn chế đã biết, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/CHANGELOG.md
- [S6] tt-a1i, CONTRIBUTING.md, REVIEWING.md và AGENTS.md: quy trình đóng góp, chính sách AI, bằng chứng theo tác động, CI, phát hành, cách rà soát, quy tắc cho agent, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/CONTRIBUTING.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/REVIEWING.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/AGENTS.md
- [S7] tt-a1i, archify/schemas/README.md: hợp đồng schema, meta, locale, bộ giao diện, chú giải, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/schemas/README.md
- [S8] tt-a1i, archify/references/delivery-contract.md: finalize, giao nguyên tử, tệp phụ, khóa thư mục, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/references/delivery-contract.md
- [S9] tt-a1i, archify/references/repository-authoring.md và authoring-defaults.md: quy trình đọc mã có bằng chứng nguồn, mặc định bố cục và khoảng cách, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/references/repository-authoring.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/references/authoring-defaults.md
- [S10] tt-a1i, archify/references/explainer-authoring.md: ngôn ngữ bản nháp trang trả lời một trang, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/references/explainer-authoring.md
- [S11] tt-a1i, benchmarks/ordinary-model-floor: README và kết quả 15 lượt ngày 26/7/2026, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/benchmarks/ordinary-model-floor/README.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/benchmarks/ordinary-model-floor/results/2026-07-26-pi-three-models-quality-first.json
- [S12] tt-a1i, benchmarks/real-repo-generation và repair-rounds: hai README về giao thức thí điểm và đo biên nhận, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/benchmarks/real-repo-generation/README.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/benchmarks/repair-rounds/README.md
- [S13] tt-a1i, mã bằng chứng nguồn, kiểm tra cập nhật và bắt biểu tượng: repository-evidence.mjs, check-update.mjs, brand-marks.mjs, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/renderers/shared/repository-evidence.mjs, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/scripts/check-update.mjs, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/renderers/shared/brand-marks.mjs
- [S14] tt-a1i, NOTICE, THIRD_PARTY_NOTICES.md và SECURITY.md: chuyển đổi giấy phép, biểu tượng bên thứ ba, chính sách báo lỗ hổng, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/NOTICE, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/THIRD_PARTY_NOTICES.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/SECURITY.md
- [S15] tt-a1i, .github/workflows/ci.yml và CODEOWNERS: các job CI, ma trận Node và hệ điều hành, chủ sở hữu tự động hóa, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/.github/workflows/ci.yml, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/.github/CODEOWNERS
- [S16] tt-a1i, tích hợp và cộng đồng: integrations/deepseek-harness/README.md, integrations/hermes-agent/README.md, community/README.md, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/integrations/deepseek-harness/README.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/integrations/hermes-agent/README.md, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/community/README.md
- [S17] tt-a1i, số liệu và manifest: archify/package.json, package.json, archify/bin/archify.mjs, docs/gallery/manifest.json, archify/brand-marks/catalog.json, 2026, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/package.json, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/package.json, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/bin/archify.mjs, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/docs/gallery/manifest.json, https://github.com/tt-a1i/archify/blob/51a291770851ad27a400cca73c753c166b5e0c65/archify/brand-marks/catalog.json
- [S18] GitHub, trang repo tt-a1i/archify: sao, fork, người theo dõi, issue, PR mở (không ghim được vào commit; đọc ngày 25/10/2026), https://github.com/tt-a1i/archify
