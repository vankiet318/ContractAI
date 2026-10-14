import { BarChart3, LockOpen, ShieldCheck, ShieldOff, Trash2 } from "lucide-react";
import { useState } from "react";
import { deleteUser, setUserRole, unlockUser } from "../../api/admin";
import { toErrorMessage } from "../../api/client";
import { useToast } from "../../hooks/useToast";
import type { AdminUser } from "../../types";
import { ConfirmDialog } from "../ConfirmDialog";
import type { ActionMenuItem } from "../ui/ActionMenu";

type PendingAction = { kind: "role" | "delete"; user: AdminUser };

/** The ⋮ menu actions on a user, with their confirmations. */
export function useUserActions({
  currentUserId,
  onOpenDetails,
  onChanged,
  onDeleted,
}: {
  currentUserId: string;
  onOpenDetails: (userId: string) => void;
  onChanged: () => void;
  onDeleted: (userId: string) => void;
}) {
  const { showToast } = useToast();
  const [pending, setPending] = useState<PendingAction | null>(null);

  const run = async (
    action: () => Promise<unknown>,
    success: string,
    failure: string,
  ): Promise<boolean> => {
    try {
      await action();
    } catch (error) {
      showToast(toErrorMessage(error, failure), "error");
      return false;
    }

    showToast(success, "success");
    return true;
  };

  const confirm = async () => {
    if (!pending) return;

    const { kind, user } = pending;
    setPending(null);

    if (kind === "role") {
      const nextRole = user.role === "admin" ? "user" : "admin";

      if (
        await run(
          () => setUserRole(user.user_id, nextRole),
          "Đã cập nhật quyền.",
          "Không đổi được quyền.",
        )
      ) {
        onChanged();
      }
    } else if (
      await run(
        () => deleteUser(user.user_id),
        `Đã xóa ${user.email}.`,
        "Không xóa được người dùng.",
      )
    ) {
      onDeleted(user.user_id);
      onChanged();
    }
  };

  const unlock = async (user: AdminUser) => {
    if (
      await run(
        () => unlockUser(user.user_id),
        `Đã mở khóa ${user.email}.`,
        "Không mở khóa được tài khoản.",
      )
    ) {
      onChanged();
    }
  };

  const menuItems = (user: AdminUser): ActionMenuItem[] => {
    const isSelf = user.user_id === currentUserId;
    return [
      {
        label: "Xem thống kê",
        icon: BarChart3,
        onSelect: () => onOpenDetails(user.user_id),
      },
      {
        label: user.role === "admin" ? "Gỡ quyền admin" : "Cấp quyền admin",
        icon: user.role === "admin" ? ShieldOff : ShieldCheck,
        onSelect: () => setPending({ kind: "role", user }),
        disabled: isSelf,
        title: isSelf ? "Không thể tự đổi quyền của chính mình" : undefined,
      },
      {
        label: "Mở khóa tài khoản",
        icon: LockOpen,
        onSelect: () => unlock(user),
        // Always listed, so admins know it exists before they need it.
        disabled: !user.is_locked,
        title: user.is_locked
          ? undefined
          : "Tài khoản không bị khóa do đăng nhập sai",
      },
      {
        label: "Xóa người dùng",
        icon: Trash2,
        tone: "danger",
        onSelect: () => setPending({ kind: "delete", user }),
        disabled: isSelf,
        title: isSelf ? "Không thể tự xóa tài khoản của chính mình" : undefined,
      },
    ];
  };

  const promotes = pending?.user.role !== "admin";

  const dialog =
    pending?.kind === "delete" ? (
      <ConfirmDialog
        open
        title="Xóa người dùng"
        message={`Xóa ${pending.user.email}? Toàn bộ đoạn chat, tài liệu và lịch sử sử dụng của tài khoản này sẽ bị xóa vĩnh viễn.`}
        onConfirm={confirm}
        onCancel={() => setPending(null)}
      />
    ) : (
      <ConfirmDialog
        open={pending !== null}
        title={promotes ? "Cấp quyền admin" : "Gỡ quyền admin"}
        message={
          promotes
            ? `${pending?.user.email} sẽ xem được thống kê của mọi người dùng và quản lý tài khoản của họ.`
            : `${pending?.user.email} sẽ không còn truy cập được trang quản trị.`
        }
        confirmLabel="Xác nhận"
        confirmVariant={promotes ? "primary" : "danger"}
        onConfirm={confirm}
        onCancel={() => setPending(null)}
      />
    );

  return { menuItems, dialog };
}
