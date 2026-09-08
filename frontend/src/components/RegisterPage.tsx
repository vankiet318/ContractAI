import { useState } from "react";
import { register } from "../api/auth";
import { ApiError } from "../api/client";

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
        err instanceof ApiError ? err.message : "Đăng ký thất bại",
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
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="rounded-md bg-slate-900 text-white text-sm font-medium py-2 hover:bg-slate-700"
          >
            Đến trang đăng nhập
          </button>
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
        <h1 className="text-lg font-semibold">Đăng ký</h1>

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
          minLength={8}
          placeholder="Mật khẩu (tối thiểu 8 ký tự)"
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
          {isSubmitting ? "..." : "Đăng ký"}
        </button>

        <button
          type="button"
          onClick={onSwitchToLogin}
          className="text-xs text-slate-500 hover:text-slate-900"
        >
          Đã có tài khoản? Đăng nhập
        </button>
      </form>
    </div>
  );
}
