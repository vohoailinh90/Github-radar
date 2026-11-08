---
id: R11
title: Firecrawl: API web cho agent, và phần nào thực sự mở
topic: ky-thuat
date: 2026-11-08
---
# Firecrawl: API web cho agent, và phần nào thực sự mở

## Tóm tắt

Repo này là gì, dùng thế nào, và cần cẩn thận ở đâu? README mô tả Firecrawl là "API để tìm kiếm, cào và tương tác với web ở quy mô lớn", "API ngữ cảnh cho các agent AI", mã nguồn mở và có bản dịch vụ lưu trữ sẵn [S1]. Về hình thức đây là một **monorepo**: `apps/api` là API và các worker, các thư mục `apps/*-sdk` là thư viện khách, cùng một dịch vụ Playwright, hàng đợi trên Postgres, Redis và một thư mục ví dụ [S3] [S7]. Cách dùng quen thuộc nhất là lấy khóa API ở dịch vụ lưu trữ, rồi gọi `search`, `scrape`, `crawl`, `map` hoặc `agent` qua REST hay SDK; cách thứ hai là tự lưu trữ bằng Docker Compose [S1] [S6].

Bài đọc repo theo bốn tầng. Tầng một là bề mặt: các endpoint công bố trong README và các route thật trong `routes/v2.ts` [S1] [S25]. Tầng hai là lõi: một lệnh scrape đi qua danh sách engine xếp theo chất lượng và thử lần lượt cho đến khi có kết quả [S10] [S11]. Tầng ba là vận hành: hàng đợi NuQ, Redis, RabbitMQ, Playwright, và những gì tệp `SELF_HOST.md` tự thừa nhận còn thiếu so với sản xuất [S6] [S7] [S15]. Tầng bốn là phản biện: "mở" đến đâu, giấy phép nào áp dụng cho phần nào, và lời hứa về `robots.txt` đúng cho lệnh nào [S1] [S2] [S13] [S14].

Mỗi khẳng định mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ một tệp ở commit `033f42f` (08/11/2026, nhánh mặc định). **Người viết đếm** là con số tính bằng lệnh trên bản đã tải; cách đếm nằm ở mục Lưu ý. **Suy luận** là nhận định của người viết, không phải điều repo tuyên bố. Người viết không chạy API, không cài SDK và không gọi dịch vụ lưu trữ nào: mọi hành vi là "đọc mã, chưa chạy". Các con số marketing trong README (độ phủ web, độ trễ) cũng chỉ là lời của README.

Ba ý đáng mang theo. Thứ nhất, lõi của API không phải một công cụ cào mà là một **bộ điều phối engine**: 16 loại engine, mỗi loại có điểm chất lượng và tập tính năng hỗ trợ, và danh sách thực dùng tùy cấu hình đang bật [S10]. Thứ hai, bản tự lưu trữ mặc định **không có xác thực** và không có volume lưu trữ cho hàng đợi; tệp hướng dẫn tự lưu trữ nói thẳng điều đó [S6] [S7]. Thứ ba, repo mang nhiều giấy phép: AGPL-3.0 ở gốc, MIT ở các SDK, và ISC ở vài `package.json` và skill, nên "mã nguồn mở" cần đọc từng thư mục [S2] [S9] [S19] [S23].

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Monorepo của API web cho agent: tìm kiếm, cào, tương tác, thu thập, bản đồ URL, agent tự tìm dữ liệu | Nguồn: repo [S1] [S3] |
| Quy mô | 2.219 tệp; 1.943 tệp trong `apps/`; `apps/api` có 1.127 tệp, trong đó 1.048 tệp `.ts` | Người viết đếm |
| Thư mục con của `apps/` | 17: `api`, 9 thư mục SDK, `go-html-to-md-service`, `nuq-postgres`, `playwright-service-ts`, `redis`, `siem`, `test-site`, `test-suite` | Người viết đếm [S3] |
| Kiểm thử | 438 tệp `*.test.ts` trong `apps/api`; 116 tệp trong bộ `snips` | Người viết đếm [S3] [S5] |
| Ví dụ | 194 tệp trong `examples/`, 58 thư mục ví dụ | Người viết đếm |
| CI | 33 tệp workflow trong `.github/workflows` | Người viết đếm |
| SDK nêu trong README | Python, Node.js, Go, Java, Elixir, Rust, Ruby, .NET, PHP (9 ngôn ngữ) | Nguồn: repo [S1] |
| Phiên bản SDK JS | `@mendable/firecrawl-js` 4.53.0, giấy phép MIT | Nguồn: repo [S19] |
| Giấy phép chính | AGPL-3.0 (tệp `LICENSE`, 35.064 byte); SDK và một số thành phần giao diện MIT theo README | Nguồn: repo [S1] [S2] |
| Số sao | Bài này không nêu: nguồn duy nhất là tệp ở commit đã ghim | Giới hạn của bài |

## Bề mặt API: các thao tác trong README và route thật

README gọi ba **endpoint cốt lõi** là Search, Scrape và Interact, và sáu thứ khác là Parse, Agent, Crawl, Map, Batch Scrape và Monitor [S1].

- **Search** tìm trên web và trả nội dung đầy đủ của kết quả, với `limit` tùy chọn [S1].
- **Scrape** biến một URL thành markdown, HTML, ảnh chụp hay JSON có cấu trúc; README minh họa cả bằng Python, Node, cURL và CLI [S1].
- **Interact** là thao tác hai bước: cào một trang, lấy mã scrape, rồi ra lệnh tiếp bằng lời hoặc mã (ví dụ tìm "mechanical keyboard" rồi bấm kết quả đầu tiên); phản hồi có trường `liveViewUrl` [S1]. Trong `routes/v2.ts` có route `/scrape/:jobId/interact` (hai phương thức POST và DELETE) và cặp `/browser`, `/interact` cho phiên trình duyệt [S25].
- **Agent** được mô tả là "cách dễ nhất để lấy dữ liệu từ web": mô tả điều cần, agent tự tìm, điều hướng và lấy, không cần cung cấp URL; README nói nó là bản tiến hóa của endpoint `/extract` [S1]. Có ba mức công sức `low`, `medium`, `high`; README nói mọi mức đều chạy mô hình `spark-2`, mức chỉ đổi ngân sách suy luận, còn tên cũ `spark-1-pro` và `spark-1-mini` vẫn được chấp nhận nhưng đã lỗi thời và cũng chạy `spark-2` [S1].
- **Crawl** thu thập cả website bằng một yêu cầu, trả mã công việc để hỏi trạng thái; SDK tự thăm dò đến khi xong [S1].
- **Map** liệt kê mọi URL của một trang, có tùy chọn `search` để xếp URL theo độ liên quan [S1].
- **Batch Scrape** cào nhiều URL bất đồng bộ [S1].

Suy luận: README liệt kê khoảng chục thao tác, nhưng mã máy chủ rộng hơn nhiều. Người viết đếm: `apps/api/src/routes/v2.ts` có 78 khai báo route (`get`, `post`, `put`, `delete`) [S25]. Ngoài các thao tác trên còn có `/parse` và tải tệp lên, `/extract`, `/monitor` (kể cả xác nhận email), truy vấn lượng dùng tín dụng và token theo thời gian, hàng đợi của nhóm, cấu hình SIEM và "bảo vệ mối đe dọa" (có đường dẫn liên quan Zscaler), và các route Slack [S25]. Nghĩa là phần lớn bề mặt dành cho bản dịch vụ lưu trữ nằm ngay trong cây mã này.

Về điều khiển bên trong, thư mục `controllers/` chia theo phiên bản API: người viết đếm 53 tệp ở `v2`, 27 ở `v1` và 7 ở `v0` (đếm theo `ls`, mỗi mục là một tệp hoặc thư mục con). Repo vẫn mang cả `openapi-v0.json`, `v1-openapi.json` và `openapi.json` ở `apps/api` [S3].

## Một lệnh scrape đi qua đâu

Tài liệu của mô-đun `scrapeURL` vẽ vòng lặp bằng sơ đồ mermaid: dựng danh sách dự phòng (`buildFallbackList`), chạy một engine, phân tích sang markdown, hỏi "scrape có thành công không?"; nếu không thì thử engine tiếp theo; hết engine thì báo `NoEnginesLeftError` [S11]. Cùng tài liệu ghi những khác biệt so với bản cũ: PDF được chuyển thẳng sang markdown bằng LlamaParse, DOCX sang HTML bằng mammoth, và dùng API schema JSON mới của OpenAI để lỗi schema khi trích xuất "gần như không còn" [S11]. Suy luận: tài liệu này hơi cũ so với mã (nó còn nhắc `v1` và `WebScraperDataProvider`), nên coi mã là nguồn chính.

Mã thật nằm ở `engines/index.ts` (1.144 dòng, người viết đếm) [S10]:

- Kiểu `Engine` có **16 giá trị** (người viết đếm): `exchange`, bốn biến thể `fire-engine` trình duyệt (`chrome-cdp`, cùng bản `retry`, cùng bản `stealth`), hai biến thể `fire-engine` kiểu `tlsclient`, `playwright`, `fetch`, `pdf`, `document`, `image`, `index`, `index;documents`, `wikipedia` và `x-twitter` [S10].
- Danh sách engine thực sự bật phụ thuộc cấu hình. `fire-engine` chỉ vào danh sách khi biến `FIRE_ENGINE_BETA_URL` có giá trị; `playwright` chỉ khi có `PLAYWRIGHT_MICROSERVICE_URL`; `index` chỉ khi có `INDEX_DATABASE_URL`; `wikipedia` cần tài khoản doanh nghiệp của Wikipedia; `x-twitter` cần khóa XAI hoặc chế độ xác thực bằng cơ sở dữ liệu; còn `fetch`, `pdf` và `document` luôn có, và `image` chỉ khi có địa chỉ dịch vụ FirePDF [S10] [S16] [S17].
- Mỗi engine có một **điểm chất lượng** và một bảng cờ tính năng nó hỗ trợ [S10]. Các điểm đọc được trong mã: `x-twitter` 1500, `exchange` 2000, `index` 1000, `wikipedia` 500, `fire-engine;chrome-cdp` 50 (bản `retry` 45), `playwright` 20, `fire-engine;tlsclient` 10, `fetch` 5; các engine đặc chủng (`pdf`, `document`, `image`, và các biến thể `stealth`) mang điểm âm. Mã ghi chú rằng điểm âm dành cho engine đặc chủng như PDF, DOCX và proxy ẩn danh [S10].
- Có 17 cờ tính năng, mỗi cờ có trọng số: `actions` 20, `waitFor` 1, `screenshot` 10, `pdf`/`document`/`image`/`audio`/`video` 100, `atsv` và `useFastMode` 90, `stealthProxy` 20, `branding` 20, và vài cờ 10 [S10]. Một engine được chọn nếu tổng trọng số cờ nó hỗ trợ đạt ít nhất **một nửa** tổng trọng số cờ của yêu cầu [S10].
- Khi người dùng chủ động xin proxy ẩn danh (`stealth` hoặc `enhanced`), danh sách bị thu về các engine hỗ trợ nó; mã có chú thích rằng nếu không engine nào đủ khả năng, danh sách ban đầu được giữ để scrape không hỏng hẳn, ví dụ "tự lưu trữ không có fire-engine" [S10]. Suy luận: trên bản tự lưu trữ, yêu cầu `stealth` có thể lặng lẽ không được thực hiện; đọc mã, chưa chạy.
- Một tệp riêng cho phép **ép engine theo miền** bằng biến `FORCED_ENGINE_DOMAINS` (đối tượng JSON ánh xạ mẫu miền sang một engine hoặc danh sách engine thử lần lượt); khớp chính xác bao cả miền con, mẫu `*.` chỉ khớp miền con [S12].

## Hàng đợi, dịch vụ và tự lưu trữ

Tệp `docker-compose.yaml` ở gốc dựng các dịch vụ sau (người viết đếm từ khai báo): `api`, `playwright-service`, `redis`, `rabbitmq`, `nuq-postgres`, `foundationdb` và `foundationdb-init` [S7]. `SELF_HOST.md` nói rõ ở bản này chỉ API mở cổng ra máy chủ, mặc định cổng `3002` [S6]. Dịch vụ `api` chạy lệnh `node dist/src/harness.js --start-docker`, giới hạn 4 CPU và 8 GB bộ nhớ trong cấu hình Compose, và phụ thuộc Redis, Playwright, RabbitMQ (phải khỏe) và Postgres của NuQ (không bắt buộc khi dùng FoundationDB) [S7].

**NuQ** là hàng đợi công việc của Firecrawl. Tệp `nuq.ts` (1.783 dòng, người viết đếm) mở kết nối nhóm tới Postgres qua `NUQ_DATABASE_URL`, dùng RabbitMQ (thư viện `amqplib`) và Redis, và định nghĩa trạng thái công việc `queued`, `active`, `completed`, `failed`, `backlog`, cùng các trường ưu tiên, `ownerId` và `groupId` [S15]. Biến `NUQ_BACKEND` nhận `pg` hoặc `fdb` [S16]. `SELF_HOST.md` khuyên giữ Postgres trừ khi bạn chủ ý chọn FoundationDB và sẵn sàng vận hành nó [S6]. Tệp `package.json` của API định nghĩa riêng nhiều worker: `nuq-worker`, `nuq-fdb-worker`, `nuq-prefetch-worker`, `nuq-reconciler-worker`, `extract-worker`, `index-worker`, `zdr-worker` và `cclog-worker` [S9].

**Playwright** chạy như một dịch vụ riêng (`playwright-scraper-api`, Node từ 22.13, các phụ thuộc `express`, `playwright`, `proxy-chain` và `ipaddr.js`) [S18]. Compose đặt `PLAYWRIGHT_MICROSERVICE_URL` mặc định trỏ tới dịch vụ này [S7]. Suy luận: do `fire-engine` không có biến nào trong khối môi trường chung của Compose, bản Compose mặc định chạy engine `playwright`, rồi `fetch`, `pdf`, `document` (xem mục sau), khớp với dòng "Scraping" trong `SELF_HOST.md` [S6] [S7] [S10].

`SELF_HOST.md` khuyên giữ chuyến chạy đầu thật đơn giản và liệt kê mặc định: dùng đúng một thẻ phát hành thay vì `main`; `USE_DB_AUTHENTICATION=false`; hàng đợi NuQ trên Postgres; scrape bằng Playwright đi kèm và `fetch` dự phòng; không nhà cung cấp mô hình cho tính năng AI; giao diện quản trị hàng đợi tắt [S6]. Những lưu ý trước khi lên sản xuất: API mặc định **không xác thực**, cần thiết kế xác thực, TLS và chính sách mạng trước khi ra khỏi mạng tin cậy; Compose gốc **không định nghĩa volume lưu trữ** cho Postgres của NuQ, Redis và RabbitMQ; không công bố cổng của các phụ thuộc; và tệp Compose là điểm khởi đầu, không phải kiến trúc sản xuất [S6]. Người viết đối chiếu: khối `volumes` của Compose chỉ khai `fdb-data` và `fdb-cluster-file`, khớp với lời tệp tự lưu trữ [S7].

Các tuyến quản trị: tuyến có khóa tồn tại khi đặt `BULL_AUTH_KEY`; bộ lắng nghe nội bộ chạy khi đặt `ADMIN_INTERNAL_PORT` và **không cần khóa**; bảng trong `SELF_HOST.md` liệt kê năm tuyến xác thực bằng tiêu đề và nhiều tuyến nội bộ như giao diện hàng đợi, số liệu, `GET /admin/precrawl` (đưa một lượt tiền thu thập vào hàng) và `POST /admin/fsearch` (chạy một lượt tìm kiếm) [S6]. Tài liệu nhắc: ai tới được cổng nội bộ là dùng được các tuyến đó, nên đừng bao giờ công bố cổng này [S6].

## SDK, CLI, MCP và skill cho agent

README liệt kê chín SDK, mỗi cái có đoạn mã mẫu cho scrape, agent (trừ vài ngôn ngữ), crawl và search [S1]. Tên và cách cài lấy từ README: Python `pip install firecrawl`, Node `npm install firecrawl`, Go `go get` từ chính repo, Java qua Maven hoặc Gradle với JitPack, Elixir `{:firecrawl, "~> 1.0"}`, Rust `firecrawl = "2"`, Ruby `gem install firecrawl-sdk`, .NET `dotnet add package firecrawl-sdk` và PHP [S1]. Người viết không cài cái nào.

Repo gốc kèm hai thư mục con Go dạng submodule (`firecrawl-go` và `firecrawl-go-examples`) khai trong `.gitmodules` [S8], trong khi README hướng dẫn cài Go từ đường dẫn `apps/go-sdk` của chính monorepo [S1]. Suy luận: SDK Go có cả mã trong cây chính lẫn mã ở các submodule; người dùng nên xem README của từng nơi.

Phần "Power Your Agent" có ba đường. **Skill** cài bằng một lệnh `npx -y firecrawl-cli@latest init --all --browser`, README nói hoạt động với Claude Code, Antigravity, OpenCode và các agent khác [S1]. **MCP** dùng cấu hình `firecrawl-mcp` chạy bằng `npx`, truyền khóa qua biến `FIRECRAWL_API_KEY` [S1]. **Agent Onboarding** là một dòng `curl` lấy tệp `SKILL.md` để một agent đăng ký tài khoản, lấy khóa và bắt đầu [S1]. Suy luận: đoạn cuối là một mẫu đáng chú ý, vì README viết thẳng cho agent đọc ("Bạn có phải agent AI không?").

Thư mục `skills/` là nguồn gốc của các **skill dựng** (tích hợp Firecrawl vào mã sản phẩm): CI phản chiếu chúng sang kho `firecrawl/skills`, còn skill CLI và skill quy trình ở kho khác; thư mục có năm skill và một số tệp tham chiếu [S22]. Skill `firecrawl-build` nói nó dùng khi tính năng cần dữ liệu web trong mã ứng dụng, và dặn chọn endpoint hẹp nhất phù hợp: `/scrape` cho một URL đã biết, `/search` khi chỉ có truy vấn, `/interact` khi phải bấm hay điền biểu mẫu; nó khai hai biến đầu vào là `FIRECRAWL_API_KEY` (bắt buộc) và `FIRECRAWL_API_URL` (tùy chọn, cho bản tự lưu trữ) [S23]. Tệp này ghi giấy phép **ISC**, khác với giấy phép AGPL của gốc [S2] [S23].

## Mã nguồn mở và bản cloud

README có mục "Open Source vs Cloud": Firecrawl "mở nguồn theo AGPL-3.0", bản cloud ở trang dịch vụ "có thêm tính năng", kèm một hình minh họa [S1]. Người viết đọc hình: nhóm "Open Source" gồm Scrape, Crawl, LLM Extract, Map, định dạng sẵn cho LLM và SDK; nhóm "Cloud" thêm chống bot (bypass bot protections), xoay vòng proxy, bảng điều khiển, Actions, duyệt không trình duyệt và duyệt có trình duyệt, và tính năng doanh nghiệp [S24].

Đối chiếu với mã: `fire-engine` (nơi các engine `chrome-cdp`, `tlsclient` và biến thể `stealth` chạy) chỉ được dùng khi có biến `FIRE_ENGINE_BETA_URL`, và hàm kiểm tra chỉ so địa chỉ có khác rỗng hay không [S17]. Người viết không thấy thư mục nào của dịch vụ `fire-engine` trong cây `apps/` (17 thư mục con, xem Hồ sơ nhanh); trong `engines/fire-engine/` chỉ có phía khách (`scrape.ts`, `checkStatus.ts`, `delete.ts`...) [S3] [S10]. Suy luận: phần cào mạnh nhất, phục vụ chống bot và proxy, là dịch vụ nằm ngoài repo; khớp với hình và với lời `SELF_HOST.md` rằng phải "kết nối và cấu hình một engine riêng như Fire-engine chỉ khi cần" [S6] [S24]. Cũng suy luận: các route `agent`, `monitor`, SIEM và Slack nằm trong cây mã, nên "bản cloud có thêm tính năng" không có nghĩa tính năng đó vắng trong mã nguồn; có thể chúng cần dịch vụ phụ trợ (cơ sở dữ liệu xác thực, thanh toán) mà bản tự lưu trữ không có [S6] [S16] [S25].

## Phản biện

1. **Một repo, nhiều giấy phép.** Tệp `LICENSE` gốc là AGPL-3.0 [S2]; README nói SDK và một số thành phần giao diện là MIT và dặn xem tệp `LICENSE` trong từng thư mục [S1]. Người viết đếm: tìm thấy tệp `LICENSE` ở `apps/elixir-sdk`, `apps/js-sdk`, `apps/python-sdk` và `apps/ruby-sdk`, mỗi tệp là MIT (SDK Python còn khai MIT trong `pyproject.toml`); thư mục `apps/js-sdk/firecrawl` cũng có một tệp nữa [S20] [S21]. Trong khi đó `apps/api/package.json` ghi `"license": "ISC"`, `apps/playwright-service-ts/package.json` cũng ghi ISC, và skill `firecrawl-build` ghi `license: ISC` [S9] [S18] [S23]. Báo cáo không chọn bên: hai tệp trong cùng repo ghi hai giấy phép khác nhau cho cùng mã API. Với AGPL-3.0, việc chạy bản sửa đổi như một dịch vụ mạng có nghĩa vụ riêng; bài này không phải tư vấn pháp lý.
2. **Lời hứa về `robots.txt` đúng khác nhau theo thao tác.** README: "Theo mặc định Firecrawl tôn trọng chỉ thị `robots.txt`" và người dùng phải tự tuân thủ chính sách của trang [S1]. Mã: trong tùy chọn thu thập (`crawlerOptions`), `ignoreRobotsTxt` có mặc định `false`, và lớp crawler cũng đặt mặc định `false`, nên **crawl** tôn trọng robots theo mặc định [S14] [S26]. Nhưng với **scrape một URL**, hàm `shouldCheckRobots` trả `false` khi đặt `lockdown`, trả `true` nếu chế độ an toàn của tổ chức bật `enforceRobots`, và còn lại chỉ trả `true` khi cờ nhóm `checkRobotsOnScrape` bật [S13]. Trong luồng scrape, bước kiểm tra nằm trong khối điều kiện `if (shouldCheckRobots(...))`, và khi tải `robots.txt` thất bại, nhật ký ghi "Failed to fetch robots.txt, allowing scrape" rồi cho phép scrape [S27]. Suy luận: với scrape đơn lẻ, mặc định có thể là không kiểm robots, trừ khi tổ chức bật cờ; đọc mã, chưa chạy, và người viết không kiểm cờ nhóm mặc định ở dịch vụ lưu trữ.
3. **Con số trong README là lời của README.** "Phủ 96% web", "độ trễ P95 3,4 giây trên hàng triệu trang" là phần giới thiệu; người viết không có phép đo nào và không mở các liên kết benchmark [S1].
4. **Tài liệu bên trong lệch nhau.** `CLAUDE.md` và `AGENTS.md` mô tả cùng quy trình viết test E2E (`snips`) và chạy bằng `pnpm harness`; tệp `CLAUDE.md` có thêm một đoạn cấm vượt kiểm tra `knip`, còn `AGENTS.md` thì không [S3] [S4]. Suy luận: hai tệp dành cho hai công cụ agent nên dễ lệch; người đọc dùng tệp nào cần để ý. README của `scrapeURL` cũng cũ hơn mã (xem trên) [S11].
5. **README ghi cách cài khác nhau cho từng nơi.** README hướng dẫn chạy tại chỗ qua `CONTRIBUTING.md`, còn `CONTRIBUTING.md` nói "phát triển" và "tự lưu trữ" là hai đường khác nhau, dùng hai tệp môi trường khác nhau và đừng chép tệp này sang tệp kia [S1] [S5]. `SELF_HOST.md` lặp lại: tệp `.env` ở gốc chỉ ghi đè các biến mà `docker-compose.yaml` tham chiếu, không dùng `apps/api/.env.example` thay cho nó [S6]. Dễ nhầm với người mới.
6. **Mặc định tự lưu trữ cần được xem như bản thử.** Mật khẩu Postgres mặc định trong Compose là `postgres`, API không xác thực, không volume cho hàng đợi [S6] [S7]. Tệp `SELF_HOST.md` đã dặn "điểm khởi đầu, không phải kiến trúc sản xuất" [S6].
7. **Độ phức tạp.** Một API kiêm dịch vụ lưu trữ, với hơn một nghìn tệp `.ts` trong `apps/api`, 8 worker, hai backend hàng đợi và nhiều tuyến quản lý nhóm, là một hệ thống lớn để tự vận hành [S3] [S9] [S25]. Người viết không đo mức tiêu thụ tài nguyên thực tế; chỉ biết Compose đặt trần 4 CPU và 8 GB cho dịch vụ `api` [S7].

## Điều cần nhớ

- Firecrawl là một **monorepo** API web cho agent: `search`, `scrape`, `interact`, `agent`, `crawl`, `map`, `batch scrape` và nhiều route phụ, kèm 9 SDK [S1] [S3] [S25].
- Lõi là **bộ điều phối 16 engine** theo điểm chất lượng và cờ tính năng; engine mạnh nhất cho chống bot (`fire-engine`) cần một dịch vụ ngoài repo [S10] [S17].
- Bản tự lưu trữ mặc định chạy Playwright và `fetch`, **không xác thực** và không volume cho hàng đợi; tệp hướng dẫn tự thừa nhận điều này [S6] [S7].
- **Giấy phép nhiều lớp**: AGPL-3.0 ở gốc, MIT ở SDK, ISC ở `package.json` và skill; cần đọc theo thư mục [S2] [S9] [S19] [S23].
- Lời hứa tôn trọng `robots.txt` rõ nhất ở **crawl**; với scrape đơn lẻ thì phụ thuộc cờ nhóm [S13] [S14].
- Mọi con số marketing là của README; bài này đọc mã và chưa chạy [S1].

## Lưu ý

- **Phạm vi đọc.** Bản clone nông (`--depth 1`) ở commit `033f42f87c270900a01fc027903fc718b9870d02` (08/11/2026). Với 2.219 tệp, người viết đọc trọn README, `LICENSE` (phần đầu), `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SELF_HOST.md`, `docker-compose.yaml`, `.gitmodules`, `README.md` của `scrapeURL`, `ENGINE_FORCING.md`, `shouldCheckRobots.ts` và `available.ts`; đọc một phần `engines/index.ts`, `nuq.ts`, `config.ts`, `types.ts`, `routes/v2.ts`, `scrapeURL/index.ts` và `crawler.ts` (các đoạn nêu trong bài); chỉ liệt kê tên tệp và đếm với phần còn lại, gồm mã của các SDK, `examples/` và các bài test. Bài không nêu số sao, số fork, issue hay lịch sử phát hành, và không mở các liên kết ra ngoài repo.
- **Chưa chạy.** Người viết không chạy API, worker, Compose, test, SDK hay CLI, không gọi dịch vụ lưu trữ; mọi hành vi là "đọc mã, chưa chạy". Phản hồi mẫu trong README là ví dụ minh họa, không phải kết quả đo.
- **Cách đếm.** Số tệp, tệp theo thư mục và theo phần mở rộng: `git ls-files`. Tệp test: tên kết thúc `.test.ts` dưới `apps/api`. Số route: các dòng bắt đầu bằng `v2Router.get(`, `.post(`, `.put(` hoặc `.delete(` trong `routes/v2.ts`. Số tệp controller: liệt kê thư mục `controllers/v0`, `v1`, `v2`. Số dòng: đếm dòng của từng tệp. Giá trị `Engine` và điểm chất lượng: đọc từ `engines/index.ts`. Hình `open-source-cloud.png` được xem trực tiếp.
- **Giấy phép.** `LICENSE` gốc là GNU Affero General Public License phiên bản 3; README nói SDK và một số thành phần giao diện là MIT; các thư mục con nêu ở mục Phản biện ghi MIT hoặc ISC. Người viết không đối chiếu từng thư mục.
- **Trích dẫn.** Các câu trong ngoặc kép là bản dịch từ README, tệp hướng dẫn hoặc chú thích mã; các chuỗi nhật ký giữ nguyên tiếng Anh. Người viết không kiểm các số liệu hiệu năng hay tuyên bố độ phủ.
- **Tính chất.** Đây là tài liệu hỗ trợ đọc repo, không phải khuyến nghị cài đặt, tự lưu trữ hay cào web, cũng không phải tư vấn pháp lý. Nội dung các tệp skill và `CLAUDE.md` là chỉ dẫn cho agent; trong bài này nó chỉ là đối tượng để mô tả.

## Nguồn tham khảo

- [S1] [firecrawl, README.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/README.md): giới thiệu, endpoint, SDK, agent, mở và cloud, giấy phép, 2026
- [S2] [firecrawl, LICENSE](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/LICENSE): GNU Affero General Public License v3, 2026
- [S3] [firecrawl, CLAUDE.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/CLAUDE.md): cấu trúc monorepo và quy trình viết test cho API, 2026
- [S4] [firecrawl, AGENTS.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/AGENTS.md): bản chỉ dẫn agent song song với CLAUDE.md, 2026
- [S5] [firecrawl, CONTRIBUTING.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/CONTRIBUTING.md): quy trình đóng góp và chạy test bằng harness, 2026
- [S6] [firecrawl, SELF_HOST.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/SELF_HOST.md): hướng dẫn tự lưu trữ, mặc định, rủi ro trước sản xuất, tuyến quản trị, 2026
- [S7] [firecrawl, docker-compose.yaml](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/docker-compose.yaml): các dịch vụ, biến môi trường và volume của bản Compose, 2026
- [S8] [firecrawl, .gitmodules](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/.gitmodules): hai submodule của SDK Go, 2026
- [S9] [firecrawl, apps/api/package.json](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/package.json): lệnh chạy, worker và giấy phép khai báo của API, 2026
- [S10] [firecrawl, apps/api/src/scraper/scrapeURL/engines/index.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/scrapeURL/engines/index.ts): kiểu Engine, điểm chất lượng, cờ tính năng, chọn engine, 2026
- [S11] [firecrawl, apps/api/src/scraper/scrapeURL/README.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/scrapeURL/README.md): sơ đồ luồng scrapeURL và khác biệt so với bản cũ, 2026
- [S12] [firecrawl, apps/api/src/scraper/WebScraper/utils/ENGINE_FORCING.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/WebScraper/utils/ENGINE_FORCING.md): ép engine theo miền, 2026
- [S13] [firecrawl, apps/api/src/scraper/scrapeURL/shouldCheckRobots.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/scrapeURL/shouldCheckRobots.ts): khi nào scrape kiểm robots.txt, 2026
- [S14] [firecrawl, apps/api/src/controllers/v2/types.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/controllers/v2/types.ts): schema tùy chọn thu thập, mặc định ignoreRobotsTxt, 2026
- [S15] [firecrawl, apps/api/src/services/worker/nuq.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/services/worker/nuq.ts): hàng đợi NuQ trên Postgres, RabbitMQ và Redis, 2026
- [S16] [firecrawl, apps/api/src/config.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/config.ts): các biến cấu hình của API, 2026
- [S17] [firecrawl, apps/api/src/scraper/scrapeURL/engines/fire-engine/available.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/scrapeURL/engines/fire-engine/available.ts): điều kiện bật fire-engine, 2026
- [S18] [firecrawl, apps/playwright-service-ts/package.json](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/playwright-service-ts/package.json): dịch vụ Playwright, phụ thuộc và giấy phép khai báo, 2026
- [S19] [firecrawl, apps/js-sdk/firecrawl/package.json](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/js-sdk/firecrawl/package.json): SDK Node, phiên bản và giấy phép MIT, 2026
- [S20] [firecrawl, apps/python-sdk/pyproject.toml](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/python-sdk/pyproject.toml): SDK Python, tên gói firecrawl-py và giấy phép MIT, 2026
- [S21] [firecrawl, apps/js-sdk/LICENSE](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/js-sdk/LICENSE): giấy phép MIT của SDK JS, 2026
- [S22] [firecrawl, skills/README.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/skills/README.md): nguồn gốc các skill dựng và cách chúng được phản chiếu, 2026
- [S23] [firecrawl, skills/firecrawl-build/SKILL.md](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/skills/firecrawl-build/SKILL.md): skill tích hợp Firecrawl vào mã sản phẩm, giấy phép ISC, 2026
- [S24] [firecrawl, img/open-source-cloud.png](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/img/open-source-cloud.png): hình so sánh tính năng mã nguồn mở và cloud, 2026
- [S25] [firecrawl, apps/api/src/routes/v2.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/routes/v2.ts): các route của API v2, 2026
- [S26] [firecrawl, apps/api/src/scraper/WebScraper/crawler.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/WebScraper/crawler.ts): lớp crawler, mặc định ignoreRobotsTxt, 2026
- [S27] [firecrawl, apps/api/src/scraper/scrapeURL/index.ts](https://github.com/firecrawl/firecrawl/blob/033f42f87c270900a01fc027903fc718b9870d02/apps/api/src/scraper/scrapeURL/index.ts): luồng scrape, bước kiểm robots.txt, 2026
