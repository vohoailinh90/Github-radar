# Plan: viết bài cho "Top 30 Claude Code Plugins" và thử báo cáo Moda do Codex làm (T0, claude lane)

Yêu cầu (chủ repo, 2026-10-25): lên kế hoạch viết bài cho tất cả repo trong ảnh *Top 30 Claude Code Plugins* (Charlie Hills, số sao đọc
ngày 23/10/2026), kiểm repo nào đã làm rồi, và thử một pilot: Claude mở PR và viết yêu cầu để Codex dựng báo cáo bằng Moda.
Chủ repo dặn thêm: việc Moda phải tự chủ, không hỏi lại từng bước (yêu cầu cho Codex ghi điều này).

Routing: dimensions ambiguity 1, scope 0, architecture 0, dependencies 0, risk 0, verification 0 = 1 -> T0, no signals, `main_session`,
no agent (`python3 scripts/route.py --dimensions 1,0,0,0,0,0`). The change is three documentation and data files, no code, no test.

Dữ liệu nằm ở [`top30-claude-plugins.json`](top30-claude-plugins.json); mọi bảng dưới đây được sinh từ file đó.

## 1. Hiện trạng: 5 repo đã có bài, 25 repo chưa

5 trong 30 mục của ảnh đã có bài học trong `digests/` (bài do radar viết, tiếng Việt):

| Mục trong ảnh | Repo | Sao (ảnh) | Bài | Ngày quét |
|---|---|---|---|---|
| ECC | `affaan-m/ECC` | 287k | `digests/2026-10-21/ecc/vi.md` | 2026-10-21 |
| REA | `morluto/rea` | 371k | `digests/2026-10-17-5/rea/vi.md` | 2026-10-17 |
| Agent Reach | `Panniantong/Agent-Reach` | 101k | `digests/2026-10-12/agent-reach/vi.md` | 2026-10-12 |
| UI UX Pro Max | `nextlevelbuilder/ui-ux-pro-max-skill` | 139k | `digests/2026-10-16-4/ui-ux-pro-max-skill/vi.md` | 2026-10-16 |
| Impeccable | `pbakaus/impeccable` | 85k | `digests/2026-10-16-4/impeccable/vi.md` | 2026-10-16 |

Cách kiểm (lặp lại được): đối chiếu từng mục của ảnh với `state/seen.json` (26 repo đã viết), `digests/INDEX.md` và các thư mục
`digests/*/*/`, rồi với `state/stars.json` (331 repo radar từng thấy), tất cả ở `main` @ `568274d`. Không mục nào trong 25 repo còn lại
có trong `seen.json`, `digests/`, `export/studio/` hay `docs/`. Tám repo (`ponytail`, `graphify`, `career-ops`, `claude-mem`, `headroom`,
`taste-skill`, `archify`, `i-have-adhd`) đã nằm trong `state/stars.json` với số sao khớp ảnh nhưng chưa từng được chọn; tên của chúng
được xác nhận bằng số sao. 17 repo còn lại có tên owner/repo được xác nhận là tồn tại bằng `git ls-remote`, **chưa** so số sao với ảnh.

Cần xác minh một chỗ: ảnh ghi REA 371k sao, còn radar đo `morluto/rea` được 293.881 sao ngày 17/10/2026 (điểm đo duy nhất). Mô tả trong
ảnh ("Shows how any app really works") khớp bài đã viết, nhưng mức tăng 77.000 sao trong sáu ngày không khớp nhịp của các repo khác
(khoảng 1.000 sao mỗi ngày), nên cần xem lại đó có đúng là một repo không. Chưa quyết định gì dựa trên điều này.

## 2. 25 repo còn lại, chia năm đợt theo nhóm của ảnh

Số liệu cột Giấy phép, README, File lấy bằng partial clone công khai ngày 2026-10-25 (`git clone --depth 1 --filter=blob:none --no-checkout`,
`git ls-tree`, `git cat-file`; chỉ đọc, không chạy gì). Giấy phép là chữ đọc từ file LICENSE, **không phải** trường `license` của GitHub mà radar dùng.
Mỗi repo ghim commit lúc đo trong file JSON (`probe_commit`).

### Đợt 1: Viết code như dân senior (5 repo)

| Mục trong ảnh | Repo | Sao (ảnh) | Giấy phép (đọc từ LICENSE) | README (byte) | File | Cờ | Giữ |
|---|---|---|---|---|---|---|---|
| Superpowers | `obra/superpowers` | 304k | MIT | 14.847 | 231 | stars-unverified |  |
| Matt Pocock Skills | `mattpocock/skills` | 301k | MIT | 16.461 | 191 | stars-unverified |  |
| Agent Skills | `addyosmani/agent-skills` | 109k | MIT | 25.930 | 217 | stars-unverified |  |
| Ponytail | `DietrichGebert/ponytail` | 174k | MIT | 14.578 | 214 | - |  |
| Karpathy Skills | `forrestchang/andrej-karpathy-skills` (cùng commit với `multica-ai/andrej-karpathy-skills`) | 222k | không có file LICENSE | 6.198 | 9 | license-unclear, stars-unverified | **giữ** |

### Đợt 2: Nghiên cứu và hiểu (4 repo)

| Mục trong ảnh | Repo | Sao (ảnh) | Giấy phép (đọc từ LICENSE) | README (byte) | File | Cờ | Giữ |
|---|---|---|---|---|---|---|---|
| Graphify | `Graphify-Labs/graphify` | 133k | Apache-2.0 | 36.226 | 1.101 | - |  |
| Understand Anything | `Lum1104/Understand-Anything` | 87k | MIT | 20.607 | 521 | stars-unverified |  |
| Career Ops | `career-ops-hq/career-ops` | 77k | MIT | 47.581 | 2.674 | readme-over-limit |  |
| Last 30 Days | `mvanhorn/last30days-skill` | 65k | MIT | 31.812 | 594 | stars-unverified |  |

### Đợt 3: Dự án lớn, ít token hơn (6 repo)

| Mục trong ảnh | Repo | Sao (ảnh) | Giấy phép (đọc từ LICENSE) | README (byte) | File | Cờ | Giữ |
|---|---|---|---|---|---|---|---|
| Claude-Mem | `thedotmack/claude-mem` | 102k | Apache-2.0 | 20.457 | 2.735 | - |  |
| Headroom | `headroomlabs-ai/headroom` | 77k | Apache-2.0 | 34.650 | 2.684 | - |  |
| Caveman | `JuliusBrussee/caveman` | 114k | Apache-2.0 | 22.657 | 1.793 | stars-unverified |  |
| gstack | `garrytan/gstack` | 137k | MIT | 89.520 | 3.949 | readme-over-limit, large-tree, stars-unverified |  |
| BMAD Method | `bmad-code-org/BMAD-METHOD` | 54k | MIT | 7.918 | 584 | stars-unverified |  |
| GSD | `gsd-build/get-shit-done` | 64k | MIT | 329 | 1.854 | readme-tiny, stars-unverified | **giữ** |

### Đợt 4: Thiết kế và hình ảnh (4 repo)

| Mục trong ảnh | Repo | Sao (ảnh) | Giấy phép (đọc từ LICENSE) | README (byte) | File | Cờ | Giữ |
|---|---|---|---|---|---|---|---|
| Taste | `Leonxlnx/taste-skill` | 101k | MIT | 15.088 | 72 | - |  |
| Archify | `tt-a1i/archify` | 88k | MIT | 36.520 | 1.174 | - |  |
| Diagram Design | `cathrynlavery/diagram-design` | 60k | MIT | 53.859 | 686 | readme-over-limit, stars-unverified |  |
| PPT Master | `hugohe3/ppt-master` | 67k | MIT | 31.156 | 13.111 | large-tree, stars-unverified |  |

### Đợt 5: Viết lách và video (6 repo)

| Mục trong ảnh | Repo | Sao (ảnh) | Giấy phép (đọc từ LICENSE) | README (byte) | File | Cờ | Giữ |
|---|---|---|---|---|---|---|---|
| Humanizer | `blader/humanizer` | 59k | MIT | 12.926 | 14 | stars-unverified |  |
| I Have ADHD | `ayghri/i-have-adhd` | 58k | MIT | 3.995 | 74 | - |  |
| Marketing Skills | `coreyhaines31/marketingskills` | 56k | MIT | 25.479 | 770 | stars-unverified |  |
| HyperFrames | `heygen-com/hyperframes` | 70k | Apache-2.0 | 22.976 | 9.167 | large-tree, stars-unverified |  |
| OpenMontage | `calesthio/OpenMontage` | 71k | GPL/AGPL/LGPL | 42.901 | 2.208 | readme-over-limit, copyleft, stars-unverified |  |
| Skills (Anthropic) | `anthropics/skills` | 183k | không có file LICENSE | 5.552 | 445 | license-unclear, stars-unverified | **giữ** |


Radar đưa cho model tối đa 12.000 ký tự README (`readme_max_chars`, cắt theo cả mục), nên mọi README dài hơn mức đó mất một phần; cờ `readme-over-limit` chỉ đánh dấu loại dài hơn 40.000 byte.

Cờ:

- `license-unclear`: no root LICENSE file: the radar's licence gate may refuse it
- `readme-tiny`: README under 1,000 bytes: the radar has almost no facts to write from
- `readme-over-limit`: README over 40,000 bytes: the model sees under a third of it (readme_max_chars is 12,000 characters, cut by whole sections), so install or usage sections may be dropped
- `large-tree`: 3,000 files or more: only top-level entries and a few children are shown to the model
- `copyleft`: GPL family licence: accepted by radar.yaml, but the digest's note on licensing must say so
- `stars-unverified`: owner/name exists but its star count has not been compared with the image

3 repo đánh dấu **giữ** chưa chạy bằng radar: lý do ở mục 3.4.

## 3. Hướng 1: bài của radar cho 25 repo

### 3.1 Cái radar đã có

- Một repo mỗi lượt: `python3 radar.py run --repo owner/tên` hoặc workflow *Radar scan* với ô `repo` (README, mục "Quét đúng một repo bạn chọn").
  Số sao, độ mới và "đã viết rồi" chỉ cho cảnh báo; repo riêng tư hoặc bị khóa, giấy phép ngoài danh sách `licenses` của `radar.yaml`, hoặc tên sai vẫn bị từ chối.
- Sau mỗi lượt: bot mở PR `radar: scan <ngày>` (khi có `RADAR_PR_TOKEN`) và `handoff` mở PR nháp vào `tool-marketing-studio`. Không bao giờ ghi vào `main` của studio.

### 3.2 Số đo thật (`state/runs`, 20 lần chạy thật)

34 lần thử viết, 30 bài xuất, 4 bài bị giữ (12%), do cổng kiểm tra từ chối (thiếu mục, lệnh không nằm trong README). 101 lượt gọi model có ghi log,
34 lượt lỗi (Gemini treo hoặc timeout, 429, 503, 404). Từ 17/10 log có thời gian: 628 giây model cho 13 lần thử, khoảng 48 giây mỗi lần, cộng nghỉ `pace_seconds: 45`.

Ước tính (số cũ chỉ từ 13 lần thử, hạn mức free theo ngày **chưa đo**): khoảng 1,5 đến 2 phút mỗi repo, 25 repo cỡ 40 đến 50 phút chạy, trải ra vài ngày vì
hạn mức; dự trù khoảng 3 bài bị giữ cần chạy lại (12% của 25). Repo bị giữ không được nhớ, nên lượt sau tự xét lại.

### 3.3 Các bước

0. Merge PR này.
   Trước mỗi lượt chạy thật hoặc báo cáo viết tay, tra repo (không phân biệt hoa thường) trong `state/seen.json` ở `main` mới nhất, `digests/<lượt>/<repo>/`, `docs/reports/` và các PR `radar/scan-*` đang mở: thấy ở đâu là đã viết, không viết lại (luật "một repo, một bài" trong `CLAUDE.md`). Không chạy lượt thật khi còn một PR quét đang mở.
1. **Chạy thử không tốn quota cho cả 25 repo** (cần `GITHUB_TOKEN`; phiên viết kế hoạch này không có):
   ```bash
   for r in $(python3 -c "import json;print(' '.join(e['repo'] for e in json.load(open('artifacts/plans/top30-claude-plugins.json'))['entries'] if e['status']=='todo'))"); do
     python3 radar.py run --repo "$r" --dry-run
   done
   ```
   Đọc `requested.warnings`, repo có bị từ chối vì giấy phép không, số sao so với ảnh, README. Kết quả quyết định các repo `stars-unverified` và ba repo giữ.
2. **Chạy thật theo đợt 1 đến 5**, mỗi lượt một repo (Actions: `dry_run` bỏ chọn, ô `repo`). Merge PR của lượt trước **trước** khi chạy lượt sau: mỗi lượt sửa
   `state/seen.json` và `state/stars.json`, hai PR chưa merge sẽ xung đột (`docs/branch-protection.md`). Bài bị giữ thì chạy lại sau.
3. **Duyệt bản nháp studio**: mỗi lượt một PR nháp ở `tool-marketing-studio`; chỉ chủ repo duyệt, merge và đăng.
4. *Tuỳ chọn, PR riêng (T2):* nếu bấm 25 lần là quá nhiều, thêm cách đưa một danh sách repo vào một lượt chạy (ví dụ `--repos-file`), chạy tuần tự trong
   giới hạn `max_run_minutes: 35`, kiểm bằng GitHub giả và model giả như `tests/test_pipeline.py`. Chưa làm trước khi bước 1 xong.

### 3.4 Ba repo giữ lại

- `forrestchang/andrej-karpathy-skills`: không có file LICENSE ở gốc (plugin.json ghi MIT, README có mục License). Nếu trường `license` của GitHub rỗng, radar từ chối, đúng thiết kế.
- `gsd-build/get-shit-done`: README chỉ 329 byte, radar không có gì để viết (nguồn duy nhất của radar là README và cây thư mục).
- `anthropics/skills`: không có LICENSE ở gốc, giấy phép nằm theo từng skill.

Không nới cổng để các repo này qua (CLAUDE.md). Đường thay thế là Hướng 2: báo cáo đọc mọi file ở commit đã ghim, không phụ thuộc README, và ghi giấy phép đúng sự thật ở mục Lưu ý.
Nếu chủ repo muốn bỏ qua các repo này thì đánh dấu bỏ.

## 4. Hướng 2: báo cáo Moda do Codex làm (pilot một repo)

`docs/reports/` có sẵn kiểu báo cáo thứ hai: đọc sâu nhiều file của repo, mỗi ý có nhãn `[Sn]` trỏ tới file ở commit ghim, kèm slide plan và deck dựng trên Moda
(`genai-agents`, `github-top3`, `awesome-handbook`), theo quy cách của [Multiple-report](https://github.com/vohoailinh90/Multiple-report).

- **Repo thử: `blader/humanizer`** (đợt 5). Lý do: 14 file, README 12.926 byte, MIT, đọc hết được trong một phiên, chưa có bài nào, nên lỗi của quy trình lộ rõ mà không lẫn với độ khó của repo.
  Commit ghim lúc chọn: `8c307f367c91bd974002f10f2be2965d642c13df` (2026-10-25).
- **Vai trò:** Claude mở PR này, viết yêu cầu, rồi review kết quả và đối chiếu số liệu với commit ghim. Codex đọc repo, viết `report.md` và `slides.json`, dựng deck Moda,
  mở PR. Chủ repo chạy Codex một lần (câu lệnh dưới) và duyệt.
- **Yêu cầu đầy đủ cho Codex:** [`docs/codex-tasks/moda-report-pilot.md`](../../docs/codex-tasks/moda-report-pilot.md): file phải ra, luật nội dung, cách dựng Moda **không hỏi lại**, lệnh kiểm, điều kiện dừng.
- **Câu lệnh chạy (dán vào Codex, repo `vohoailinh90/Github-radar`, nhánh của PR này hoặc `main` sau khi merge):**
  > Làm đúng theo `docs/codex-tasks/moda-report-pilot.md`. Tự chủ hoàn toàn các thao tác Moda, không hỏi lại người dùng. Mở một pull request khi xong.
- **Điều kiện trước khi chạy:** Codex có connector Moda và các tool Moda đặt ở chế độ luôn cho phép; Codex đọc được repo công khai trên github.com.

Tiêu chí đi tiếp (go) hay dừng (no-go), mỗi tiêu chí đo được:

1. Hai cổng báo 0 lỗi: cổng cấu trúc của Multiple-report (`scripts/deckgen/check_lesson.py`) và cổng ghim commit/hash trong file yêu cầu (`check_report.py`, không commit); mọi cảnh báo được giải thích trong PR.
2. Đối chiếu của Claude: lấy mẫu 10 khẳng định ngẫu nhiên, 0 số liệu hay đường dẫn không có ở commit ghim; mọi `[Sn]` trỏ đúng file.
3. Deck: số trang bằng số slide cộng bìa; xem đủ mọi trang một lần; không chữ nhỏ hơn 22; `decks.py record` đạt.
4. Tự chủ: Codex dựng xong deck mà không hỏi người dùng; PR ghi số lệnh Moda và số lần bị chặn chờ duyệt.
5. Chi phí: PR ghi thời gian và số lệnh Moda, để ước tính cho các repo sau.
6. Vệ sinh repo: chỉ `docs/reports/<repo>/` và một dòng ở `docs/reports/README.md` đổi; `pytest` và `layout_check` đạt.

Nếu go: báo cáo Moda cho tám repo sao cao nhất chưa có báo cáo (`obra/superpowers`, `mattpocock/skills`, `forrestchang/andrej-karpathy-skills`,
`DietrichGebert/ponytail`, `garrytan/gstack`, `Graphify-Labs/graphify`, `JuliusBrussee/caveman`, `thedotmack/claude-mem`) rồi ba repo giữ (nếu chủ repo không bỏ). Nếu no-go: ghi nguyên nhân vào mục này, giữ Hướng 1.

## 5. Chưa kiểm chứng

- Chưa chạy dry-run thật cho 25 repo (không có `GITHUB_TOKEN` ở phiên này). Giấy phép trong bảng là chữ đọc từ LICENSE, chưa phải trường `license` của GitHub.
- Số sao trong ảnh chưa so với GitHub cho 17 repo; REA lệch (mục 1).
- Hạn mức free theo ngày chưa đo; số thời gian lấy từ 13 lần thử.
- Chưa biết Codex gọi được Moda ở chế độ luôn cho phép và đọc được repo công khai: đó chính là việc pilot kiểm.
- Ảnh là một ảnh chụp do người khác dựng (Charlie Hills); báo cáo này không kiểm nó đúng hay đủ, chỉ lấy tên và nhóm.

## Quyết định đã chọn mặc định (chủ repo muốn tự chủ; đổi được bằng một dòng)

- Pilot dùng `blader/humanizer`; đợt chạy theo nhóm của ảnh; ba repo giữ chờ dry-run; chưa làm hàng đợi; deck xuất PPTX (không PDF) để repo nhẹ.
