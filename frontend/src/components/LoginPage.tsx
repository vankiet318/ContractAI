import { useState } from "react";
import { toErrorMessage } from "../api/client";
import { AppLogo } from "./AppLogo";
import { Button, TextButton } from "./ui/Button";
import { TextInput } from "./ui/TextInput";

export function LoginPage({
  onLogin,
  onSwitchToRegister,
}: {
  onLogin: (email: string, password: string) => Promise<void>;
  onSwitchToRegister: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onLogin(email, password);
    } catch (err) {
      setError(
        toErrorMessage(err, "Đăng nhập thất bại"),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center h-screen">
      <form
        onSubmit={handleSubmit}
        className="w-80 flex flex-col gap-3 p-6 rounded-lg border border-slate-200"
      >
        <AppLogo />
        <h1 className="text-lg font-semibold">Đăng nhập</h1>

        <TextInput
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <TextInput
          type="password"
          required
          placeholder="Mật khẩu"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Đang xử lý..." : "Đăng nhập"}
        </Button>

        <TextButton onClick={onSwitchToRegister}>
          Chưa có tài khoản? Đăng ký
        </TextButton>
      </form>
    </div>
  );
}
