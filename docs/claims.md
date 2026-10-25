# Giữ chỗ khi nhiều phiên Claude / Codex làm chung

Mỗi phiên Claude hoặc Codex làm việc trong một bản sao riêng của repo (một container trên cloud, một worktree), nên chúng **không thấy nhau**. Hai phiên có thể cùng nhận một việc: cùng viết báo cáo cho một repo, cùng dựng một deck Moda, cùng sửa một thư mục. `scripts/claim.py` là sổ ghi "ai đang làm gì" để chuyện đó không xảy ra. Nó bổ sung cho `state/seen.json` (cái đã làm xong) bằng cái **đang làm dở**.

## Dùng thế nào

Hạng mục là một repo (`owner/name`), một thư mục báo cáo (`docs/reports/<tên>`) hoặc một đường dẫn tệp.

```bash
python3 scripts/claim.py claim docs/reports/genai-agents --agent claude --note "deck Moda"   # giữ chỗ trước khi làm
python3 scripts/claim.py renew docs/reports/genai-agents          # làm lâu hơn 2 giờ thì gia hạn
python3 scripts/claim.py release docs/reports/genai-agents        # xong thì nhả
python3 scripts/claim.py list                                     # ai đang giữ gì (thêm --live, --json)
python3 scripts/claim.py check docs/reports/genai-agents          # chỉ hỏi, không ghi gì
```

| Mã thoát | Nghĩa | Phiên làm gì |
|---|---|---|
| 0 | Hạng mục là của bạn trong thời hạn (mặc định 2 giờ, tối đa 24 giờ) | Làm |
| 1 | Phiên khác đang giữ, hoặc một thư mục / tệp lồng với nó đang bị giữ | Chọn việc khác, không làm hạng mục này, nói rõ vì sao |
| 2 | Sai cách gọi (tên hạng mục không hợp lệ...) | Sửa lệnh |
| 3 | Không với tới được sổ (mạng, quyền), hoặc lệnh đứt giữa chừng | Không làm hạng mục khi chưa giữ chỗ, báo một lần. Nếu thông báo nói *một giữ chỗ của bạn có thể còn đứng*, chạy `list`, và `release` khi sổ trả lời lại (nếu không, nó tự hết hạn) |

- Nhiều hạng mục một lệnh thì **được cả hoặc không được gì**.
- Giữ chỗ của chính bạn đã **hết hạn** không còn được coi là gia hạn: nó được kiểm trùng đường dẫn lại như giữ chỗ mới, vì trong lúc đó phiên khác có thể đã nhận một thư mục hay tệp lồng với nó.
- Giữ chỗ theo đúng cỡ của việc: một báo cáo là cả thư mục của nó. Thư mục và tệp bên trong nó **lồng nhau**: không giữ đồng thời bởi hai phiên khác nhau.
- Giữ chỗ hết hạn sau thời hạn của nó, nên một phiên bị ngắt giữa chừng không chặn hạng mục mãi mãi. Chỉ giữ chỗ **đã hết hạn hoặc đã nhả** mới bị phiên khác nhận; cũng chỉ giữ chỗ **còn hiệu lực** của phiên khác mới bị từ chối khi bạn `release` nó.
- Hai phiên dùng chung một bản sao dùng chung một mã phiên; cho mỗi phiên mã riêng bằng `--session` hoặc biến `CLAIM_SESSION`.

## Cách nó hoạt động (và vì sao tin được)

Mỗi hạng mục là **một nhánh `claims/<tên>`** trên GitHub. Mỗi thay đổi (giữ chỗ, gia hạn, nhả, nhận lại) là một **commit mới nối vào đầu nhánh**, commit rỗng chứa thông tin giữ chỗ dạng JSON trong lời nhắn, không thêm tệp nào. Hai phiên cùng đẩy một commit con của cùng một đầu nhánh thì GitHub chỉ nhận một: đó là bảo đảm của git, không phải của script. Nhánh này chỉ nối thêm, không ai ghi đè hay xoá, nên mọi lần giữ chỗ đều còn trong lịch sử. CI chỉ chạy cho `main` và pull request nên giữ chỗ không kích hoạt lượt chạy nào.

Thiết kế này theo đúng những gì **đo được** ở phiên Claude Code trên web: đẩy nhánh được, nhưng xoá nhánh, đẩy tag hay đẩy ref ngoài `refs/heads/` đều bị từ chối (HTTP 403). Vì vậy script không dùng force-push, không xoá và không dùng tag.

## Dọn dẹp

Một hạng mục xong vẫn **giữ nhánh** của nó (phiên trên web không xoá được). Số nhánh bị chặn bởi số hạng mục từng được giữ, vì giữ lại cùng hạng mục thì nối vào cùng nhánh. Khi muốn dọn, chạy trên máy của bạn (nơi được xoá nhánh):

```bash
python3 scripts/claim.py prune --older 30d --dry-run   # xem sẽ xoá gì
python3 scripts/claim.py prune --older 30d             # xoá nhánh của giữ chỗ đã nhả/hết hạn từ 30 ngày trước
```

`prune` không bao giờ xoá giữ chỗ còn hiệu lực, và bỏ qua nhánh `claims/*` không do script tạo (của người tạo tay).

## Giới hạn

- Hết hạn so giờ của các máy khác nhau, nên lệch đồng hồ làm lệch giờ hết hạn đúng bằng độ lệch. Hạn mặc định 2 giờ chịu được lệch vài phút.
- Không gì **ép** một phiên gọi script; đó là công cụ mà quy luật trong `CLAUDE.md` ("Shared work") yêu cầu dùng. Nếu cần ép, bước sau là một hook từ chối ghi vào đường dẫn đang bị phiên khác giữ (chưa làm).
- Một nhánh `claims/*` do người tạo tay (không phải của script) được coi là đang giữ chỗ cho tới khi hết hạn mặc định; xoá nó bằng `git push origin :refs/heads/claims/<tên>` nếu muốn mở lại ngay.
