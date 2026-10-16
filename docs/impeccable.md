# Kỹ năng thiết kế UI: impeccable

Repo này giữ một bản sao của skill [**impeccable**](https://github.com/pbakaus/impeccable) (Paul Bakaus, Apache-2.0) để **đem sang các repo khác** khi cần thiết kế giao diện. Skill gồm 1 lệnh `/impeccable` với 24 lệnh con (`init`, `shape`, `critique`, `audit`, `polish`, `harden`, `animate`, ...), cộng các quy tắc chống kiểu giao diện "do AI làm" (font mặc định, gradient tím-xanh, thẻ lồng thẻ...).
Skill **không tham gia pipeline Radar**: hình trong bài học do script vẽ (`radar/svg.py`, `radar/boards.py`), không phải model thiết kế.

## Có gì trong repo

| Đường dẫn | Là gì |
|---|---|
| `.claude/skills/impeccable/` | Skill (`SKILL.md`, `reference/`, `scripts/`). Đúng từng byte bản dựng Claude Code của upstream |
| `.claude/agents/impeccable-*.md` | 4 subagent mà skill tự gọi khi dựng và rà soát giao diện (asset-producer, documenter, finish-reviewer, manual-edit-applier). Chép chúng cùng skill; chỉ môi trường không có subagent mới chạy các vai này tại chỗ theo `reference/degraded/` |
| `docs/third-party/impeccable/` | `LICENSE` (Apache-2.0) và `NOTICE.md` (hai tệp tham chiếu iOS/Android chắt lọc từ MIT `ehmo/platform-design-skills`) |
| `.claude/skills/impeccable.lock.json` | Commit upstream, phiên bản skill/engine và sha256 từng tệp |

Phiên bản đang giữ: skill **4.6.0**, engine **0.1.15**, upstream commit ghi trong tệp lock.

## Dùng ở repo khác

Cách 1, chép bản đã được pin ở đây (từ gốc repo này):

```bash
mkdir -p <repo-đích>/.claude/skills <repo-đích>/.claude/agents
cp -a .claude/skills/impeccable <repo-đích>/.claude/skills/
cp -a .claude/agents/impeccable-*.md <repo-đích>/.claude/agents/
```

Chép vào `~/.claude/skills/` và `~/.claude/agents/` thì áp dụng cho mọi repo.

Cách 2, cài thẳng từ upstream (lấy bản mới nhất, và cài cả hook): `npx impeccable install --providers=claude --scope=project` chạy ở gốc repo đích. Cách 3, trong Claude Code: `/plugin marketplace add pbakaus/impeccable`.

Sau đó mở repo đích và chạy `/impeccable init` một lần (ghi `PRODUCT.md`), rồi dùng, ví dụ `/impeccable critique landing` hoặc `/impeccable polish settings`. Danh sách lệnh đầy đủ: README của upstream hoặc bảng *Commands* trong `SKILL.md`.

## Điều cần biết trước khi dùng

- **Engine được tải ở lần chạy đầu.** `scripts/impeccable` (launcher) chạy một binary dựng sẵn. Thứ tự tìm: `$IMPECCABLE_BIN` (chạy thẳng, không thăm dò), binary cạnh launcher, `~/.impeccable/bin/impeccable` và lệnh `impeccable` trên `PATH` (hai nơi này chỉ được thăm dò bằng một lời chào, không xác thực). Không có thì nó tải `impeccable-<os>-<arch>` từ `github.com/pbakaus/impeccable/releases` (bản `engine-v0.1.15`) vào `~/.impeccable/bin/` và chỉ chạy khi khớp tệp `.sha256` đi kèm. Tệp `.sha256` nằm cùng bản phát hành nên chỉ chống tải hỏng, **không** chống một bản phát hành bị xâm phạm. Binary này **không nằm trong repo** và chưa được kiểm toán ở đây. Môi trường sandbox không có mạng: cài sẵn rồi đặt `IMPECCABLE_BIN`.
- **Hook không được nối ở repo này.** Upstream có hook chạy `impeccable hook` sau mỗi lần Edit/Write và khi Stop; ở đây không có `.claude/settings.json` nào gọi chúng. Muốn dùng hook ở repo đích, để `npx impeccable install` cài, rồi duyệt hook theo hướng dẫn của upstream.
- **Không sửa tay bản sao.** `python3 scripts/vendor_impeccable.py check` (cũng chạy trong `pytest`) báo tệp bị sửa, thiếu, thừa hoặc mất quyền thực thi của launcher.

## Cập nhật lên bản mới

```bash
git clone --depth 1 https://github.com/pbakaus/impeccable <thư-mục-tạm>
python3 scripts/vendor_impeccable.py snapshot <thư-mục-tạm>   # chép lại và ghi lại tệp lock
python3 -m pytest -q
git diff --stat                                                # đọc phần thay đổi trước khi commit
```

`snapshot` từ chối chạy nếu bản clone có thay đổi chưa commit, để commit ghi trong lock mô tả đúng nội dung.
