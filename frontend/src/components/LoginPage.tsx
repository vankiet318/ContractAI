import { useState } from "react";
import { ApiError } from "../api/client";

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
        err instanceof ApiError ? err.message : "Đăng nhập thất bại",
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
        <h1 className="text-lg font-semibold">Đăng nhập</h1>

        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="password"
          required
          placeholder="Mật khẩu"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        />

        {error && <p className="text-xs text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-700 disabled:opacity-50 disabled:hover:bg-slate-900"
        >
          {isSubmitting ? "..." : "Đăng nhập"}
        </button>

        <button
          type="button"
          onClick={onSwitchToRegister}
          className="text-xs text-slate-500 hover:text-slate-900"
        >
          Chưa có tài khoản? Đăng ký
        </button>
      </form>
    </div>
  );
}
