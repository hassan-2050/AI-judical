"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authAPI } from "@/lib/api";
import toast from "react-hot-toast";
import { FiMail, FiLock, FiUser, FiPhone, FiMapPin, FiUserPlus } from "react-icons/fi";

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
    phone_number: "",
    cnic_number: "",
    organization: "",
    city: "",
    province: "",
    country: "Pakistan",
  });

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.email || !form.password || !form.first_name) {
      toast.error("Please fill in required fields");
      return;
    }
    if (form.password !== form.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (form.password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      const { confirmPassword, ...data } = form;
      const res = await authAPI.register(data);
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      toast.success("Registration successful!");
      router.push("/dashboard");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string | Record<string, string[]> } } };
      const errData = error.response?.data?.error;
      if (typeof errData === "string") {
        toast.error(errData);
      } else if (typeof errData === "object") {
        toast.error(Object.values(errData).flat().join(", "));
      } else {
        toast.error("Registration failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="card">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-display font-bold text-judiciary-dark">
              Create Account
            </h1>
            <p className="text-gray-500 text-sm mt-1">
              Register to access all features
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  First Name *
                </label>
                <div className="relative">
                  <FiUser className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    className="input pl-10"
                    placeholder="First name"
                    value={form.first_name}
                    onChange={(e) => update("first_name", e.target.value)}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Last Name
                </label>
                <input
                  className="input"
                  placeholder="Last name"
                  value={form.last_name}
                  onChange={(e) => update("last_name", e.target.value)}
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Email *
              </label>
              <div className="relative">
                <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  className="input pl-10"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Password *
                </label>
                <div className="relative">
                  <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="password"
                    className="input pl-10"
                    placeholder="Min 6 characters"
                    value={form.password}
                    onChange={(e) => update("password", e.target.value)}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Confirm Password *
                </label>
                <input
                  type="password"
                  className="input"
                  placeholder="Confirm password"
                  value={form.confirmPassword}
                  onChange={(e) => update("confirmPassword", e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Contact */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Phone
                </label>
                <div className="relative">
                  <FiPhone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    className="input pl-10"
                    placeholder="03xx-xxxxxxx"
                    value={form.phone_number}
                    onChange={(e) => update("phone_number", e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  CNIC
                </label>
                <input
                  className="input"
                  placeholder="xxxxx-xxxxxxx-x"
                  value={form.cnic_number}
                  onChange={(e) => update("cnic_number", e.target.value)}
                />
              </div>
            </div>

            {/* Organization */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Organization
              </label>
              <input
                className="input"
                placeholder="Your organization"
                value={form.organization}
                onChange={(e) => update("organization", e.target.value)}
              />
            </div>

            {/* Location */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  City
                </label>
                <div className="relative">
                  <FiMapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    className="input pl-10"
                    placeholder="City"
                    value={form.city}
                    onChange={(e) => update("city", e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Province
                </label>
                <select
                  className="input"
                  value={form.province}
                  onChange={(e) => update("province", e.target.value)}
                >
                  <option value="">Select</option>
                  <option value="Punjab">Punjab</option>
                  <option value="Sindh">Sindh</option>
                  <option value="KPK">KPK</option>
                  <option value="Balochistan">Balochistan</option>
                  <option value="Islamabad">Islamabad</option>
                  <option value="AJK">AJK</option>
                  <option value="GB">Gilgit-Baltistan</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">
                  Country
                </label>
                <input
                  className="input"
                  value={form.country}
                  onChange={(e) => update("country", e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-6"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <FiUserPlus size={18} /> Create Account
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-600 hover:underline font-medium">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
