# Hướng dẫn dựng mô hình trong PowerDesigner

Nguồn chuẩn là [`../database/usad_schema.sql`](../database/usad_schema.sql).
Tạo **Physical Data Model (PDM)** cho MySQL từ đúng DDL này; không thêm, bỏ,
đổi tên bảng/cột, khóa, kiểu dữ liệu, quan hệ, UNIQUE, CHECK hoặc index. Tài
liệu này chỉ hướng dẫn mô hình hóa, không phải migration và không tự chạy SQL.

## Thiết lập mô hình

1. Tạo PDM mới và chọn DBMS MySQL phù hợp với MySQL 8.0.16 trở lên để CHECK
   constraints được thực thi.
2. Đặt database/schema name là `usad_dev`.
3. Chọn InnoDB, character set `utf8mb4`, collation `utf8mb4_unicode_ci`.
4. Reverse-engineer/import DDL từ `database/usad_schema.sql` nếu phiên bản
   PowerDesigner hỗ trợ đúng cú pháp MySQL của file; nếu không, dựng đúng chín
   bảng và các thuộc tính liệt kê bên dưới.
5. Kiểm tra tên và thuộc tính constraint/index trong PDM khớp nguyên văn với
   DDL. Không tạo migration framework hay tự đồng bộ với database đang chạy.
6. Lưu model trong file làm việc của PowerDesigner theo quy trình dự án. Không
   ghi credentials hoặc dữ liệu người dùng thật vào model hay file seed.

## Danh sách bảng chuẩn

| # | Bảng | Primary key | Quan hệ chính |
|---:|---|---|---|
| 1 | `users` | `pk_users(user_id)` | Người dùng |
| 2 | `projects` | `pk_projects(project_id)` | `fk_projects_owner` → `users.user_id` |
| 3 | `project_members` | `pk_project_members(project_id, user_id)` | Project và user |
| 4 | `workspaces` | `pk_workspaces(workspace_id)` | `fk_workspaces_project` → `projects.project_id` |
| 5 | `runtime_nodes` | `pk_runtime_nodes(node_id)` | Metadata node thực thi |
| 6 | `sandboxes` | `pk_sandboxes(sandbox_id)` | Workspace, node, creator |
| 7 | `sandbox_sessions` | `pk_sandbox_sessions(session_id)` | Sandbox và user |
| 8 | `audit_logs` | `pk_audit_logs(log_id)` | User, project, sandbox tùy chọn |
| 9 | `ai_jobs` | `pk_ai_jobs(job_id)` | User, project, workspace tùy chọn |

Chi tiết toàn bộ cột, kiểu dữ liệu, defaults, nullability, checks, unique
constraints, indexes và foreign keys được liệt kê trong
[Data Dictionary](./DATA_DICTIONARY.md) và phải đối chiếu với SQL gốc. Tất cả
bảng dùng `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci`.

## Quan hệ cần thể hiện

- `users` 1:N `projects` theo `projects.owner_user_id`.
- `users` N:N `projects` qua bảng nối `project_members` (hai cột khóa chính
  đồng thời là foreign key).
- `projects` 1:N `workspaces`.
- `workspaces`, `runtime_nodes`, `users` 1:N `sandboxes` tương ứng theo các
  foreign key workspace, node, creator.
- `sandboxes` 1:N `sandbox_sessions`; `users` 1:N `sandbox_sessions`.
- `users`, `projects`, `sandboxes` 1:N `audit_logs` theo các FK nullable.
- `users`, `projects` 1:N `ai_jobs`; `workspaces` 1:N `ai_jobs` qua FK nullable.

Mỗi foreign key sử dụng `ON UPDATE RESTRICT ON DELETE RESTRICT`, như trong DDL.
Không đổi thành cascade hoặc tự thêm quan hệ.

## Quy tắc nghiệp vụ không được schema đảm bảo

Foreign key chỉ kiểm tra sự tồn tại của dòng được tham chiếu, không tự xác
nhận quyền truy cập hoặc sự nhất quán giữa nhiều quan hệ:

- `ai_jobs.workspace_id` có thể trỏ tới một workspace thuộc **project khác**
  với `ai_jobs.project_id`. Phải kiểm tra workspace cùng project ở application
  service hoặc thiết kế constraint bổ sung chỉ sau khi chủ schema phê duyệt.
- `ai_jobs.user_id` không được ràng buộc phải là owner hoặc thành viên của
  `ai_jobs.project_id`.
- `sandboxes.created_by_user_id` có thể không có quyền với project chứa
  workspace. Ứng dụng cần xác định project từ workspace và kiểm tra membership
  / role trước khi tạo hoặc thao tác sandbox.
- `sandbox_sessions.user_id` chỉ cần tồn tại trong `users`; schema không bắt
  buộc người đó là thành viên project, người tạo sandbox, hay được phép mở
  terminal. Phải xác thực và phân quyền mỗi request.
- `project_members` cho phép role `owner` nhưng không buộc phải có đúng một
  owner, cũng không đồng bộ tự động với `projects.owner_user_id`.
- `audit_logs` cho phép các ID user/project/sandbox tùy chọn độc lập; FK không
  xác nhận chúng cùng thuộc một project. Ứng dụng cần ghi audit đã chuẩn hóa
  và loại trừ bí mật.
- Status, CPU/RAM/PID limits và `network_enabled` là metadata. Chúng không tự
  vận hành container, áp đặt resource controls, chặn network, hoặc chứng minh
  runtime đang ở trạng thái tương ứng.
- Unique constraint `(node_id, runtime_ref)` ở MySQL có thể cho phép nhiều dòng
  `NULL` trong `runtime_ref`; vì vậy không xem constraint này là unique cho
  các sandbox chưa có runtime reference.

## Kiểm tra trước khi xuất DDL

- Đúng chín bảng nêu trên; không có bảng phụ.
- Tên, kiểu, nullability, default, PK/FK, CHECK, UNIQUE, index khớp
  `database/usad_schema.sql`.
- Các cột FK tham chiếu đến PK tương ứng: `users.user_id`,
  `projects.project_id`, `workspaces.workspace_id`, `runtime_nodes.node_id`,
  `sandboxes.sandbox_id`.
- Toàn bộ bảng dùng InnoDB và `utf8mb4_unicode_ci`.
- Dùng compare/preview của PowerDesigner trước khi export; không execute SQL
  trên database hiện có trong bước modeling này.
- Chỉ chủ dự án/database được phê duyệt mới chạy thử trên một MySQL local dev
  riêng, rỗng và có thể xóa. Kiểm tra lại database/schema đích trong client
  trước khi thực thi file; file có `CREATE DATABASE IF NOT EXISTS` và `USE
  usad_dev`, nhưng không nên dựa vào đó để tránh nhầm môi trường.

Backend hiện có FastAPI, SQLAlchemy và PyMySQL; các route project/workspace
dùng database này. File SQL không được backend hoặc Compose thực thi tự động,
và repository chưa có migration framework. Mọi thay đổi bootstrap/migration
vẫn cần được đề xuất, review và phê duyệt riêng.

## Chạy thử thủ công trên MySQL local

Chỉ làm bước này khi bạn đã chủ động cài/chọn một MySQL local dev riêng và xác
nhận đúng instance không chứa dữ liệu cần giữ. Không dùng VPS hay production.
Từ thư mục gốc workspace, có thể yêu cầu MySQL client đọc file bằng:

```powershell
cmd.exe /d /c "mysql --default-character-set=utf8mb4 -u local_dev_user -p < database\usad_schema.sql"
```

Thay `local_dev_user` bằng tài khoản MySQL local của bạn. `-p` để client hỏi
mật khẩu tương tác; không ghi mật khẩu trực tiếp vào lệnh, file SQL hoặc tài
liệu. Trước khi xác nhận, xem lại host/socket và instance được client chọn;
câu lệnh trên không chỉ định host để dùng cấu hình local client mặc định. File
tạo/chọn `usad_dev`, sau đó bạn có thể kiểm tra thủ công:

```sql
SHOW TABLES;
SHOW CREATE TABLE projects;
SHOW CREATE TABLE sandboxes;
```

Các câu lệnh SQL kiểm tra trên chỉ chạy thủ công trong MySQL client sau khi
người dùng chọn đúng local instance; không được chạy bởi ứng dụng hay quy
trình này.
