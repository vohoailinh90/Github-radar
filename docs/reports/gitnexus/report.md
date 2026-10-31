---
id: R10
title: GitNexus: biến cả codebase thành đồ thị tri thức cho AI agent
topic: ky-thuat
date: 2026-10-24
---
# GitNexus: biến cả codebase thành đồ thị tri thức cho AI agent

## Tóm tắt

GitNexus là gì, dùng vào việc gì, và chỗ nào cần dè dặt? README mô tả nó là công cụ lập chỉ mục một codebase thành đồ thị tri thức gồm symbol, lời gọi, phụ thuộc và luồng thực thi; coding agent hỏi đồ thị đó qua công cụ MCP, dòng lệnh hoặc giao diện web [S1]. Bộ lập chỉ mục chạy cục bộ và không dùng LLM [S1]. Về hình thức, đây là một monorepo TypeScript: gói npm `gitnexus` (CLI, MCP server, API HTTP, bộ lập chỉ mục), giao diện web React và một gói kiểu dùng chung [S4] [S3]. Gói npm ở phiên bản 1.6.12 và đòi hỏi Node 22.18 trở lên (nhánh 22) hoặc 24.11 trở lên [S13].

Bài này đọc repo theo ba tầng. Tầng một là ý tưởng và cách dùng: vì sao tính sẵn đồ thị giúp agent bớt đoán [S2]. Tầng hai là cơ chế bên trong: pipeline 20 phase, phân giải lời gọi cho 18 ngôn ngữ, lược đồ đồ thị, 19 công cụ MCP [S3] [S9] [S10] [S11] [S6]. Tầng ba là điều cần dè dặt: giấy phép phi thương mại, máy chủ `serve` chưa tự xác thực, và tài liệu kiến trúc lệch mã nguồn ở vài con số [S8] [S5] [S7] [S3].

Mỗi khẳng định trong bài mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ file của repo ở commit d8a256a (24/10/2026). **Người viết đếm** nghĩa là một con số tính bằng lệnh trên bản đã tải về, và bài nói rõ đếm cái gì. **Suy luận** là nhận xét của người viết, không phải lời của tác giả repo. Bài **chưa chạy** công cụ nào: mọi mô tả hành vi là đọc mã và tài liệu, không phải kết quả thực nghiệm.

Ba ý đáng mang theo. Thứ nhất, giá trị của GitNexus nằm ở chỗ đồ thị được tính trước, nên agent hỏi "ai gọi hàm này" và "sửa nó ảnh hưởng gì" bằng một lời gọi thay vì nhiều lượt grep [S2]. Thứ hai, repo tự đặt nguyên tắc "chính xác hơn đầy đủ": bỏ sót một route là giới hạn độ phủ, còn bịa ra một route là nói sai sự thật, và kết quả luôn kèm độ tin cậy [S3]. Thứ ba, trước khi dùng trong công việc có thu tiền hoặc mở máy chủ ra ngoài mạng, hãy đọc giấy phép PolyForm Noncommercial và phần bảo mật của tài liệu triển khai [S8] [S7].

## Repo này là gì

**Mục tiêu (nguồn: repo).** README: GitNexus lập chỉ mục một codebase thành đồ thị tri thức gồm symbol, lời gọi, phụ thuộc và luồng thực thi, và được dùng qua công cụ MCP của agent, qua CLI, hoặc qua một trình khám phá đồ thị trên web [S1]. Tài liệu kiến trúc mô tả một luồng duy nhất: lập chỉ mục, đồ thị, rồi công cụ truy vấn [S3].

**Các gói (nguồn: repo).** Thư mục gốc có `gitnexus` (CLI và MCP), `gitnexus-web` (giao diện web), `gitnexus-shared` (kiểu và lược đồ dùng chung), cùng các gói tích hợp cho Claude Code, Cursor và Factory, bộ đánh giá `eval` và bộ rà soát PR `pr-swarm-review` [S4] [S3].

**Số liệu tự báo của repo (nguồn: repo).** Khối GitNexus trong AGENTS.md ghi repo tự lập chỉ mục chính nó được 248.612 symbol, 565.510 quan hệ và 918 luồng thực thi [S4]. Đây là con số do công cụ báo cho repo của chính nó tại thời điểm tác giả chạy, có thể đã cũ so với mã hiện tại (suy luận).

**Giấy phép và mô hình thương mại (nguồn: repo).** Giấy phép là PolyForm Noncommercial 1.0.0 [S8]. README nói dùng thương mại cần giấy phép riêng qua trang của Akon Labs, và có bản Enterprise (SaaS hoặc tự lưu trữ) với review PR theo phạm vi ảnh hưởng, wiki tự cập nhật, tự lập chỉ mục lại, đồ thị đa repo, hỗ trợ OCaml và ưu tiên ngôn ngữ; Code Wiki cũng có ở bản mã nguồn mở [S1]. Bài không phải tư vấn pháp lý.

## Ý tưởng cốt lõi và cách dùng

**Vấn đề được giải (nguồn: repo).** Agent lập trình thường sửa một hàm mà không biết còn bao nhiêu nơi phụ thuộc vào nó. GitNexus tính trước mọi phụ thuộc, chuỗi lời gọi và luồng thực thi vào một đồ thị truy vấn được, để agent hỏi thẳng thay vì tự suy ra từ chuỗi ký tự [S2].

**Ba cửa vào cho cùng một đồ thị (nguồn: repo).** Qua MCP, agent gọi các tool như `query`, `context`, `impact`; nhiều agent có thể dùng chung một server HTTP trên cổng 3111. Qua CLI có các lệnh `query`, `impact`, `status`, `list`, và cờ `analyze --watch` lập chỉ mục lại khi file đổi. Qua web, chạy `gitnexus serve` rồi mở giao diện web để duyệt đồ thị và hỏi đáp AI trên index sẵn có [S1].

**Bắt đầu nhanh (nguồn: repo).** README đưa hai lệnh: `npx gitnexus analyze` từ thư mục gốc của repo để lập chỉ mục, và `npx gitnexus setup` để cấu hình MCP cho các editor, chạy một lần. `analyze` còn cài skill, đăng ký hook của Claude Code và ghi các file ngữ cảnh `AGENTS.md` và `CLAUDE.md`; cờ `--index-only` chỉ lập chỉ mục mà không ghi các file tích hợp đó [S1].

**Sáu việc agent làm được ngay (nguồn: repo).** Bảng trong README: tìm code và luồng liên quan (`query`), xem người gọi và phụ thuộc của một symbol (`context`), đo phạm vi ảnh hưởng của một thay đổi (`impact`), lần đường giữa hai symbol (`trace`), ánh xạ một git diff sang symbol bị tác động (`detect_changes`), và đổi tên theo ngữ nghĩa với xem trước rồi mới áp dụng (`rename`) [S1].

**Dè dặt của chính tài liệu (nguồn: repo).** README dặn rằng độ phân giải phụ thuộc vào mức hỗ trợ ngôn ngữ và bằng chứng sẵn có, nên cần đọc cảnh báo mơ hồ, độ mới của chỉ mục và giới hạn độ phủ [S1].

## Pipeline lập chỉ mục

**Một DAG phase (nguồn: repo).** Lệnh `analyze` gọi `runFullAnalysis`, rồi `runPipelineFromRepo`. Mỗi phase khai báo phụ thuộc và kiểu đầu ra; bộ chạy sắp xếp theo thứ tự topo, từ chối tên trùng, phụ thuộc thiếu và chu trình, và chỉ đưa cho một phase kết quả của đúng các phụ thuộc nó khai [S3].

**Số phase (người viết đếm).** Hàm `buildPhaseList` đăng ký 22 phase; hai phase `taintSummaries` và `callSummaries` chỉ bật khi dùng cờ `--pdg`, nên DAG mặc định có 20 phase [S9]. Tài liệu kiến trúc ghi "19 phase": con số cũ hơn mã [S3].

**Thứ tự phụ thuộc (nguồn: repo).** Chuỗi chạy bắt đầu bằng `scan` rồi `structure`; sau đó có ba nhánh độc lập (`springConfig`, `markdown`, `cobol`), rồi `parse`, rồi ba nhánh độc lập nữa (`routes`, `tools`, `orm`), rồi `crossFile` và `scopeResolution`, các phase Spring, `pruneLocalSymbols`, rồi `mro`, `springAopInheritance`, `di`, và cuối cùng `communities` rồi `processes` [S9] [S3].

**Vòng đời của một lần analyze (nguồn: repo).** Pipeline dựng đồ thị trong bộ nhớ, rồi nạp vào LadybugDB trong thư mục `.gitnexus/`. Trước khi chạy, `analyze` thoát sớm nếu `lastCommit` đã trùng HEAD (trừ khi dùng `--force`). Sau khi nạp là bước lập chỉ mục toàn văn, rồi embeddings nếu bật cờ `--embeddings`, rồi ghi metadata, đăng ký repo và sinh `AGENTS.md`, `CLAUDE.md` [S3].

**Bộ chạy và cách parse (nguồn: repo).** Các phase chạy tuần tự và cùng ghi vào một `KnowledgeGraph` dùng chung. Việc parse đi theo mẻ khoảng 20 MB để chặn bộ nhớ, qua một worker pool là đường parse duy nhất, và có cache nhận diện theo nội dung SHA-256: mẻ file không đổi thì bỏ qua parse. Thêm một phase mới nghĩa là tạo file, export và đăng ký trong `buildPhaseList()` [S3].

**Ghi tăng dần (nguồn: repo).** Mã có một ngưỡng: nếu phần đồ thị phải ghi lại vượt một nửa (`INCREMENTAL_MAX_WRITE_FRACTION = 0.5`) và có từ 50 file trở lên, lần ghi tăng dần được nâng thành ghi lại toàn bộ [S17].

## Phân giải lời gọi và 18 ngôn ngữ

**Phần dày nhất của tài liệu kiến trúc (nguồn: repo).** Câu hỏi trung tâm là: lời gọi này trỏ tới hàm nào? GitNexus tách phần chung (phân giải theo phạm vi) khỏi phần riêng từng ngôn ngữ. Mỗi ngôn ngữ cắm vào bằng một `ScopeResolver` đăng ký trong `SCOPE_RESOLVERS`, và quy tắc trong AGENTS.md cấm mã dùng chung trong `ingestion/` nêu tên một ngôn ngữ [S3] [S4].

**Mười tám ngôn ngữ (người viết đếm).** Enum `SupportedLanguages` có 18 mục: JavaScript, TypeScript, Python, Java, C, C++, Objective-C, C#, Go, Ruby, Rust, PHP, Kotlin, Swift, Dart, Vue, COBOL và Zig [S11]. README nêu đủ danh sách này và dặn rằng mức hỗ trợ khác nhau theo cấu trúc ngôn ngữ, với các kiểm kê riêng từng ngôn ngữ [S1]. Tài liệu kiến trúc cho biết COBOL dùng bộ xử lý regex riêng thay vì tree-sitter [S3].

**Thứ tự kế thừa (nguồn: repo).** Tài liệu mô tả các chiến lược MRO: `first-wins` cho Java, C#, C++, TypeScript, Ruby và Go; `c3` (tuyến tính hoá C3) cho Python; `ruby-mixin` cho Ruby có nhận biết mixin; và `none` cho ngôn ngữ đơn kế thừa [S3].

**Nguyên tắc "chính xác hơn đầy đủ" (nguồn: repo).** Bỏ sót một route là giới hạn độ phủ; bịa ra một route là nói sai sự thật. Regex không dịch chính xác thì bị bỏ. Tên mơ hồ thì từ chối chọn thay vì đoán, và một đối tượng tên `app` hay `router` tự nó không phải bằng chứng. `impact` và `context` trả kèm độ tin cậy `exact` hoặc `lower-bound`, để người đọc biết con số là chính xác hay chỉ là cận dưới, và mức rủi ro có thể là `UNKNOWN` thay vì một số 0 giả [S3].

## Dữ liệu và lưu trữ

**Lược đồ (người viết đếm).** Trong `schema-constants.ts`, `NODE_TABLES` có 35 loại node và `REL_TYPES` có 33 loại quan hệ [S10]. Tài liệu kiến trúc còn ghi "44 loại node, 21 loại quan hệ" ở một sơ đồ: số cũ hơn mã [S3].

**Nhóm node (nguồn: repo).** Gồm cấu trúc (File, Folder, Module, Namespace, Section), khả gọi (Function, Method, Constructor, Delegate, Macro, Template), kiểu (Class, Interface, Struct, Enum, Trait, Impl, Union, Typedef, TypeAlias, Record, Protocol, Category, Annotation), giá trị (Const, Static, Variable, Property, CodeElement), lớp phân tích (Community, Process), lớp framework (Route, Tool, Destination) và BasicBlock cho cờ `--pdg` [S10]. Mọi quan hệ dùng chung bảng `CodeRelation` và phân biệt bằng cột `type` [S3].

**Cơ sở dữ liệu (nguồn: repo).** Đồ thị nằm trong LadybugDB, một cơ sở dữ liệu đồ thị nhúng có hỗ trợ vector, trước đây tên là KuzuDB; README cũng ghi lời cảm ơn dự án này [S1] [S3].

**Tìm kiếm và embeddings (nguồn: repo).** Tìm kiếm lai BM25 và vector, gộp bằng Reciprocal Rank Fusion với K=60. Embeddings dùng mô hình Snowflake arctic-embed-xs 384 chiều, chỉ cho File, Function, Class, Method và Interface, cập nhật tăng dần theo băm SHA1 nội dung [S3].

**Độ mới của chỉ mục (nguồn: repo).** Mô-đun `git-staleness` so `lastCommit` với HEAD và xếp trạng thái thành `current`, `behind`, `diverged` hoặc `unknown`; cùng một dữ liệu dùng cho MCP và web [S3].

## Công cụ MCP

**Mười chín công cụ (người viết đếm).** Tài liệu tham chiếu ghi 19 công cụ MCP, gồm 17 công cụ theo repo và 2 công cụ theo nhóm repo; README của gói ghi cùng con số [S6] [S2]. Tài liệu kiến trúc chỉ liệt kê 16 công cụ trong bảng của nó: số cũ hơn mã [S3].

**Chia theo việc cần làm (nguồn: repo).** Khám phá: `list_repos`, `query`, `context`, `trace`, `cypher`. An toàn khi sửa: `impact` (phạm vi ảnh hưởng theo độ sâu, kèm mức rủi ro), `detect_changes`, `rename` (xem trước rồi áp dụng bằng một `plan_token` dùng một lần), `check`. API và tích hợp: `route_map`, `api_impact`, `shape_check`, `tool_map`. Luồng dữ liệu, cần `analyze --pdg`: `explain` và `pdg_query`. Đọc mã gốc: `read_file` và `grep` làm dự phòng khi đồ thị chưa đủ. Nhóm repo: `group_list`, `group_sync` [S6] [S3].

**Resource và prompt (người viết đếm).** File `resources.ts` khai 2 resource tĩnh (`gitnexus://repos`, `gitnexus://setup`) và 8 mẫu resource (tổng quan repo, module, process, lược đồ, chi tiết module, vết process, registry hợp đồng của nhóm, trạng thái chỉ mục của nhóm), tức 10 resource. Hai prompt dẫn đường là `detect_impact` và `generate_map` [S12] [S6].

**Kiểm soát truy cập và ngân sách phản hồi (nguồn: repo).** Đặt `GITNEXUS_MCP_READ_ONLY=1` thì chỉ còn bề mặt đọc của một repo: `rename` chỉ xem trước, `cypher` và các công cụ nhóm repo bị ẩn. `GITNEXUS_MCP_ALLOWED_REPOS` giới hạn repo cho tool, resource và HTTP nhúng. Tham số `maxTokens` cắt phản hồi của `query`, `context`, `impact`; mã ước lượng 4 byte cho mỗi token (`MCP_TOKEN_ESTIMATE_BYTES = 4`), và `response_sections` chọn phần được trả về [S6] [S18].

## Phân tích sâu: luồng dữ liệu và nhiều repo

**Lớp CFG và PDG, tuỳ chọn (nguồn: repo).** Cờ `analyze --pdg` thêm đồ thị luồng điều khiển và phụ thuộc dữ liệu ở mức câu lệnh: `BasicBlock` cùng cạnh `CFG`, phụ thuộc dữ liệu `REACHING_DEF`, phụ thuộc điều khiển `CDG` kiểu Ferrante, và các cạnh `TAINTED`, `SANITIZES`, `TAINT_PATH` cho phân tích taint. `explain` đọc dữ liệu taint; `pdg_query` trả lời điều kiện để chạy và dòng chảy của biến. Các lớp này mặc định tắt, và provider báo vùng không hỗ trợ thay vì bịa ra luồng đầy đủ [S3] [S10].

**Nhóm repo và hợp đồng giữa dịch vụ (nguồn: repo).** Một nhóm repo có Contract Registry (`contracts.json`) và một đồ thị cầu nối. `query`, `context`, `impact` nhận repo dạng `@tên-nhóm` hoặc `@nhóm/thư-mục-member`; `query` gộp kết quả từng repo bằng RRF, `impact` chạy trong member được chọn rồi lan qua biên bằng Contract Bridge, và `trace` nối đường đi qua một biên hợp đồng. Trạng thái nhóm lộ ra qua các resource, và các tool `group_query`, `group_context`, `group_impact`, `group_contracts`, `group_status` cố ý không được thêm [S3] [S6].

## Web UI, triển khai và bảo mật

**Web UI (nguồn: repo).** Giao diện là client mỏng: mọi truy vấn đi qua API HTTP của `gitnexus serve` trên cổng 4747 [S7]. Ngăn xếp theo `package.json`: React 19, Vite 8, Tailwind 4, i18next, Sigma.js 3 vẽ đồ thị bằng WebGL, graphology, d3, Mermaid, và hỏi đáp AI qua các gói LangChain cho Anthropic, OpenAI, Google GenAI và Ollama [S15].

**Ba cách triển khai (nguồn: repo).** Cục bộ: chạy `gitnexus serve` rồi mở giao diện web, dùng index sẵn có mà không cần lập chỉ mục lại [S1]. Docker: server ở cổng 4747 và web ở cổng 4173, hai image ký Cosign phát hành đồng thời ở GHCR và Docker Hub [S7]. Render: một Blueprint hai dịch vụ, mức chi phí mặc định khoảng 35 USD mỗi tháng (25 USD cho server, 7 USD cho web, 2,5 USD cho đĩa 10 GB); mặc định server có 2 GB RAM và có thể nâng lên 4 GB nếu hết bộ nhớ khi lập chỉ mục [S7].

**Ranh giới bảo mật cần nhớ (nguồn: repo).** `serve` chưa tự xác thực và từ chối khởi động khi đặt `GITNEXUS_PUBLIC_ORIGIN`; muốn mở công khai phải đi qua proxy có token. Trên Render, token là kiểm soát duy nhất, vì proxy xoá header `Origin` nên lớp chống CSRF của server không còn tác dụng. Nếu không có `GITNEXUS_MCP_AUTH_TOKEN` hay một ranh giới xác thực ở rìa mạng, `/api/mcp` không xác thực. Image chỉ phát hành từ tag `vX.Y.Z` [S7] [S5].

**Quyền riêng tư dữ liệu (nguồn: repo).** README: bộ lập chỉ mục không gọi LLM; embeddings từ xa, wiki và AI chat chỉ dùng nhà cung cấp mà người dùng cấu hình [S1].

## Tích hợp agent và tự kiểm chứng

**Mức hỗ trợ editor (nguồn: repo).** README của gói có bảng mức hỗ trợ theo editor. Claude Code và Codex có mức "Full" và đi sâu nhất: hook `PreToolUse` làm giàu truy vấn bằng đồ thị trước khi chạy, và hook `PostToolUse` phát hiện chỉ mục đã cũ rồi nhắc agent lập chỉ mục lại. Cursor và Factory chỉ có hook sau khi chạy [S2].

**Skill đi kèm (người viết đếm).** Thư mục `gitnexus/skills` có 12 skill: tám file skill đơn (guide, cli, exploring, debugging, impact-analysis, refactoring, pdg-query, taint-analysis) và bốn quy trình (plan, work, review, lfg) [S19].

**Tự kiểm chứng trong repo (nguồn: repo).** Thư mục `eval` chạy SWE-bench ở ba chế độ: `baseline` (grep, find, cat), `native` (thêm tool GitNexus) và `native_augment` (thêm làm giàu kết quả grep), chế độ cuối được khuyến nghị [S14]. `pr-swarm-review` gồm 7 persona chỉ đọc (người đếm 7 file trong thư mục `personas`) để rà soát PR [S16]. Bài này không chạy bộ đo nên không nêu con số kết quả nào.

## Quy mô và chất lượng

**Số dòng và số file (người viết đếm).** Đếm bằng `wc -l` trên mọi file `.ts` và `.tsx` của từng thư mục ở commit d8a256a: `gitnexus/test` có 501.873 dòng, `gitnexus/src` có 366.610 dòng, `gitnexus-web/src` có 23.866 dòng [S22] [S23]. Mã kiểm thử bằng khoảng 1,37 lần mã nguồn của gói chính (501.873 so với 366.610; phép chia là suy luận từ hai số đã đếm). Có 1.071 file `.ts` trong `gitnexus/src`, 905 file `*.test.ts` trong `test/unit` và 434 file trong `test/integration`, và 32 workflow GitHub Actions [S22] [S23] [S20].

**CI và phát hành (người viết đếm tên file).** Chất lượng: `ci-tests`, `ci-quality`, `ci-e2e`, `ci-report`. Bảo mật: `codeql`, `gitleaks`, `trivy`, `scorecard`, `dependency-review`, `workflow-lint`. Phát hành: `publish`, `docker`, `release-evaluation`. Tự động hoá: `pr-autofix`, `pr-labeler`, `triage-sweep`, `skill-sync`, `gitnexus-review-agent`, `claude` [S20].

**Tài liệu lệch mã (suy luận từ các số đã đối chiếu).** CHANGELOG.md dừng ở bản 1.5.3 (ngày 1/4/2026) trong khi gói là 1.6.12, nên không dùng nó để suy ra lịch sử phát hành [S21] [S13]. Tài liệu kiến trúc ghi 19 phase, 16 công cụ và 44 loại node, trong khi mã có 20 phase, 19 công cụ và 35 loại node [S3] [S9] [S6] [S10].

## Phản biện

**Điểm mạnh (suy luận).** Trung thực về độ chắc chắn: kết quả có `lower-bound`, `UNKNOWN`, cảnh báo cắt cụt, và không bịa route [S3]. Một đồ thị phục vụ cả MCP, CLI và web, với lược đồ và kiểu dùng chung [S3]. Hạ tầng kiểm thử và CI dày, và repo tự áp quy tắc cho agent bằng AGENTS.md, hook và skill [S4] [S20].

**Rủi ro và hạn chế (suy luận).** Giấy phép phi thương mại nên cần kiểm tra trước khi dùng trong doanh nghiệp [S8]. `serve` chưa có xác thực: mở công khai chỉ an toàn khi có proxy giữ token [S7]. Độ phủ khác nhau theo ngôn ngữ, và kết quả `impact` có thể chỉ là cận dưới [S1] [S3]. Cài đặt cần Node 22.18 trở lên [S13]. Tài liệu kiến trúc lệch mã ở vài con số [S3].

**Nên thử thế nào (suy luận).** Bắt đầu trên một repo nhỏ: chạy `analyze`, rồi `status`, `query` và `impact` [S1]. Dùng agent theo quy tắc của AGENTS.md: chạy `impact` trước khi sửa và `detect_changes` trước khi commit [S4]. Với repo lớn, theo dõi bộ nhớ khi lập chỉ mục [S7]. Cần nhóm repo hoặc review PR tự động thì xem bản Enterprise [S1].

## Điều cần nhớ

Bốn điều đáng mang theo. Một: GitNexus tính sẵn đồ thị để agent hỏi "ai gọi" và "ảnh hưởng gì" bằng một lời gọi, và kết quả luôn kèm độ tin cậy [S2] [S3]. Hai: mọi con số cấu trúc quan trọng trong bài (20 phase, 19 công cụ, 35 loại node, 33 loại quan hệ, 18 ngôn ngữ) đều lấy từ mã, và chúng lệch với tài liệu kiến trúc, nên khi hai nguồn mâu thuẫn hãy tin mã [S9] [S6] [S10] [S11] [S3]. Ba: giấy phép PolyForm Noncommercial không cho dùng thương mại nếu chưa có giấy phép riêng [S8]. Bốn: máy chủ `serve` chưa tự xác thực, nên đặt nó sau proxy có token trước khi mở ra mạng [S7] [S5].

## Lưu ý

Giới hạn nguồn: bài đọc bản sao nông (độ sâu 1) của repo ở commit d8a256a, ngày 24/10/2026, gói `gitnexus` 1.6.12. Người viết không mở trang GitHub của repo, nên không đọc số sao, số fork, số người đóng góp hay lịch sử issue: bài không có con số nào về mức độ phổ biến. Bài chưa chạy `analyze`, chưa chạy kiểm thử, chưa đo hiệu năng hay độ chính xác của phân giải; mọi mô tả hành vi là đọc mã và văn bản. Số tự báo của repo (248.612 symbol, 565.510 quan hệ, 918 luồng) lấy từ AGENTS.md và có thể đã cũ.

Về chính file này: văn bản được viết lại thành `report.md` ngày 31/10/2026 từ báo cáo A4 đã dựng trên Moda ngày 24/10/2026 (các file `gitnexus.pdf` và `gitnexus.pptx`). Khi viết lại, người viết đối chiếu lại các con số với bản clone và sửa một lỗi trên báo cáo A4: số dòng của `gitnexus/test` ban đầu là 501.503 vì chỉ đếm file `.ts` và bỏ file `.tsx`, còn các thư mục khác đếm cả hai loại; con số đúng theo cách đếm nhất quán là 501.873, và canvas, PDF, PPTX trong thư mục này đã được sửa theo. Báo cáo A4 là một tài liệu 14 trang khổ A4 dọc, không phải bộ slide 16:9, nên thư mục này không có `slides.json`. Giấy phép nêu trong bài lấy từ file LICENSE; bài không phải tư vấn pháp lý và không khuyến nghị cài đặt.

## Nguồn tham khảo

- [S1] abhigyanpatwari, README.md: giới thiệu, bắt đầu nhanh, sáu việc agent làm được, ngôn ngữ, bản Enterprise, giấy phép, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/README.md
- [S2] abhigyanpatwari, gitnexus/README.md: README của gói npm, 19 công cụ, mức hỗ trợ editor và hook, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/README.md
- [S3] abhigyanpatwari, ARCHITECTURE.md: luồng từ mã đến công cụ, pipeline, phân giải, lưu trữ, công cụ MCP, CFG và PDG, nhóm repo, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/ARCHITECTURE.md
- [S4] abhigyanpatwari, AGENTS.md: bố cục monorepo, quy tắc cho agent, số liệu tự báo của repo, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/AGENTS.md
- [S5] abhigyanpatwari, SECURITY.md: ranh giới bảo mật của serve và /api/mcp, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/SECURITY.md
- [S6] abhigyanpatwari, docs/mcp-reference.md: 19 công cụ MCP, resource, prompt, kiểm soát truy cập, ngân sách phản hồi, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/docs/mcp-reference.md
- [S7] abhigyanpatwari, docs/deployment.md: Docker, Render, proxy và token, chuỗi cung ứng, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/docs/deployment.md
- [S8] abhigyanpatwari, LICENSE: PolyForm Noncommercial 1.0.0, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/LICENSE
- [S9] abhigyanpatwari, gitnexus/src/core/ingestion/pipeline.ts: buildPhaseList đăng ký các phase, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/src/core/ingestion/pipeline.ts
- [S10] abhigyanpatwari, gitnexus-shared/src/lbug/schema-constants.ts: NODE_TABLES và REL_TYPES, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus-shared/src/lbug/schema-constants.ts
- [S11] abhigyanpatwari, gitnexus-shared/src/languages.ts: enum SupportedLanguages, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus-shared/src/languages.ts
- [S12] abhigyanpatwari, gitnexus/src/mcp/resources.ts: danh sách resource MCP, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/src/mcp/resources.ts
- [S13] abhigyanpatwari, gitnexus/package.json: phiên bản 1.6.12 và yêu cầu Node, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/package.json
- [S14] abhigyanpatwari, eval/README.md: ba chế độ đánh giá SWE-bench, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/eval/README.md
- [S15] abhigyanpatwari, gitnexus-web/package.json: các phụ thuộc của giao diện web, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus-web/package.json
- [S16] abhigyanpatwari, pr-swarm-review/README.md: bộ rà soát PR bằng các persona chỉ đọc, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/pr-swarm-review/README.md
- [S17] abhigyanpatwari, gitnexus/src/core/incremental/escalation-gate.ts: ngưỡng nâng ghi tăng dần thành ghi lại toàn bộ, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/src/core/incremental/escalation-gate.ts
- [S18] abhigyanpatwari, gitnexus/src/mcp/output-budget.ts: ước lượng 4 byte mỗi token cho maxTokens, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/src/mcp/output-budget.ts
- [S19] abhigyanpatwari, gitnexus/skills: thư mục 12 skill đi kèm gói npm, 2026, https://github.com/abhigyanpatwari/GitNexus/tree/d8a256a03a101a767dc4e1118913c679af740336/gitnexus/skills
- [S20] abhigyanpatwari, .github/workflows: 32 workflow CI, bảo mật, phát hành và tự động hoá, 2026, https://github.com/abhigyanpatwari/GitNexus/tree/d8a256a03a101a767dc4e1118913c679af740336/.github/workflows
- [S21] abhigyanpatwari, CHANGELOG.md: bản mới nhất được ghi là 1.5.3, 2026, https://github.com/abhigyanpatwari/GitNexus/blob/d8a256a03a101a767dc4e1118913c679af740336/CHANGELOG.md
- [S22] abhigyanpatwari, gitnexus: thư mục gói chính, nơi đếm src và test, 2026, https://github.com/abhigyanpatwari/GitNexus/tree/d8a256a03a101a767dc4e1118913c679af740336/gitnexus
- [S23] abhigyanpatwari, gitnexus-web/src: thư mục mã nguồn của giao diện web, nơi đếm số dòng, 2026, https://github.com/abhigyanpatwari/GitNexus/tree/d8a256a03a101a767dc4e1118913c679af740336/gitnexus-web/src
