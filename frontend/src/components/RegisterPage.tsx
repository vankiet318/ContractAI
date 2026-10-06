import { useState } from "react";
import { register } from "../api/auth";
import { toErrorMessage } from "../api/client";
import { AppLogo } from "./AppLogo";
import { Button, TextButton } from "./ui/Button";
import { TextInput } from "./ui/TextInput";

export function RegisterPage({
  onSwitchToLogin,
}: {
  onSwitchToLogin: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDone, setIsDone] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await register(email, password);
      setIsDone(true);
    } catch (err) {
      setError(
        toErrorMessage(err, "Đăng ký thất bại"),
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isDone) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-80 flex flex-col gap-3 p-6 rounded-lg border border-slate-200 text-center">
          <p className="text-sm">
            Tạo tài khoản thành công. Vui lòng đăng nhập.
          </p>
          <Button onClick={onSwitchToLogin}>Đến trang đăng nhập</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-screen">
      <form
        onSubmit={handleSubmit}
        className="w-80 flex flex-col gap-3 p-6 rounded-lg border border-slate-200"
      >
        <AppLogo />
        <h1 className="text-lg font-semibold">Đăng ký</h1>

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
          minLength={8}
          placeholder="Mật khẩu (tối thiểu 8 ký tự)"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Đang xử lý..." : "Đăng ký"}
        </Button>

        <TextButton onClick={onSwitchToLogin}>
          Đã có tài khoản? Đăng nhập
        </TextButton>
      </form>
    </div>
  );
}
