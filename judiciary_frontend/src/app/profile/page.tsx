"use client";

import { useState, useEffect } from "react";
import { authAPI, notificationsAPI } from "@/lib/api";
import type { User, Notification } from "@/types";
import Loading from "@/components/common/Loading";
import {
  FiUser,
  FiMail,
  FiPhone,
  FiMapPin,
  FiBell,
  FiStar,
  FiEdit,
  FiSave,
  FiX,
  FiTrash2,
  FiCalendar,
  FiCheck,
} from "react-icons/fi";
import toast from "react-hot-toast";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [auth, setAuth] = useState<{ email: string; role: string } | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<"profile" | "notifications" | "subscription">("profile");
  const [showReminder, setShowReminder] = useState(false);
  const [reminderData, setReminderData] = useState({ title: "", message: "", case_number: "", reminder_date: "" });

  useEffect(() => {
    loadProfile();
    loadNotifications();
  }, []);

  async function loadProfile() {
    try {
      const res = await authAPI.getProfile();
      setUser(res.data.profile);
      setAuth(res.data.auth);
    } catch {
      toast.error("Please login to view profile");
    } finally {
      setLoading(false);
    }
  }

  async function loadNotifications() {
    try {
      const res = await notificationsAPI.list({ page_size: 50 });
      setNotifications(res.data.notifications || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch {}
  }

  async function saveProfile() {
    try {
      await authAPI.updateProfile(editData);
      toast.success("Profile updated!");
      setEditing(false);
      loadProfile();
    } catch {
      toast.error("Failed to update profile");
    }
  }

  async function markRead(id: string) {
    try {
      await notificationsAPI.markRead(id);
      loadNotifications();
    } catch {}
  }

  async function markAllRead() {
    try {
      await notificationsAPI.markAllRead();
      loadNotifications();
    } catch {}
  }

  async function deleteNotification(id: string) {
    try {
      await notificationsAPI.delete(id);
      loadNotifications();
    } catch {}
  }

  async function createReminder() {
    if (!reminderData.title || !reminderData.message) {
      toast.error("Title and message are required");
      return;
    }
    try {
      await notificationsAPI.create({
        ...reminderData,
        notification_type: "hearing_reminder",
      });
      toast.success("Reminder created!");
      setShowReminder(false);
      setReminderData({ title: "", message: "", case_number: "", reminder_date: "" });
      loadNotifications();
    } catch {
      toast.error("Failed to create reminder");
    }
  }

  function startEditing() {
    if (!user) return;
    setEditData({
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      phone_number: user.phone_number || "",
      organization: user.organization || "",
      city: user.city || "",
      province: user.province || "",
      address: user.address || "",
    });
    setEditing(true);
  }

  if (loading) return <Loading text="Loading profile..." />;
  if (!user) {
    return (
      <div className="page-container text-center py-20">
        <FiUser className="mx-auto text-gray-300 mb-4" size={48} />
        <p className="text-gray-500 text-lg mb-4">Please login to view your profile</p>
        <a href="/login" className="btn-primary">Login</a>
      </div>
    );
  }

  const subscriptionTiers = [
    { name: "Free", price: "PKR 0", features: ["Basic search", "View cases", "5 documents/month"], current: user.subscription === "free" },
    { name: "Basic", price: "PKR 999/mo", features: ["Advanced search", "AI Assistant (limited)", "20 documents/month", "Case summaries"], current: user.subscription === "basic" },
    { name: "Premium", price: "PKR 2,499/mo", features: ["Unlimited AI Assistant", "Unlimited documents", "Case prediction", "Similar case finder", "Priority support", "Legal templates"], current: user.subscription === "premium" },
  ];

  const tabs = [
    { key: "profile", label: "Profile", icon: <FiUser size={14} /> },
    { key: "notifications", label: `Notifications${unreadCount > 0 ? ` (${unreadCount})` : ""}`, icon: <FiBell size={14} /> },
    { key: "subscription", label: "Subscription", icon: <FiStar size={14} /> },
  ] as const;

  return (
    <div className="page-container">
      <h1 className="page-title">My Profile</h1>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition ${
              activeTab === t.key
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <div className="card max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
                <FiUser className="text-primary-600" size={28} />
              </div>
              <div>
                <h2 className="text-xl font-bold">{user.first_name} {user.last_name}</h2>
                <p className="text-gray-500 text-sm flex items-center gap-1">
                  <FiMail size={12} /> {auth?.email}
                </p>
                <span className="badge bg-primary-50 text-primary-700 mt-1 capitalize">{auth?.role || "user"}</span>
              </div>
            </div>
            {!editing ? (
              <button onClick={startEditing} className="btn-secondary flex items-center gap-1">
                <FiEdit size={14} /> Edit
              </button>
            ) : (
              <div className="flex gap-2">
                <button onClick={saveProfile} className="btn-primary flex items-center gap-1">
                  <FiSave size={14} /> Save
                </button>
                <button onClick={() => setEditing(false)} className="btn-secondary">
                  <FiX size={14} />
                </button>
              </div>
            )}
          </div>

          {editing ? (
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(editData).map(([key, value]) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray-500 mb-1 capitalize">
                    {key.replace(/_/g, " ")}
                  </label>
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => setEditData({ ...editData, [key]: e.target.value })}
                    className="input"
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-y-4 gap-x-8">
              <InfoRow icon={<FiUser size={14} />} label="Name" value={`${user.first_name} ${user.last_name || ""}`} />
              <InfoRow icon={<FiPhone size={14} />} label="Phone" value={user.phone_number} />
              <InfoRow icon={<FiMapPin size={14} />} label="City" value={user.city} />
              <InfoRow icon={<FiMapPin size={14} />} label="Province" value={user.province} />
              <InfoRow icon={<FiUser size={14} />} label="Organization" value={user.organization} />
              <InfoRow icon={<FiStar size={14} />} label="Subscription" value={user.subscription || "free"} />
            </div>
          )}
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === "notifications" && (
        <div className="max-w-2xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-2">
              <button onClick={() => setShowReminder(true)} className="btn-primary text-sm flex items-center gap-1">
                <FiBell size={14} /> New Reminder
              </button>
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="btn-secondary text-sm flex items-center gap-1">
                  <FiCheck size={14} /> Mark All Read
                </button>
              )}
            </div>
          </div>

          {/* Reminder Form Modal */}
          {showReminder && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
                <div className="flex justify-between mb-4">
                  <h2 className="font-semibold text-lg">Create Hearing Reminder</h2>
                  <button onClick={() => setShowReminder(false)}><FiX size={20} /></button>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium mb-1">Title *</label>
                    <input
                      type="text"
                      value={reminderData.title}
                      onChange={(e) => setReminderData({ ...reminderData, title: e.target.value })}
                      className="input"
                      placeholder="e.g., Court Hearing - Case #123"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Message *</label>
                    <textarea
                      value={reminderData.message}
                      onChange={(e) => setReminderData({ ...reminderData, message: e.target.value })}
                      className="input"
                      rows={3}
                      placeholder="Details about the hearing..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Case Number</label>
                    <input
                      type="text"
                      value={reminderData.case_number}
                      onChange={(e) => setReminderData({ ...reminderData, case_number: e.target.value })}
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reminder Date</label>
                    <input
                      type="datetime-local"
                      value={reminderData.reminder_date}
                      onChange={(e) => setReminderData({ ...reminderData, reminder_date: e.target.value })}
                      className="input"
                    />
                  </div>
                  <button onClick={createReminder} className="btn-primary w-full">Create Reminder</button>
                </div>
              </div>
            </div>
          )}

          {notifications.length === 0 ? (
            <div className="card text-center py-12">
              <FiBell className="mx-auto text-gray-300 mb-3" size={40} />
              <p className="text-gray-500">No notifications yet</p>
              <p className="text-gray-400 text-sm">Create a reminder to get started</p>
            </div>
          ) : (
            <div className="space-y-2">
              {notifications.map((n) => (
                <div
                  key={n.id}
                  className={`card flex items-start gap-3 ${!n.is_read ? "border-primary-200 bg-primary-50/30" : ""}`}
                >
                  <div className={`p-2 rounded-full ${
                    n.notification_type === "hearing_reminder"
                      ? "bg-blue-100 text-blue-600"
                      : n.notification_type === "case_update"
                      ? "bg-green-100 text-green-600"
                      : "bg-gray-100 text-gray-600"
                  }`}>
                    {n.notification_type === "hearing_reminder" ? <FiCalendar size={14} /> : <FiBell size={14} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm">{n.title}</p>
                      {!n.is_read && <span className="w-2 h-2 bg-primary-600 rounded-full" />}
                    </div>
                    <p className="text-xs text-gray-600 mt-0.5">{n.message}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                      {n.case_number && <span>Case: {n.case_number}</span>}
                      {n.reminder_date && (
                        <span className="flex items-center gap-1">
                          <FiCalendar size={10} />
                          {new Date(n.reminder_date).toLocaleDateString()}
                        </span>
                      )}
                      <span>{new Date(n.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {!n.is_read && (
                      <button onClick={() => markRead(n.id)} className="p-1 hover:bg-green-100 rounded" title="Mark read">
                        <FiCheck size={14} className="text-green-600" />
                      </button>
                    )}
                    <button onClick={() => deleteNotification(n.id)} className="p-1 hover:bg-red-100 rounded" title="Delete">
                      <FiTrash2 size={14} className="text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Subscription Tab */}
      {activeTab === "subscription" && (
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl">
          {subscriptionTiers.map((tier) => (
            <div
              key={tier.name}
              className={`card relative ${
                tier.current ? "border-primary-500 ring-2 ring-primary-200" : ""
              }`}
            >
              {tier.current && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 badge bg-primary-600 text-white">
                  Current Plan
                </span>
              )}
              <h3 className="text-xl font-bold text-center mb-1">{tier.name}</h3>
              <p className="text-2xl font-bold text-center text-primary-600 mb-4">{tier.price}</p>
              <ul className="space-y-2 mb-6">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm">
                    <FiCheck className="text-green-500 flex-shrink-0" size={14} />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                className={`w-full ${tier.current ? "btn-secondary" : "btn-primary"}`}
                disabled={tier.current}
              >
                {tier.current ? "Active" : "Upgrade"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value?: string | null }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-gray-400">{icon}</span>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-sm font-medium capitalize">{value || "Not set"}</p>
      </div>
    </div>
  );
}
